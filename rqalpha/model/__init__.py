# -*- coding: utf-8 -*-
# 版权所有 2019 深圳米筐科技有限公司（下称“米筐科技”）
#
# 除非遵守当前许可，否则不得使用本软件。
#
#     * 非商业用途（非商业用途指个人出于非商业目的使用本软件，或者高校、研究所等非营利机构出于教育、科研等目的使用本软件）：
#         遵守 Apache License 2.0（下称“Apache 2.0 许可”），您可以在以下位置获得 Apache 2.0 许可的副本：http://www.apache.org/licenses/LICENSE-2.0。
#         除非法律有要求或以书面形式达成协议，否则本软件分发时需保持当前许可“原样”不变，且不得附加任何条件。
#
#     * 商业用途（商业用途指个人出于任何商业目的使用本软件，或者法人或其他组织出于任何目的使用本软件）：
#         未经米筐科技授权，任何个人不得出于任何商业目的使用本软件（包括但不限于向第三方提供、销售、出租、出借、转让本软件、本软件的衍生产品、引用或借鉴了本软件功能或源代码的产品或服务），任何法人或其他组织不得出于任何目的使用本软件，否则米筐科技有权追究相应的知识产权侵权责任。
#         在此前提下，对本软件的使用同样需要遵守 Apache 2.0 许可，Apache 2.0 许可与本许可冲突之处，以本许可为准。
#         详细的授权流程，请联系 public@ricequant.com 获取。

"""
数据模型模块

本模块定义了 RQAlpha 回测系统中的核心数据模型，这些模型是策略与回测引擎之间数据交互的基础。

核心概念
--------

- **Instrument（合约）**: 表示一个可交易的金融工具，如股票、期货合约等
- **Order（订单）**: 表示一个交易委托，包含买卖方向、数量、价格等信息
- **Trade（成交）**: 表示一笔实际完成的交易，记录成交价格、数量、费用等
- **Bar（K线）**: 表示一个时间周期内的行情数据，包含开高低收、成交量等
- **Tick（快照）**: 表示某一时刻的市场快照数据，包含盘口信息

数据流向
--------

在回测过程中，数据流向如下::

    DataSource → Bar/Tick → Strategy → Order → Trade → Position

使用方式
--------

这些模型通常不需要用户直接创建，而是通过 API 获取::

    # 获取 K 线数据
    bar = bar_dict['000001.XSHE']
    print(bar.close)  # 收盘价

    # 下单后获取订单对象
    order = order_shares('000001.XSHE', 1000)
    print(order.order_id)  # 订单ID

    # 查看合约信息
    ins = instruments('000001.XSHE')
    print(ins.symbol)  # 平安银行

注意事项
--------

- 这些对象的属性大多是只读的，不应尝试修改
- 对象的某些属性可能返回 NaN，表示数据不可用
- 期货和股票的某些属性含义不同，请参考具体属性文档
"""

from .order import Order, OrderStyle
from .trade import Trade
from .instrument import Instrument
from .bar import BarMap, BarObject, PartialBarObject
from .tick import TickObject
