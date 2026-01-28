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
全局变量模块

本模块定义了 GlobalVars 类（即策略中的 g 对象），
为用户策略提供一个全局变量存储空间。

核心概念
--------

- **GlobalVars（全局变量）**: 策略中的 g 对象

g 对象 vs context 对象
-----------------------

g 和 context 都可以存储用户数据，区别在于：

- ``context``: 策略上下文，包含系统属性（如 portfolio）
- ``g``: 纯粹的全局变量存储，不包含系统属性

推荐使用场景：

- 与回测相关的数据存储在 ``context``
- 纯粹的全局变量或跨模块共享数据存储在 ``g``

使用方式
--------

在策略中使用 g::

    from rqalpha.api import g
    
    def init(context):
        # 存储全局变量
        g.counter = 0
        g.my_list = []
        
    def handle_bar(context, bar_dict):
        g.counter += 1
        g.my_list.append(context.now)

状态持久化
----------

g 对象上的数据支持序列化，用于断点续跑：

- 只有可 pickle 的数据才能被保存
- 序列化失败的属性会产生警告但不影响运行
"""

import pickle
from rqalpha.utils.logger import user_system_log, system_log


class GlobalVars(object):
    """
    全局变量存储对象（即 g 对象）
    
    GlobalVars 为用户提供一个简单的全局变量存储空间。
    用户可以在 g 对象上存储任意属性，这些属性在整个回测过程中持久存在。
    
    与 context 不同，g 对象不包含任何系统预定义的属性，
    它是一个纯粹的用户数据容器。
    
    Example:
        >>> # 在 init 中初始化全局变量
        >>> def init(context):
        ...     g.counter = 0
        ...     g.data_cache = {}
        ...
        >>> # 在 handle_bar 中使用
        >>> def handle_bar(context, bar_dict):
        ...     g.counter += 1
        ...     print(f"这是第 {g.counter} 根 K 线")
        
    Note:
        - 所有属性都支持序列化（用于断点续跑）
        - 不可 pickle 的对象会产生警告
        - 建议存储简单的 Python 对象（int, float, list, dict 等）
    """
    def get_state(self):
        dict_data = {}
        for key, value in self.__dict__.items():
            try:
                dict_data[key] = pickle.dumps(value)
            except Exception:
                user_system_log.warn("g.{} can not pickle", key)
        return pickle.dumps(dict_data)

    def set_state(self, state):
        dict_data = pickle.loads(state)
        for key, value in dict_data.items():
            try:
                self.__dict__[key] = pickle.loads(value)
                system_log.debug("restore g.{} {}", key, type(self.__dict__[key]))
            except Exception:
                user_system_log.warn("g.{} restore failed", key)
