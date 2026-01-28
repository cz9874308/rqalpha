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
策略 API 聚合模块

本模块聚合了 RQAlpha 提供给策略使用的所有 API 函数。

API 分类
--------

**基础 API (api_base)**:
    通用交易和数据 API，如 ``order_shares``, ``history_bars`` 等

**股票 API (api_stock)**:
    股票特有的交易 API，如 ``order_lots`` 等

**期货 API (api_future)**:
    期货特有的交易 API，如 ``buy_open``, ``sell_close`` 等

**数据 API (api_rqdatac)**:
    RQDatac 数据查询 API

使用方式
--------

在策略中导入 API::

    from rqalpha.api import *
    
    def init(context):
        context.s1 = '000001.XSHE'
    
    def handle_bar(context, bar_dict):
        order_shares(context.s1, 1000)

或者选择性导入::

    from rqalpha.apis import order_shares, history_bars
    
注意事项
--------

- 大部分 API 只能在特定的执行阶段调用
- 某些 API 需要启用相应的 Mod 才能使用
- 使用 ``from rqalpha.api import *`` 可导入所有可用 API
"""

from rqalpha.apis.api_abstract import *
from rqalpha.apis.api_base import *
from rqalpha.apis.api_rqdatac import *

from rqalpha.mod.rqalpha_mod_sys_accounts.api.api_stock import *
from rqalpha.mod.rqalpha_mod_sys_accounts.api.api_stock import *
