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
模块（Mod）管理系统

本模块提供了 RQAlpha 的 Mod 插件系统，支持通过 Mod 扩展系统功能。

核心概念
--------

- **Mod（模块）**: 实现 AbstractMod 接口的插件
- **ModHandler**: Mod 的加载和生命周期管理器
- **系统 Mod**: RQAlpha 内置的核心功能模块

Mod 生命周期
------------

1. **加载**: set_env 时导入 Mod 模块，创建 Mod 实例
2. **启动**: start_up 时初始化 Mod，注册事件监听等
3. **销毁**: tear_down 时清理资源，收集结果

系统内置 Mod
------------

- ``sys_accounts``: 账户和交易 API
- ``sys_simulation``: 模拟撮合
- ``sys_analyser``: 结果分析
- ``sys_risk``: 风控验证
- ``sys_progress``: 进度显示
- ``sys_transaction_cost``: 交易费用
- ``sys_scheduler``: 定时任务

Mod 加载顺序
------------

1. 按配置文件中的顺序加载
2. 按 priority 排序执行 start_up（默认 100）
3. 按逆序执行 tear_down

自定义 Mod
----------

创建自定义 Mod 的步骤：

1. 创建 Python 包，命名为 ``rqalpha_mod_xxx``
2. 实现 ``__config__`` 配置和 ``load_mod()`` 函数
3. 实现 AbstractMod 接口
4. 在配置文件中启用::

    mod:
      xxx:
        enabled: true

使用方式
--------

Mod 配置示例::

    mod:
      sys_accounts:
        enabled: true
        stock_t1: true
      sys_simulation:
        enabled: true
        slippage: 0.001
"""

import sys
import copy
import typing
from collections import OrderedDict

from rqalpha.interface import AbstractMod
from rqalpha.utils.package_helper import import_mod
from rqalpha.utils.logger import system_log
from rqalpha.utils.i18n import gettext as _
from rqalpha.utils import RqAttrDict, create_custom_exception
from rqalpha.utils.exception import ExceptionGroup


class ModHandler(object):
    def __init__(self):
        self._env = None
        self._mod_list = list()  # type: typing.List[typing.Tuple[str, RqAttrDict]]
        self._mod_dict = OrderedDict()  # type: typing.OrderedDict[str, AbstractMod]

    def set_env(self, environment):
        self._env = environment

        config = environment.config

        for mod_name in config.mod.__dict__:
            mod_config = getattr(config.mod, mod_name)
            if not mod_config.enabled:
                continue
            self._mod_list.append((mod_name, mod_config))

        for idx, (mod_name, user_mod_config) in enumerate(self._mod_list):
            if hasattr(user_mod_config, 'lib'):
                lib_name = user_mod_config.lib
            elif mod_name in SYSTEM_MOD_LIST:
                lib_name = "rqalpha.mod.rqalpha_mod_" + mod_name
            else:
                lib_name = "rqalpha_mod_" + mod_name
            system_log.debug(_(u"loading mod {}").format(lib_name))
            mod_module = import_mod(lib_name)
            if mod_module is None:
                del self._mod_list[idx]
                return
            mod = mod_module.load_mod()  # type: AbstractMod

            mod_config = RqAttrDict(copy.deepcopy(getattr(mod_module, "__config__", {})))
            mod_config.update(user_mod_config)
            setattr(config.mod, mod_name, mod_config)
            self._mod_list[idx] = (mod_name, mod_config)
            self._mod_dict[mod_name] = mod

        self._mod_list.sort(key=lambda item: getattr(item[1], "priority", 100))
        environment.mod_dict = self._mod_dict

    def start_up(self):
        for mod_name, mod_config in self._mod_list:
            system_log.debug(_(u"mod start_up [START] {}\n{}").format(mod_name, mod_config))
            self._mod_dict[mod_name].start_up(self._env, mod_config)
            system_log.debug(_(u"mod start_up [END]   {}").format(mod_name))

    def tear_down(self, *args):
        result = {}
        exceptions = []
        for mod_name, __ in reversed(self._mod_list):
            try:
                system_log.debug(_(u"mod tear_down [START] {}").format(mod_name))
                ret = self._mod_dict[mod_name].tear_down(*args)
                system_log.debug(_(u"mod tear_down [END]   {}").format(mod_name))
            except Exception as e:
                exc_type, exc_val, exc_tb = sys.exc_info()
                exceptions.append(create_custom_exception(exc_type, exc_val, exc_tb, self._env.config.base.strategy_file))
                system_log.exception("tear down fail for {}", mod_name)
                continue
            else:
                if ret is not None:
                    result[mod_name] = ret
        if exceptions:
            raise ExceptionGroup("Mod tear down failed", exceptions)
        return result


SYSTEM_MOD_LIST = [
    "sys_accounts",
    "sys_analyser",
    "sys_progress",
    "sys_risk",
    "sys_simulation",
    "sys_transaction_cost",
    'sys_scheduler',
]
