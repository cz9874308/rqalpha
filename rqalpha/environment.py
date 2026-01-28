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
运行环境模块

本模块定义了 Environment 类，它是 RQAlpha 的核心服务注册中心，
采用服务定位器（Service Locator）模式管理各种系统组件。

核心概念
--------

Environment 是一个单例对象，在整个回测过程中提供对以下服务的访问：

- **DataProxy**: 数据代理，提供行情和合约数据
- **DataSource**: 底层数据源
- **PriceBoard**: 价格板，提供最新价格
- **EventSource**: 事件源，生成时间事件
- **EventBus**: 事件总线，事件发布订阅
- **Broker**: 经纪商，处理订单和成交
- **Portfolio**: 投资组合，管理账户和持仓
- **Strategy**: 用户策略
- **Mods**: 已加载的模块

使用方式
--------

获取 Environment 实例::

    from rqalpha.environment import Environment
    
    env = Environment.get_instance()
    
    # 访问各种服务
    data_proxy = env.data_proxy
    portfolio = env.portfolio
    
    # 获取当前时间
    current_dt = env.calendar_dt
    trading_dt = env.trading_dt
    
    # 获取股票池
    universe = env.get_universe()

时间管理
--------

Environment 维护两个时间概念：

- **calendar_dt**: 日历时间，表示当前的实际时间点
- **trading_dt**: 交易日时间，处理期货夜盘等跨日交易

例如：期货夜盘 23:00 的 calendar_dt 是当天 23:00，
但 trading_dt 是下一个交易日。

注意事项
--------

- Environment 是单例，通过 ``get_instance()`` 获取
- 在系统初始化前调用 ``get_instance()`` 会抛出异常
- 各服务在初始化过程中通过 ``set_xxx`` 方法注册
"""

from datetime import datetime
from typing import Optional, Dict, List, Tuple
from itertools import chain
from typing import TYPE_CHECKING

from typing_extensions import deprecated

import rqalpha
from rqalpha.core.events import EventBus, Event, EVENT
from rqalpha.const import INSTRUMENT_TYPE, DAYS_CNT, MARKET
from rqalpha.utils.logger import system_log, user_log, user_system_log
from rqalpha.core.global_var import GlobalVars
from rqalpha.utils.i18n import gettext as _
from rqalpha.utils.class_helper import cached_property
from rqalpha.utils.exception import EnvironmentNotInitialized
from rqalpha.const import SIDE
if TYPE_CHECKING:
    from rqalpha.model.order import Order
    from rqalpha.portfolio import Portfolio
    from rqalpha.data.data_proxy import DataProxy
    from rqalpha.interface import AbstractDataSource, AbstractPriceBoard, AbstractEventSource, \
        AbstractStrategyLoader, AbstractMod, AbstractBroker, AbstractTransactionCostDecider, TransactionCostArgs, TransactionCost
    from rqalpha.core.strategy import Strategy
    from rqalpha.model.instrument import Instrument


class Environment(object):
    """
    运行环境，RQAlpha 的核心服务注册中心
    
    Environment 是一个单例对象，作为整个回测系统的服务定位器，
    提供对数据、交易、账户等各种核心服务的统一访问入口。
    
    所有模块都可以通过 ``Environment.get_instance()`` 获取环境实例，
    进而访问所需的服务。
    
    Attributes:
        config: 回测配置
        global_vars: 用户全局变量存储
        event_bus (EventBus): 事件总线
        calendar_dt (datetime): 当前日历时间
        trading_dt (datetime): 当前交易日时间
        data_proxy (DataProxy): 数据代理
        data_source (AbstractDataSource): 数据源
        price_board (AbstractPriceBoard): 价格板
        event_source (AbstractEventSource): 事件源
        broker (AbstractBroker): 经纪商
        portfolio (Portfolio): 投资组合
        strategy_loader (AbstractStrategyLoader): 策略加载器
        user_strategy (Strategy): 用户策略
        mod_dict (dict): 已加载的模块字典
        
    Example:
        >>> env = Environment.get_instance()
        >>> 
        >>> # 获取当前时间
        >>> print(env.trading_dt)
        >>> 
        >>> # 获取数据
        >>> bar = env.get_bar('000001.XSHE')
        >>> 
        >>> # 获取账户
        >>> account = env.get_account('000001.XSHE')
        
    Note:
        - 这是单例类，只能通过 ``get_instance()`` 获取
        - 在系统初始化完成前调用会抛出 ``EnvironmentNotInitialized``
    """
    _env: Optional["Environment"] = None

    data_proxy: "DataProxy"
    data_source: "AbstractDataSource"
    price_board: "AbstractPriceBoard"
    event_source: "AbstractEventSource"
    broker: "AbstractBroker"
    strategy_loader: "AbstractStrategyLoader"
    portfolio: "Portfolio"
    mod_dict: "Dict[str, AbstractMod]"
    user_strategy: "Strategy"

    def __init__(self, config, rqdatac_init):
        Environment._env = self
        self.config = config

        self.global_vars = GlobalVars()
        self.persist_provider = None
        self.persist_helper = None
        self.profile_deco = None
        self.system_log = system_log
        self.user_log = user_log
        self.user_system_log = user_system_log
        self.event_bus = EventBus()
        self.calendar_dt: datetime = datetime.combine(config.base.start_date, datetime.min.time())
        self.trading_dt: datetime = datetime.combine(config.base.start_date, datetime.min.time())

        self._frontend_validators = {}  # type: Dict[str, List]
        self._default_frontend_validators = []
        self._transaction_cost_deciders: Dict[Tuple[INSTRUMENT_TYPE, MARKET], AbstractTransactionCostDecider] = {}
        self.rqdatac_init = rqdatac_init
        self._trading_days_a_year = None

        # Environment.event_bus used in StrategyUniverse()
        from rqalpha.core.strategy_universe import StrategyUniverse
        self._universe = StrategyUniverse()

    @classmethod
    def get_instance(cls):
        """
        返回已经创建的 Environment 对象
        """
        if Environment._env is None:
            raise EnvironmentNotInitialized(
                _(u"Environment has not been created. Please Use `Environment.get_instance()` after RQAlpha init"))
        return Environment._env

    def set_data_proxy(self, data_proxy):
        self.data_proxy = data_proxy

    def set_data_source(self, data_source):
        self.data_source = data_source

    def set_price_board(self, price_board):
        self.price_board = price_board

    def set_strategy_loader(self, strategy_loader):
        self.strategy_loader = strategy_loader

    def set_portfolio(self, portfolio):
        self.portfolio = portfolio

    def set_hold_strategy(self):
        self.config.extra.is_hold = True

    def cancel_hold_strategy(self):
        self.config.extra.is_hold = False

    def set_persist_helper(self, helper):
        self.persist_helper = helper

    def set_persist_provider(self, provider):
        self.persist_provider = provider

    def set_event_source(self, event_source):
        self.event_source = event_source

    def set_broker(self, broker):
        self.broker = broker

    def add_frontend_validator(self, validator, instrument_type=None):
        if instrument_type:
            self._frontend_validators.setdefault(instrument_type, []).append(validator)
        else:
            self._default_frontend_validators.append(validator)

    def _get_frontend_validators(self, instrument_type):
        return chain(self._frontend_validators.get(instrument_type, []), self._default_frontend_validators)

    def submit_order(self, order: "Order") -> "Optional[Order]":
        if self.can_submit_order(order):
            self.broker.submit_order(order)
            return order

    def can_cancel_order(self, order):
        instrument_type = self.data_proxy.instrument_not_none(order.order_book_id).type
        account = self.portfolio.get_account(order.order_book_id)
        for v in chain(self._frontend_validators.get(instrument_type, []), self._default_frontend_validators):
            try:
                reason = v.validate_cancellation(order, account)
                if reason:
                    self.order_cancellation_failed(order_book_id=order.order_book_id, reason=reason)
                    return False
            except NotImplementedError:
                # 避免由于某些 mod 版本未更新，Validator method 未修改
                if not v.can_cancel_order(order, account):
                    return False
        return True
    
    def order_creation_failed(self, order_book_id, reason):
        user_system_log.warn(reason)
        self.event_bus.publish_event(Event(EVENT.ORDER_CREATION_REJECT, order_book_id=order_book_id, reason=reason))

    def order_cancellation_failed(self, order_book_id, reason):
        user_system_log.warn(reason)
        self.event_bus.publish_event(Event(EVENT.ORDER_CANCELLATION_REJECT, order_book_id=order_book_id, reason=reason))

    def get_universe(self):
        return self._universe.get()

    def update_universe(self, universe):
        self._universe.update(universe)

    def get_bar(self, order_book_id):
        return self.data_proxy.get_bar(order_book_id, self.calendar_dt, self.config.base.frequency)

    def get_last_price(self, order_book_id):
        return self.data_proxy.get_last_price(order_book_id)

    @deprecated("Use APIs from data_proxy instead", category=None)
    def get_instrument(self, order_book_id):
        return self.data_proxy.instrument(order_book_id)

    def get_account_type(self, order_book_id):
        return self.portfolio.get_account_type(order_book_id)

    def get_account(self, order_book_id):
        return self.portfolio.get_account(order_book_id)

    def get_open_orders(self, order_book_id=None):
        return self.broker.get_open_orders(order_book_id)

    def set_transaction_cost_decider(self, instrument_type: INSTRUMENT_TYPE, decider: "AbstractTransactionCostDecider", market: MARKET = MARKET.CN):
        self._transaction_cost_deciders[(instrument_type, market)] = decider

    def get_transaction_cost_decider(self, instrument_type: INSTRUMENT_TYPE, market: MARKET = MARKET.CN) -> "AbstractTransactionCostDecider":
        return self._transaction_cost_deciders[(instrument_type, market)]

    def calc_transaction_cost(self, args: "TransactionCostArgs") -> "TransactionCost":
        ins = args.instrument
        try:
            decider = self.get_transaction_cost_decider(ins.type, ins.market)
        except KeyError:
            raise NotImplementedError(_(u"No such transaction cost decider, order_book_id = {}".format(
                ins.order_book_id
            )))
        return decider.calc(args)

    def update_time(self, calendar_dt, trading_dt):
        # type: (datetime, datetime) -> None
        self.calendar_dt = calendar_dt
        self.trading_dt = trading_dt

    def can_submit_order(self, order: 'Order') -> bool:
        # forward compatible
        instrument_type = self.data_proxy.instrument_not_none(order.order_book_id).type
        account = self.portfolio.get_account(order.order_book_id)
        for v in self._get_frontend_validators(instrument_type):
            try:
                reason = v.validate_submission(order, account)
                if reason:
                    self.order_creation_failed(order_book_id=order.order_book_id, reason=reason)
                    return False
            except NotImplementedError:
                # 避免由于某些 mod 版本未更新，Validator method 未修改
                if not v.can_submit_order(order, account):
                    return False
        return True
    
    @cached_property
    def trading_days_a_year(self):
        self._trading_days_a_year = getattr(self.config.base, 'custom_trading_days_a_year', DAYS_CNT.TRADING_DAYS_A_YEAR)
        if self._trading_days_a_year is None:
            self._trading_days_a_year = DAYS_CNT.TRADING_DAYS_A_YEAR
        return self._trading_days_a_year
