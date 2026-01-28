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
订单模块

本模块定义了订单（Order）及订单样式（OrderStyle）相关的数据结构，
用于表示和管理交易委托。

核心概念
--------

- **Order（订单）**: 一个交易委托，记录买卖方向、数量、价格、状态等
- **OrderStyle（订单样式）**: 订单的类型，如市价单、限价单、算法订单等

订单生命周期
------------

订单从创建到最终状态的流程::

    PENDING_NEW → ACTIVE → FILLED/CANCELLED/REJECTED
         │          │
         │          └→ PENDING_CANCEL → CANCELLED
         │
         └→ REJECTED（创建失败）

订单状态说明：

- **PENDING_NEW**: 订单已创建，等待确认
- **ACTIVE**: 订单已激活，等待成交
- **FILLED**: 订单全部成交
- **CANCELLED**: 订单已撤销
- **REJECTED**: 订单被拒绝
- **PENDING_CANCEL**: 等待撤销确认

订单类型
--------

- **MarketOrder（市价单）**: 以当前市场价格立即成交
- **LimitOrder（限价单）**: 以指定价格或更优价格成交
- **VWAPOrder（VWAP算法单）**: 按成交量加权平均价格成交
- **TWAPOrder（TWAP算法单）**: 按时间加权平均价格成交

使用方式
--------

订单通常通过下单 API 创建::

    # 市价单
    order = order_shares('000001.XSHE', 1000)
    
    # 限价单
    order = order_shares('000001.XSHE', 1000, price=10.5)
    # 或
    order = order_shares('000001.XSHE', 1000, style=LimitOrder(10.5))
    
    # 查看订单状态
    print(order.status)           # ORDER_STATUS.ACTIVE
    print(order.filled_quantity)  # 已成交数量
    print(order.unfilled_quantity)  # 未成交数量

注意事项
--------

- 订单对象的属性是只读的
- 订单 ID 在整个回测过程中是唯一的
- 期货订单有 position_effect（开平标志）属性
"""

import time
from decimal import Decimal

from datetime import datetime
from typing import Optional

import numpy as np

from rqalpha.const import MARKET, ORDER_STATUS, ORDER_TYPE, SIDE, POSITION_EFFECT, POSITION_DIRECTION, ALGO
from rqalpha.utils import id_gen, decimal_rounding_floor, get_position_direction
from rqalpha.utils.repr import property_repr, properties
from rqalpha.utils.logger import user_system_log
from rqalpha.environment import Environment
from rqalpha.model.instrument import Instrument
from rqalpha.utils.class_helper import cached_property


class Order(object):
    """
    订单对象，表示一个交易委托
    
    订单对象记录了一次交易委托的全部信息，包括标的、方向、数量、价格、
    状态等。订单是连接策略逻辑和交易执行的核心数据结构。
    
    订单对象通过下单 API（如 ``order_shares``）创建，不应直接实例化。
    
    Attributes:
        order_id (int): 订单唯一标识符
        order_book_id (str): 合约代码
        side (SIDE): 买卖方向，BUY 或 SELL
        quantity (int): 委托数量
        filled_quantity (int): 已成交数量
        unfilled_quantity (int): 未成交数量
        price (float): 委托价格（限价单有效）
        avg_price (float): 成交均价
        status (ORDER_STATUS): 订单状态
        type (ORDER_TYPE): 订单类型（市价/限价/算法）
        datetime (datetime): 订单创建时间
        transaction_cost (float): 交易费用
        message (str): 订单消息（如拒单原因）
        
    Example:
        >>> order = order_shares('000001.XSHE', 1000)
        >>> order.order_id
        16093847561234
        >>> order.status
        ORDER_STATUS.ACTIVE
        >>> order.is_final()  # 订单是否已结束
        False
        
    Note:
        - 期货订单额外有 ``position_effect`` 属性表示开平方向
        - ``frozen_price`` 是下单时冻结资金使用的价格
        - 算法订单（VWAP/TWAP）的实际成交价格由算法决定
    """

    order_id_gen = id_gen(int(time.time()) * 10000)

    __repr__ = property_repr  # type: ignore

    _env: Environment

    _order_id: int
    _secondary_order_id: str
    _calendar_dt: datetime
    _trading_dt: datetime
    _quantity: int
    _order_book_id: str
    _side: SIDE
    _position_effect: Optional[POSITION_EFFECT]
    _message: str
    _filled_quantity: int
    _status: ORDER_STATUS
    _frozen_price: float
    _init_frozen_cash: float
    _type: ORDER_TYPE
    _avg_price: float
    _transaction_cost: float
    _style: "OrderStyle"
    _kwargs: dict

    @staticmethod
    def _str_to_enum(enum_class, s):
        return enum_class.__members__[s]

    def get_state(self):
        return {
            'order_id': self._order_id,
            'secondary_order_id': self._secondary_order_id,
            'calendar_dt': self._calendar_dt,
            'trading_dt': self._trading_dt,
            'order_book_id': self._order_book_id,
            'quantity': self._quantity,
            'side': self._side,
            'position_effect': self._position_effect,
            'message': self._message,
            'filled_quantity': self._filled_quantity,
            'status': self._status,
            'frozen_price': self._frozen_price,
            'type': self._type,
            'transaction_cost': self._transaction_cost,
            'avg_price': self._avg_price,
            'kwargs': self._kwargs,
        }

    def set_state(self, d):
        self._order_id = d['order_id']
        if 'secondary_order_id' in d:
            self._secondary_order_id = d['secondary_order_id']
        self._calendar_dt = d['calendar_dt']
        self._trading_dt = d['trading_dt']
        self._order_book_id = d['order_book_id']
        self._quantity = d['quantity']
        self._side = SIDE(d["side"])
        self._position_effect = POSITION_EFFECT(d["position_effect"]) if d["position_effect"] else None
        self._message = d['message']
        self._filled_quantity = d['filled_quantity']
        self._status = ORDER_STATUS(d["status"])
        self._frozen_price = d['frozen_price']
        self._type = ORDER_TYPE(d["type"])
        self._transaction_cost = d['transaction_cost']
        self._avg_price = d['avg_price']
        self._kwargs = d['kwargs']

    @classmethod
    def __from_create__(cls, order_book_id, quantity, side, style, position_effect, **kwargs):
        env = Environment.get_instance()
        order = cls()
        order._env = env
        order._order_id = next(order.order_id_gen)
        order._calendar_dt = env.calendar_dt
        order._trading_dt = env.trading_dt
        order._quantity = quantity
        order._order_book_id = order_book_id
        order._side = side
        order._position_effect = position_effect
        order._message = ""
        order._filled_quantity = 0
        order._status = ORDER_STATUS.PENDING_NEW
        order._style = style
        if isinstance(style, LimitOrder):
            if env.config.base.round_price:
                tick_size = env.data_proxy.get_tick_size(order_book_id)
                style.round_price(tick_size)
            order._frozen_price = style.get_limit_price()
            order._type = ORDER_TYPE.LIMIT
        elif isinstance(style, ALGO_ORDER_STYLES):
            algo_price, _ = env.data_proxy.get_algo_bar(order_book_id, style, env.calendar_dt)
            order._frozen_price = env.get_last_price(order_book_id) if np.isnan(algo_price) else algo_price
            order._type = ORDER_TYPE.ALGO
        else:
            order._frozen_price = env.get_last_price(order_book_id)
            order._type = ORDER_TYPE.MARKET
        order._avg_price = 0
        order._transaction_cost = 0
        order._kwargs = kwargs
        return order

    @property
    def order_id(self):
        # type: () -> int
        """
        [int] 唯一标识订单的id
        """
        return self._order_id

    @property
    def secondary_order_id(self):
        """
        [str] 实盘交易中交易所产生的订单ID
        """
        return self._secondary_order_id

    @property
    def trading_datetime(self) -> datetime:
        """
        [datetime.datetime] 订单的交易日期（对应期货夜盘）
        """
        return self._trading_dt

    @property
    def datetime(self) -> datetime:
        """
        [datetime.datetime] 订单创建时间
        """
        return self._calendar_dt

    @property
    def quantity(self):
        """
        [int] 订单数量
        """
        if np.isnan(self._quantity):
            raise RuntimeError("Quantity of order {} is not supposed to be nan.".format(self.order_id))
        return self._quantity

    @property
    def unfilled_quantity(self):
        """
        [int] 订单未成交数量
        """
        return self.quantity - self.filled_quantity

    @property
    def order_book_id(self):
        """
        [str] 合约代码
        """
        return self._order_book_id

    @property
    def side(self):
        # type: () -> SIDE
        """
        [SIDE] 订单方向
        """
        return self._side

    @property
    def position_effect(self):
        """
        [POSITION_EFFECT] 订单开平（期货专用）
        """
        if self._position_effect is None:
            if self._side == SIDE.BUY:
                return POSITION_EFFECT.OPEN
            else:
                return POSITION_EFFECT.CLOSE
        return self._position_effect

    @property
    def position_direction(self):
        # type: () -> POSITION_DIRECTION
        return get_position_direction(self._side, self._position_effect)

    @property
    def message(self):
        """
        [str] 信息。比如拒单时候此处会提示拒单原因
        """
        return self._message

    @property
    def filled_quantity(self):
        """
        [int] 订单已成交数量
        """
        if np.isnan(self._filled_quantity):
            raise RuntimeError("Filled quantity of order {} is not supposed to be nan.".format(self.order_id))
        return self._filled_quantity

    @property
    def status(self):
        """
        [ORDER_STATUS] 订单状态
        """
        return self._status

    @property
    def price(self):
        """
        [float] 订单价格，只有在订单类型为'限价单'的时候才有意义
        """
        return 0 if self.type == ORDER_TYPE.MARKET else self.frozen_price

    @property
    def type(self):
        """
        [ORDER_TYPE] 订单类型
        """
        return self._type

    @property
    def style(self):
        """
        [ORDER_STYLE] 订单类型
        """
        return self._style

    @property
    def avg_price(self):
        """
        [float] 成交均价
        """
        return self._avg_price

    @property
    def transaction_cost(self):
        """
        [float] 费用
        """
        return self._transaction_cost

    @property
    def frozen_price(self):
        """
        [float] 冻结价格
        """
        if np.isnan(self._frozen_price):
            raise RuntimeError("Frozen price of order {} is not supposed to be nan.".format(self.order_id))
        return self._frozen_price

    @property
    def init_frozen_cash(self):
        """
        [float] 冻结资金
        """
        if np.isnan(self._init_frozen_cash):
            raise RuntimeError("Frozen cash of order {} is not supposed to be nan.".format(self.order_id))
        return self._init_frozen_cash

    @property
    def kwargs(self):
        return self._kwargs
    
    @cached_property
    def instrument(self) -> Instrument:
        return self._env.data_proxy.instrument_not_none(self._order_book_id)
    
    @cached_property
    def market(self) -> MARKET:
        return self.instrument.market

    @property
    def estimated_transaction_cost(self) -> float:
        from rqalpha.interface import TransactionCostArgs

        if self.position_effect == POSITION_EFFECT.CLOSE_TODAY:
            close_today_quantity = self.quantity
        else:
            close_today_quantity = 0
        return self._env.calc_transaction_cost(TransactionCostArgs(
            self.instrument, self.frozen_price, self.quantity, self.side, self.position_effect,
            close_today_quantity=close_today_quantity,
        )).total

    def __getattr__(self, item):
        try:
            return self.__dict__["_kwargs"][item]
        except KeyError:
            raise AttributeError("'{}' object has no attribute '{}'".format(self.__class__.__name__, item))

    def is_final(self):
        return self._status not in {
            ORDER_STATUS.PENDING_NEW,
            ORDER_STATUS.ACTIVE,
            ORDER_STATUS.PENDING_CANCEL
        }

    def is_active(self):
        return self.status == ORDER_STATUS.ACTIVE

    def active(self):
        self._status = ORDER_STATUS.ACTIVE

    def set_pending_cancel(self):
        if not self.is_final():
            self._status = ORDER_STATUS.PENDING_CANCEL

    def fill(self, trade):
        quantity = trade.last_quantity
        assert self.filled_quantity + quantity <= self.quantity
        new_quantity = self._filled_quantity + quantity
        self._transaction_cost += trade.transaction_cost
        if trade.position_effect != POSITION_EFFECT.MATCH:
            self._avg_price = (self._avg_price * self._filled_quantity + trade.last_price * quantity) / new_quantity
        self._filled_quantity = new_quantity
        if self.unfilled_quantity == 0:
            self._status = ORDER_STATUS.FILLED

    def mark_rejected(self, reject_reason):
        if not self.is_final():
            self._message = reject_reason
            self._status = ORDER_STATUS.REJECTED
            user_system_log.warn(reject_reason)

    def mark_cancelled(self, cancelled_reason, user_warn=True):
        if not self.is_final():
            self._message = cancelled_reason
            self._status = ORDER_STATUS.CANCELLED
            if user_warn:
                user_system_log.warn(cancelled_reason)

    def set_frozen_price(self, value):
        self._frozen_price = value

    def set_frozen_cash(self, value):
        self._init_frozen_cash = value

    def set_secondary_order_id(self, secondary_order_id):
        self._secondary_order_id = str(secondary_order_id)

    def __simple_object__(self):
        return properties(self)


class OrderStyle(object):
    """
    订单样式基类
    
    订单样式定义了订单的执行方式，如市价成交、限价成交或算法成交。
    这是一个抽象基类，不应直接使用。
    
    子类:
        - MarketOrder: 市价单
        - LimitOrder: 限价单
        - VWAPOrder: 成交量加权平均价格算法单
        - TWAPOrder: 时间加权平均价格算法单
    """
    def get_limit_price(self):
        """获取限价，市价单返回 None"""
        raise NotImplementedError


class AlgoOrder(OrderStyle):
    """
    算法订单基类
    
    算法订单会在指定的时间段内，按照特定算法拆分成多个小订单执行，
    以减少市场冲击成本。
    
    Attributes:
        start_min (int): 算法执行开始时间（分钟）
        end_min (int): 算法执行结束时间（分钟）
    """
    __repr__ = ORDER_TYPE.ALGO.__repr__  # type: ignore

    def __init__(self, start_min, end_min):
        self.start_min = start_min
        self.end_min = end_min

    def get_limit_price(self):
        return None


class TWAPOrder(AlgoOrder):
    """
    TWAP（时间加权平均价格）算法订单
    
    订单会在指定时间段内均匀拆分执行，成交价格接近该时间段的
    时间加权平均价格。适合需要平滑执行的大单。
    
    Example:
        >>> # 在开盘后30分钟到60分钟之间执行
        >>> order = order_shares('000001.XSHE', 10000, style=TWAPOrder(30, 60))
    """
    TYPE = ALGO.TWAP
    __repr__ = ALGO.TWAP.__repr__


class VWAPOrder(AlgoOrder):
    """
    VWAP（成交量加权平均价格）算法订单
    
    订单会在指定时间段内按照历史成交量分布拆分执行，成交价格
    接近该时间段的成交量加权平均价格。适合跟踪市场节奏的大单。
    
    Example:
        >>> # 在开盘后30分钟到60分钟之间执行
        >>> order = order_shares('000001.XSHE', 10000, style=VWAPOrder(30, 60))
    """
    TYPE = ALGO.VWAP
    __repr__ = ALGO.VWAP.__repr__


class MarketOrder(OrderStyle):
    """
    市价单
    
    以当前市场最优价格立即成交的订单。在回测中，市价单通常以
    当前 Bar 的收盘价或下一个 Bar 的开盘价成交（取决于配置）。
    
    优点:
        - 成交确定性高
        - 执行速度快
        
    缺点:
        - 可能有较大滑点
        - 涨跌停时可能无法成交
        
    Example:
        >>> order = order_shares('000001.XSHE', 1000)  # 默认市价单
        >>> order = order_shares('000001.XSHE', 1000, style=MarketOrder())
    """
    __repr__ = ORDER_TYPE.MARKET.__repr__  # type: ignore

    def get_limit_price(self):
        return None

    def __eq__(self, other):
        return isinstance(other, MarketOrder)


class LimitOrder(OrderStyle):
    """
    限价单
    
    以指定价格或更优价格成交的订单。买入时，只有当市场价格低于或
    等于限价时才会成交；卖出时，只有当市场价格高于或等于限价时才会成交。
    
    Attributes:
        limit_price (float): 限定价格
        
    优点:
        - 可以控制成交价格
        - 避免不利价格成交
        
    缺点:
        - 可能无法成交
        - 在快速变动的市场中可能错过机会
        
    Example:
        >>> # 以 10.5 元的价格买入
        >>> order = order_shares('000001.XSHE', 1000, price=10.5)
        >>> # 或者
        >>> order = order_shares('000001.XSHE', 1000, style=LimitOrder(10.5))
    """
    __repr__ = ORDER_TYPE.LIMIT.__repr__  # type: ignore

    def __init__(self, limit_price):
        self.limit_price = float(limit_price)

    def __eq__(self, other):
        return isinstance(other, LimitOrder) and self.limit_price == other.limit_price

    def get_limit_price(self):
        return self.limit_price

    def round_price(self, tick_size):
        if tick_size:
            with decimal_rounding_floor():
                limit_price_decimal = Decimal("{:.4f}".format(self.limit_price))
                tick_size_decimal = Decimal("{:.4f}".format(tick_size))
                self.limit_price = float((limit_price_decimal / tick_size_decimal).to_integral() * tick_size_decimal)
        else:
            user_system_log.warn('Invalid tick size: {}'.format(tick_size))


ALGO_ORDER_STYLES = (VWAPOrder, TWAPOrder)
ALL_ORDER_STYPES = (LimitOrder, MarketOrder, TWAPOrder, VWAPOrder)
