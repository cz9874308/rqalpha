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
数据层模块

本模块提供了 RQAlpha 的数据访问层，负责行情数据、合约信息、交易日历等数据的获取和处理。

核心组件
--------

**DataProxy（数据代理）**:
    统一的数据访问接口，整合数据源和价格板功能

**DataSource（数据源）**:
    底层数据提供者，负责从数据文件或数据库读取原始数据

**PriceBoard（价格板）**:
    提供当前最新价格的组件

数据层架构
----------

数据访问的层次结构::

    API / Strategy
          ↓
      DataProxy（统一接口）
          ↓
    ┌─────┴─────┐
    DataSource   PriceBoard
    (历史数据)    (实时价格)
          ↓
    Bundle Files / RQDatac

主要功能
--------

- 合约信息查询（instruments）
- 历史K线数据（history_bars）
- 实时价格获取（get_last_price）
- 交易日历查询（trading_dates）
- 分红送股信息（dividend, split）
- 复权因子计算（adjust）

使用方式
--------

通过 Environment 获取 DataProxy::

    env = Environment.get_instance()
    data_proxy = env.data_proxy
    
    # 获取合约信息
    ins = data_proxy.instrument('000001.XSHE')
    
    # 获取历史数据
    bars = data_proxy.history_bars('000001.XSHE', 10, '1d', 'close')
"""

from . import data_proxy
from .data_proxy import DataProxy
