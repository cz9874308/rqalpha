# 第 2 课：环境搭建

**⏱ 预计学习时间**：30 分钟  
**🎯 学习目标**：
- 安装 Python 运行环境
- 安装 RQAlpha
- 下载回测数据包
- 验证安装成功

**📚 难度**：⭐ 入门

---

## 📖 课程概览

在开始量化之旅之前，我们需要先准备好工具。这一课我们会：

1. 安装 Python（如果你还没有的话）
2. 安装 RQAlpha 框架
3. 下载 A 股历史数据
4. 确认一切准备就绪

> 💡 **小贴士**：安装过程中遇到问题很正常，不要着急，本课末尾有常见问题解答。

---

## 2.1 系统要求

在开始之前，请确认你的电脑满足以下要求：

| 要求 | 说明 |
|------|------|
| 操作系统 | Windows 10+、macOS 10.14+、Linux |
| Python 版本 | 3.8 或更高版本 |
| 内存 | 建议 8GB 以上 |
| 硬盘空间 | 至少 2GB（数据包需要空间） |
| 网络 | 需要联网下载 |

---

## 2.2 安装 Python

### 检查是否已安装 Python

打开终端（Windows 用 PowerShell 或命令提示符，Mac 用终端），输入：

```bash
python --version
```

或者：

```bash
python3 --version
```

如果显示类似 `Python 3.10.0` 的版本号，且版本 ≥ 3.8，恭喜你，可以跳过这一节！

### Windows 用户安装指南

#### 方法一：官网下载（推荐新手）

1. 访问 [Python 官网](https://www.python.org/downloads/)
2. 点击 "Download Python 3.x.x" 按钮
3. 运行下载的安装程序
4. **⚠️ 重要**：勾选 "Add Python to PATH"
5. 点击 "Install Now"

```
┌─────────────────────────────────────────────────────────────┐
│                    Python 安装界面                           │
│                                                             │
│  ☑️ Add Python 3.x to PATH    ← 一定要勾选这个！              │
│                                                             │
│  [Install Now]                                              │
└─────────────────────────────────────────────────────────────┘
```

#### 方法二：使用 Miniconda（推荐进阶用户）

Miniconda 是一个轻量级的 Python 环境管理工具：

1. 下载 [Miniconda](https://docs.conda.io/en/latest/miniconda.html)
2. 运行安装程序
3. 创建虚拟环境：

```bash
conda create -n rqalpha python=3.10
conda activate rqalpha
```

### macOS 用户安装指南

#### 方法一：官网下载

1. 访问 [Python 官网](https://www.python.org/downloads/)
2. 下载 macOS 安装包
3. 双击运行安装

#### 方法二：使用 Homebrew（推荐）

如果你已经安装了 Homebrew：

```bash
brew install python@3.10
```

### Linux 用户安装指南

大多数 Linux 发行版已经预装 Python，如果版本较低：

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3.10 python3.10-venv python3-pip

# CentOS/RHEL
sudo yum install python3
```

---

## 2.3 安装 RQAlpha

### 使用虚拟环境（推荐）

虚拟环境可以避免不同项目之间的依赖冲突：

```bash
# 创建虚拟环境
python -m venv rqalpha-env

# 激活虚拟环境
# Windows:
rqalpha-env\Scripts\activate

# macOS/Linux:
source rqalpha-env/bin/activate
```

激活后，命令行前面会出现 `(rqalpha-env)` 标识。

### 安装 RQAlpha

在终端中执行：

```bash
pip install rqalpha
```

你会看到类似这样的输出：

```
Collecting rqalpha
  Downloading rqalpha-5.x.x-py3-none-any.whl (xxx kB)
...
Successfully installed rqalpha-5.x.x
```

### 验证安装

```bash
rqalpha version
```

如果显示版本号，说明安装成功！🎉

```
rqalpha 5.x.x
```

---

## 2.4 下载数据包

RQAlpha 需要历史数据才能进行回测。我们提供了免费的 A 股日线数据。

### 下载命令

```bash
rqalpha download-bundle
```

### 下载过程

```
[████████████████████████████████████████] 100%
Bundle downloaded successfully.
```

> ⚠️ **注意**：
> - 数据包约 500MB-1GB，下载时间取决于网速
> - 默认保存在 `~/.rqalpha/bundle` 目录
> - 首次下载后，后续可以增量更新

### 指定下载目录（可选）

如果你想把数据放在其他位置：

```bash
rqalpha download-bundle -d /path/to/your/directory
```

---

## 2.5 生成示例策略

RQAlpha 提供了一些示例策略，可以帮助你快速上手：

```bash
rqalpha examples -d ./examples
```

这会在当前目录下创建一个 `examples` 文件夹，包含几个示例策略文件。

### 查看示例文件

```
examples/
├── buy_and_hold.py      # 买入持有策略
├── golden_cross.py      # 金叉策略
├── rsi.py               # RSI 策略
└── ...
```

---

## 2.6 验证一切就绪

让我们运行一个简单的测试，确保一切正常：

```bash
cd examples
rqalpha run -f buy_and_hold.py -s 2020-01-01 -e 2020-12-31 --account stock 100000
```

如果看到类似这样的输出，恭喜你，环境配置成功！

```
                           回测结果
═══════════════════════════════════════════════════════════
    年化收益率: 25.5%
    夏普比率: 1.2
    最大回撤: 15.3%
    ...
```

---

## 💡 实践任务

完成以下任务，确保你的环境已经准备就绪：

- [ ] 安装 Python 3.8+
- [ ] 安装 RQAlpha（`pip install rqalpha`）
- [ ] 运行 `rqalpha version` 确认安装成功
- [ ] 下载数据包（`rqalpha download-bundle`）
- [ ] 生成示例策略（`rqalpha examples -d ./examples`）
- [ ] 运行测试命令，确认一切正常

---

## ❓ 常见问题

### Q1: pip 命令找不到？

**症状**：`'pip' 不是内部或外部命令`

**解决方案**：
```bash
# 尝试使用 pip3
pip3 install rqalpha

# 或者使用 python -m pip
python -m pip install rqalpha
```

### Q2: 安装时报错 "Permission denied"？

**解决方案**：
```bash
# Windows: 以管理员身份运行命令提示符

# macOS/Linux:
pip install --user rqalpha
```

### Q3: 下载数据包失败？

**可能原因**：网络问题

**解决方案**：
1. 检查网络连接
2. 使用代理或 VPN
3. 多尝试几次

### Q4: 运行时报错 "No module named 'xxx'"？

**解决方案**：
```bash
pip install xxx
```

### Q5: Python 版本太低？

**解决方案**：
- 升级 Python 到 3.8+
- 或者使用 pyenv/conda 管理多版本

### Q6: Windows 编码问题？

**症状**：中文乱码

**解决方案**：
```bash
# 在命令行执行
chcp 65001
```

---

## 📝 知识检查

### 基础问题

1. RQAlpha 需要 Python 什么版本？
2. 数据包下载命令是什么？
3. 如何验证 RQAlpha 安装成功？

<details>
<summary>💡 点击查看答案</summary>

1. Python 3.8 或更高版本
2. `rqalpha download-bundle`
3. 运行 `rqalpha version`，如果显示版本号则安装成功

</details>

---

## 📌 核心要点

1. **Python 版本**：需要 3.8+，记得勾选 "Add to PATH"
2. **安装命令**：`pip install rqalpha`
3. **下载数据**：`rqalpha download-bundle`
4. **虚拟环境**：推荐使用，避免依赖冲突
5. **验证安装**：`rqalpha version`

---

## ➡️ 下一课预告

环境准备好了，下一课我们将运行第一个策略！

你将学到：
- 运行示例策略
- 理解命令行参数
- 解读回测结果
- 查看收益图表

**准备工作**：
- 确保上面的安装步骤都已完成
- 示例策略文件已生成

👉 [**继续学习：第3课 - 运行第一个策略**](./lesson-03-first-strategy.md)

---

[← 上一课](./lesson-01-introduction.md) | [返回目录](./README.md) | [下一课 →](./lesson-03-first-strategy.md)
