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
系统账户模块（sys_accounts）

本模块是 RQAlpha 的核心内置 Mod，提供账户管理、持仓管理和交易 API 的实现。

核心功能
--------

1. **股票 API 实现**: order_shares, order_value, order_percent 等
2. **期货 API 实现**: buy_open, sell_close, buy_close, sell_open 等
3. **持仓模型**: StockPosition, FuturePosition
4. **订单验证**: 仓位检查、资金检查、T+1 限制等

配置选项
--------

- ``stock_t1``: 是否开启股票 T+1 限制（默认 True）
- ``dividend_reinvestment``: 是否开启自动分红再投资（默认 False）
- ``dividend_tax_rate``: 红利税率（默认 0.0）
- ``cash_return_by_stock_delisted``: 退市时是否返还现金（默认 True）
- ``auto_switch_order_value``: 资金不足时使用全部剩余资金（默认 False）
- ``validate_stock_position``: 检查股票仓位（默认 True）
- ``validate_future_position``: 检查期货仓位（默认 True）
- ``financing_rate``: 融资利率（默认 0.0）
- ``futures_settlement_price_type``: 期货结算价类型，settlement 或 close

命令行参数
----------

- ``--stock-t1/--no-stock-t1``: 开启/关闭股票 T+1
- ``--dividend-reinvestment``: 开启分红再投资
- ``--no-short-stock/--short-stock``: 禁止/允许股票做空
- ``--futures-settlement-price-type``: 期货结算价类型

使用示例
--------

配置文件::

    mod:
      sys_accounts:
        enabled: true
        stock_t1: true
        dividend_reinvestment: false

命令行::

    rqalpha run -f strategy.py --no-stock-t1
"""

import click
from rqalpha import cli


__config__ = {
    # 是否开启股票 T+1 限制
    "stock_t1": True,
    # 是否开启自动分红再投资
    "dividend_reinvestment": False,
    # 红利税，暂只支持固定税率
    "dividend_tax_rate": 0.0,
    # 当持仓股票退市时，是否按照退市价格返还现金
    "cash_return_by_stock_delisted": True,
    # 股票下单因资金不足被拒时改为使用全部剩余资金下单
    "auto_switch_order_value": False,
    # 开启对股票仓位是否能满足平仓需求的检查
    "validate_stock_position": True,
    # 开启对期货仓位是否能满足平仓需求的检查
    "validate_future_position": True,
    # 融资利率/年
    "financing_rate": 0.00,
    # 是否开启融资可买入股票的限制
    "financing_stocks_restriction_enabled": False,
    # 逐日盯市结算价: settlement/close
    "futures_settlement_price_type": "close",
}


def load_mod():
    from .mod import AccountMod
    return AccountMod()


cli_prefix = "mod__sys_accounts__"

cli.commands['run'].params.append(
    click.Option(
        ('--stock-t1/--no-stock-t1', cli_prefix + "stock_t1"),
        default=None,
        help="[sys_accounts] enable/disable stock T+1"
    )
)

cli.commands['run'].params.append(
    click.Option(
        ('--dividend-reinvestment', cli_prefix + 'dividend_reinvestment'),
        default=None, is_flag=True,
        help="[sys_accounts] enable dividend reinvestment"
    )
)


cli.commands['run'].params.append(
    click.Option(
        (
            '--cash-return-by-stock-delisted/--no-cash-return-by-stock-delisted',
            cli_prefix + 'cash_return_by_stock_delisted'
        ),
        default=True,
        help="[sys_accounts] return cash when stock delisted"
    )
)


cli.commands['run'].params.append(
    click.Option(
        ("--no-short-stock/--short-stock", cli_prefix + "validate_stock_position"),
        is_flag=True, default=True,
        help="[sys_accounts] enable stock shorting"
    )
)

cli.commands['run'].params.append(
    click.Option(
        ('--futures-settlement-price-type', cli_prefix + 'futures_settlement_price_type'),
        default=None,
        help="[sys_accounts] future settlement price"
    )
)
