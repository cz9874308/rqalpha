# -*- coding: utf-8 -*-
# 版权所有 2019 深圳米筐科技有限公司（下称“米筐科技”）
#
# 除非遵守当前许可，否则不得使用本软件。
#
#     * 非商业用途（非商业用途指个人出于非商业目的使用本软件，或者高校、研究所等非营利机构出于教育、科研等目的使用本软件）：
#         遵守 Apache License 2.0（下称“Apache 2.0 许可”），
#         您可以在以下位置获得 Apache 2.0 许可的副本：http://www.apache.org/licenses/LICENSE-2.0。
#         除非法律有要求或以书面形式达成协议，否则本软件分发时需保持当前许可“原样”不变，且不得附加任何条件。
#
#     * 商业用途（商业用途指个人出于任何商业目的使用本软件，或者法人或其他组织出于任何目的使用本软件）：
#         未经米筐科技授权，任何个人不得出于任何商业目的使用本软件（包括但不限于向第三方提供、销售、出租、出借、转让本软件、
#         本软件的衍生产品、引用或借鉴了本软件功能或源代码的产品或服务），任何法人或其他组织不得出于任何目的使用本软件，
#         否则米筐科技有权追究相应的知识产权侵权责任。
#         在此前提下，对本软件的使用同样需要遵守 Apache 2.0 许可，Apache 2.0 许可与本许可冲突之处，以本许可为准。
#         详细的授权流程，请联系 public@ricequant.com 获取。

"""
策略模块

本模块定义了 Strategy 类，它是用户策略代码的包装器，
负责管理策略的生命周期和事件处理。

核心概念
--------

- **Strategy**: 用户策略的包装器，连接用户代码和事件系统
- **生命周期方法**: init, before_trading, handle_bar, handle_tick, after_trading
- **ExecutionContext**: 执行上下文，标记当前所处的执行阶段

策略生命周期
------------

用户策略包含以下可选的生命周期方法：

1. **init(context)**: 初始化，只在回测开始时调用一次
2. **before_trading(context)**: 每个交易日开盘前调用
3. **open_auction(context, bar_dict)**: 集合竞价阶段调用
4. **handle_bar(context, bar_dict)**: 每根K线触发调用
5. **handle_tick(context, tick)**: 每个Tick触发调用
6. **after_trading(context)**: 每个交易日收盘后调用

事件订阅
--------

Strategy 在初始化时自动将用户定义的方法订阅到相应事件::

    如果定义了 handle_bar  →  订阅 EVENT.BAR
    如果定义了 handle_tick →  订阅 EVENT.TICK
    ...

异常处理
--------

所有用户代码都被包装在异常处理中：

- 用户代码异常会被标记为 USER_EXC
- 系统内部异常会被标记为 SYSTEM_EXC

这样便于区分错误来源和生成有意义的错误信息。

注意事项
--------

- 策略暂停时（is_hold=True）不会触发用户回调
- before_trading 的旧签名（带 bar_dict 参数）已废弃
- 用户可通过 subscribe_event 订阅自定义事件处理器
"""

from functools import wraps

from rqalpha.core.events import EVENT, Event
from rqalpha.utils.logger import user_system_log
from rqalpha.utils.i18n import gettext as _
from rqalpha.utils.exception import ModifyExceptionFromType
from rqalpha.core.execution_context import ExecutionContext
from rqalpha.const import EXECUTION_PHASE, EXC_TYPE
from rqalpha.environment import Environment


def run_when_strategy_not_hold(func):
    from rqalpha.utils.logger import system_log

    def wrapper(*args, **kwargs):
        if not Environment.get_instance().config.extra.is_hold:
            return func(*args, **kwargs)
        else:
            system_log.debug(_(u"not run {}({}, {}) because strategy is hold").format(func, args, kwargs))

    return wrapper


class Strategy(object):
    """
    策略包装器，管理用户策略的生命周期和事件处理
    
    Strategy 类将用户编写的策略函数包装起来，自动订阅相应的事件，
    并在事件触发时调用用户代码。它负责设置正确的执行上下文和异常处理。
    
    Attributes:
        _user_context: 用户上下文对象（即 context）
        _init: 用户定义的 init 函数
        _before_trading: 用户定义的 before_trading 函数
        _handle_bar: 用户定义的 handle_bar 函数
        _handle_tick: 用户定义的 handle_tick 函数
        _open_auction: 用户定义的 open_auction 函数
        _after_trading: 用户定义的 after_trading 函数
        
    Example:
        用户策略文件::
        
            def init(context):
                context.s1 = '000001.XSHE'
                
            def handle_bar(context, bar_dict):
                order_shares(context.s1, 1000)
        
        系统内部创建 Strategy::
        
            scope = {'init': init, 'handle_bar': handle_bar}
            strategy = Strategy(event_bus, scope, context)
            strategy.init()  # 调用用户 init
            
    Note:
        - 如果策略被暂停（config.extra.is_hold=True），回调不会执行
        - 所有用户代码都在 try-except 中执行，异常会被标记类型
    """
    def __init__(self, event_bus, scope, ucontext):
        self._user_context = ucontext
        self._current_universe = set()

        self._init = scope.get('init', None)
        self._handle_bar = scope.get('handle_bar', None)
        self._handle_tick = scope.get('handle_tick', None)
        self._open_auction = scope.get("open_auction", None)
        func_before_trading = scope.get('before_trading', None)
        if func_before_trading is not None and func_before_trading.__code__.co_argcount > 1:
            self._before_trading = lambda context: func_before_trading(context, None)
            user_system_log.warn(_(u"deprecated parameter[bar_dict] in before_trading function."))
        else:
            self._before_trading = func_before_trading
        self._after_trading = scope.get('after_trading', None)

        if self._before_trading is not None:
            event_bus.add_listener(EVENT.BEFORE_TRADING, self.before_trading)
        if self._handle_bar is not None:
            event_bus.add_listener(EVENT.BAR, self.handle_bar)
        if self._handle_tick is not None:
            event_bus.add_listener(EVENT.TICK, self.handle_tick)
        if self._after_trading is not None:
            event_bus.add_listener(EVENT.AFTER_TRADING, self.after_trading)
        if self._open_auction is not None:
            event_bus.add_listener(EVENT.OPEN_AUCTION, self.open_auction)

    @property
    def user_context(self):
        return self._user_context

    def init(self):
        if self._init:
            with ExecutionContext(EXECUTION_PHASE.ON_INIT):
                with ModifyExceptionFromType(EXC_TYPE.USER_EXC):
                    self._init(self._user_context)

        Environment.get_instance().event_bus.publish_event(Event(EVENT.POST_USER_INIT))

    @run_when_strategy_not_hold
    def before_trading(self, event):
        with ExecutionContext(EXECUTION_PHASE.BEFORE_TRADING):
            with ModifyExceptionFromType(EXC_TYPE.USER_EXC):
                self._before_trading(self._user_context)

    @run_when_strategy_not_hold
    def handle_bar(self, event):
        bar_dict = event.bar_dict
        with ExecutionContext(EXECUTION_PHASE.ON_BAR):
            with ModifyExceptionFromType(EXC_TYPE.USER_EXC):
                self._handle_bar(self._user_context, bar_dict)

    @run_when_strategy_not_hold
    def open_auction(self, event):
        bar_dict = event.bar_dict
        with ExecutionContext(EXECUTION_PHASE.OPEN_AUCTION):
            with ModifyExceptionFromType(EXC_TYPE.USER_EXC):
                self._open_auction(self._user_context, bar_dict)

    @run_when_strategy_not_hold
    def handle_tick(self, event):
        tick = event.tick
        with ExecutionContext(EXECUTION_PHASE.ON_TICK):
            with ModifyExceptionFromType(EXC_TYPE.USER_EXC):
                self._handle_tick(self._user_context, tick)

    @run_when_strategy_not_hold
    def after_trading(self, event):
        with ExecutionContext(EXECUTION_PHASE.AFTER_TRADING):
            with ModifyExceptionFromType(EXC_TYPE.USER_EXC):
                self._after_trading(self._user_context)

    def wrap_user_event_handler(self, handler):
        @wraps(handler)
        def wrapped_handler(event):
            with ExecutionContext(EXECUTION_PHASE.GLOBAL):
                with ModifyExceptionFromType(EXC_TYPE.USER_EXC):
                    return handler(self._user_context, event)
        return wrapped_handler
