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
事件执行器模块

本模块定义了 Executor 类，它是 RQAlpha 回测引擎的核心驱动器，
负责从事件源获取事件并分发到事件总线。

核心概念
--------

- **Executor（执行器）**: 驱动整个回测流程的引擎
- **事件分割**: 将主事件拆分为 PRE/MAIN/POST 三个阶段

执行流程
--------

Executor 的工作流程::

    EventSource.events()  →  Executor.run()  →  EventBus.publish_event()
           ↑                       ↓
        生成事件              处理并分发事件

对于每个交易日，事件处理顺序为：

1. BEFORE_TRADING - 开盘前
2. OPEN_AUCTION - 集合竞价（可选）
3. BAR/TICK - 行情事件（循环）
4. AFTER_TRADING - 收盘后
5. SETTLEMENT - 结算（交易日结束）

事件拆分
--------

每个主事件会被拆分为三个阶段事件：

- PRE_xxx: 事件前，供系统模块准备工作
- xxx: 主事件，触发用户策略
- POST_xxx: 事件后，供系统模块收尾工作

例如 BAR 事件会触发：PRE_BAR → BAR → POST_BAR

状态管理
--------

Executor 维护的状态用于断点续跑：

- ``_last_before_trading``: 上一次触发 BEFORE_TRADING 的日期

注意事项
--------

- Executor 确保每个交易日只触发一次 BEFORE_TRADING
- 结算事件在新交易日开始前触发（而非当日结束后）
"""

from copy import copy
from datetime import datetime

from rqalpha.core.events import EVENT, Event
from rqalpha.utils.rq_json import convert_dict_to_json, convert_json_to_dict
from rqalpha.utils.logger import system_log


class Executor(object):
    """
    事件执行器，驱动回测流程的核心引擎
    
    Executor 负责从 EventSource 获取时间事件，并将它们分发到 EventBus。
    它是整个回测系统的"心脏"，驱动时间前进和事件触发。
    
    主要职责：
    
    1. 消费 EventSource 生成的事件
    2. 确保正确的事件触发顺序
    3. 将事件拆分为 PRE/MAIN/POST 三阶段
    4. 管理 BEFORE_TRADING 和 SETTLEMENT 的触发时机
    5. 维护状态以支持断点续跑
    
    Attributes:
        _env (Environment): 运行环境
        _last_before_trading (date): 上次触发 BEFORE_TRADING 的日期
        
    Example:
        >>> executor = Executor(env)
        >>> executor.run(bar_dict)  # 开始回测
        
    Note:
        - 每个交易日只触发一次 BEFORE_TRADING
        - SETTLEMENT 在新交易日的 BEFORE_TRADING 之前触发
        - 回测结束后会触发最后一天的 SETTLEMENT
    """
    def __init__(self, env):
        self._env = env
        self._last_before_trading = None

    def get_state(self):
        return convert_dict_to_json({"last_before_trading": self._last_before_trading}).encode('utf-8')

    def set_state(self, state):
        self._last_before_trading = convert_json_to_dict(state.decode('utf-8')).get("last_before_trading")

    def run(self, bar_dict):
        conf = self._env.config.base
        for event in self._env.event_source.events(conf.start_date, conf.end_date, conf.frequency):
            if event.event_type == EVENT.TICK:
                if self._ensure_before_trading(event):
                    self._split_and_publish(event)
            elif event.event_type == EVENT.BAR:
                if self._ensure_before_trading(event):
                    bar_dict.update_dt(event.calendar_dt)
                    event.bar_dict = bar_dict
                    self._split_and_publish(event)
            elif event.event_type == EVENT.OPEN_AUCTION:
                if self._ensure_before_trading(event):
                    bar_dict.update_dt(event.calendar_dt)
                    event.bar_dict = bar_dict
                    self._split_and_publish(event)
            elif event.event_type == EVENT.BEFORE_TRADING:
                self._ensure_before_trading(event)
            elif event.event_type == EVENT.AFTER_TRADING:
                self._split_and_publish(event)
            else:
                self._env.event_bus.publish_event(event)

        # publish settlement after last day
        if self._env.trading_dt.date() == conf.end_date:
            self._split_and_publish(Event(EVENT.SETTLEMENT))

    def _ensure_before_trading(self, event):
        # return True if before_trading won't run this time
        if self._last_before_trading == event.trading_dt.date() or self._env.config.extra.is_hold:
            return True
        if self._last_before_trading:
            # don't publish settlement on first day
            previous_trading_date = self._env.data_proxy.get_previous_trading_date(event.trading_dt).date()
            if self._env.trading_dt.date() != previous_trading_date:
                self._env.update_time(
                    datetime.combine(previous_trading_date, self._env.calendar_dt.time()),
                    datetime.combine(previous_trading_date, self._env.trading_dt.time())
                )
            system_log.debug("publish settlement events with calendar_dt={}, trading_dt={}".format(
                self._env.calendar_dt, self._env.trading_dt
            ))
            self._split_and_publish(Event(EVENT.SETTLEMENT))
        self._last_before_trading = event.trading_dt.date()
        self._split_and_publish(Event(EVENT.BEFORE_TRADING, calendar_dt=event.calendar_dt, trading_dt=event.trading_dt))
        return False

    EVENT_SPLIT_MAP = {
        EVENT.BEFORE_TRADING: (EVENT.PRE_BEFORE_TRADING, EVENT.BEFORE_TRADING, EVENT.POST_BEFORE_TRADING),
        EVENT.BAR: (EVENT.PRE_BAR, EVENT.BAR, EVENT.POST_BAR),
        EVENT.TICK: (EVENT.PRE_TICK, EVENT.TICK, EVENT.POST_TICK),
        EVENT.AFTER_TRADING: (EVENT.PRE_AFTER_TRADING, EVENT.AFTER_TRADING, EVENT.POST_AFTER_TRADING),
        EVENT.SETTLEMENT: (EVENT.PRE_SETTLEMENT, EVENT.SETTLEMENT, EVENT.POST_SETTLEMENT),
        EVENT.OPEN_AUCTION: (EVENT.PRE_OPEN_AUCTION, EVENT.OPEN_AUCTION, EVENT.POST_OPEN_AUCTION),
    }

    def _split_and_publish(self, event):
        if hasattr(event, "calendar_dt") and hasattr(event, "trading_dt"):
            self._env.update_time(event.calendar_dt, event.trading_dt)
        for event_type in self.EVENT_SPLIT_MAP[event.event_type]:
            e = copy(event)
            e.event_type = event_type
            self._env.event_bus.publish_event(e)
