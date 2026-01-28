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
基础数据源模块

本模块提供了 RQAlpha 的默认数据源实现，用于从本地数据包（bundle）读取行情数据。

核心组件
--------

**BaseDataSource**:
    默认数据源实现，从 bundle 文件读取数据

**BaseDataSourceProtocol**:
    数据源协议定义

**Storage 组件**:
    - DayBarStore: 日线数据存储
    - MinuteBarStore: 分钟线数据存储
    - InstrumentStore: 合约信息存储
    - DividendStore: 分红数据存储

数据文件结构
------------

默认数据包结构::

    ~/.rqalpha/bundle/
    ├── instruments.pk      # 合约信息
    ├── trading_dates.npy   # 交易日历
    ├── stocks/             # 股票日线数据
    ├── futures/            # 期货日线数据
    ├── dividends/          # 分红数据
    └── ...

扩展数据源
----------

要实现自定义数据源，需要：

1. 继承 ``AbstractDataSource`` 接口
2. 实现必要的数据获取方法
3. 在 Mod 中注册数据源

参见 ``rqalpha/interface.py`` 中的 ``AbstractDataSource`` 定义。
"""

from .data_source import BaseDataSource, BaseDataSourceProtocol
