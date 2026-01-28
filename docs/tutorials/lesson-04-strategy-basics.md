# 第 4 课：策略编写基础

**⏱ 预计学习时间**：45 分钟  
**🎯 学习目标**：
- 理解策略文件的完整结构
- 掌握核心函数的用法
- 学会使用 context 对象
- 理解 bar_dict 数据结构

**📚 难度**：⭐⭐ 基础

---

## 📖 课程概览

上一课我们运行了第一个策略，但只是"照葫芦画瓢"。这一课我们要深入理解策略是怎么工作的，这样才能写出自己的策略。

我们将学习：
1. 策略的整体结构
2. 必须实现的函数
3. context 对象的奥秘
4. bar_dict 数据的使用

---

## 4.1 策略文件结构

### 一个完整策略的骨架

```python
# ============ 策略文件结构 ============

# 1. 导入需要的库（可选）
import talib

# 2. 初始化函数（必须）
def init(context):
    # 策略启动时执行一次
    pass

# 3. 盘前处理（可选）
def before_trading(context):
    # 每天开盘前执行
    pass

# 4. 核心交易逻辑（必须）
def handle_bar(context, bar_dict):
    # 每根K线触发
    pass

# 5. 盘后处理（可选）
def after_trading(context):
    # 每天收盘后执行
    pass
```

### 函数调用顺序

```
策略启动
    │
    ▼
┌─────────┐
│  init   │ ← 只执行一次
└─────────┘
    │
    ▼
┌─────────────────────────────────────────────────────┐
│                   每个交易日循环                      │
│  ┌───────────────┐                                  │
│  │before_trading │ ← 开盘前执行                      │
│  └───────────────┘                                  │
│          ↓                                          │
│  ┌───────────────┐                                  │
│  │  handle_bar   │ ← 每根K线执行（日线=每天1次）       │
│  │  handle_bar   │   （分钟线=每分钟1次）              │
│  │     ...       │                                  │
│  └───────────────┘                                  │
│          ↓                                          │
│  ┌───────────────┐                                  │
│  │ after_trading │ ← 收盘后执行                      │
│  └───────────────┘                                  │
└─────────────────────────────────────────────────────┘
    │
    ▼
回测结束
```

---

## 4.2 init() 函数

### 作用

`init()` 是策略的初始化函数，在策略启动时**只执行一次**。

### 常见用途

1. **设置股票池**
2. **初始化策略参数**
3. **设置全局变量**

### 代码示例

```python
def init(context):
    # 用途1: 设置要交易的股票
    context.stock = "000001.XSHE"  # 平安银行
    
    # 用途2: 设置策略参数
    context.short_period = 5    # 短期均线周期
    context.long_period = 20    # 长期均线周期
    
    # 用途3: 设置其他配置
    context.max_position = 0.8  # 最大仓位80%
    
    # 可以打印日志
    logger.info("策略初始化完成")
    logger.info(f"交易标的: {context.stock}")
```

### 注意事项

> ⚠️ **重要**：`init()` 只在策略启动时执行一次，不是每天都执行！

---

## 4.3 context 对象

### 什么是 context？

`context` 是一个**全局上下文对象**，在所有函数之间传递。你可以把它想象成一个"共享的笔记本"，在任何地方都能读写。

### context 的用途

```
┌─────────────────────────────────────────────────────────────┐
│                     context 对象                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   📝 自定义属性         可以存储任何你需要的数据               │
│      context.stock = "000001.XSHE"                          │
│      context.my_data = [1, 2, 3]                            │
│                                                             │
│   💰 portfolio          投资组合信息（系统提供）               │
│      context.portfolio.cash        # 可用资金                │
│      context.portfolio.total_value # 总资产                  │
│                                                             │
│   📊 run_info           运行信息（系统提供）                  │
│      context.run_info.start_date   # 开始日期                │
│      context.run_info.end_date     # 结束日期                │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 常用属性一览

#### 自定义属性（你自己设置的）

```python
def init(context):
    context.stock = "000001.XSHE"     # 股票代码
    context.days = 0                   # 计数器
    context.signal = False             # 信号标志
```

#### context.portfolio（投资组合）

```python
def handle_bar(context, bar_dict):
    # 可用资金
    cash = context.portfolio.cash
    
    # 总资产（现金 + 持仓市值）
    total = context.portfolio.total_value
    
    # 持仓市值
    market_value = context.portfolio.market_value
    
    # 当日盈亏
    daily_pnl = context.portfolio.daily_pnl
    
    # 累计收益率
    returns = context.portfolio.total_returns
```

#### context.run_info（运行信息）

```python
def init(context):
    # 回测开始日期
    start = context.run_info.start_date
    
    # 回测结束日期
    end = context.run_info.end_date
    
    # 运行频率（'1d' 或 '1m'）
    freq = context.run_info.frequency
```

---

## 4.4 handle_bar() 函数

### 作用

`handle_bar()` 是策略的**核心交易逻辑**，每当有新的 K 线数据时就会被调用。

- 日线策略：每天调用一次
- 分钟策略：每分钟调用一次

### 函数签名

```python
def handle_bar(context, bar_dict):
    # context: 上下文对象
    # bar_dict: 当前的K线数据
    pass
```

### 典型结构

```python
def handle_bar(context, bar_dict):
    # Step 1: 获取数据
    stock = context.stock
    price = bar_dict[stock].close  # 当前收盘价
    
    # Step 2: 计算指标或信号
    should_buy = price < 10  # 示例条件
    
    # Step 3: 执行交易
    if should_buy:
        order_shares(stock, 1000)  # 买入1000股
```

---

## 4.5 bar_dict 数据

### 什么是 bar_dict？

`bar_dict` 是一个字典，包含当前时刻所有股票的 K 线数据。

### 获取数据的方式

```python
def handle_bar(context, bar_dict):
    stock = "000001.XSHE"
    
    # 获取这只股票的bar数据
    bar = bar_dict[stock]
    
    # 或者使用 context 中保存的股票
    bar = bar_dict[context.stock]
```

### Bar 数据包含的字段

```python
def handle_bar(context, bar_dict):
    bar = bar_dict[context.stock]
    
    # 价格数据
    open_price = bar.open      # 开盘价
    high_price = bar.high      # 最高价
    low_price = bar.low        # 最低价
    close_price = bar.close    # 收盘价
    
    # 成交数据
    volume = bar.volume        # 成交量（股）
    total_turnover = bar.total_turnover  # 成交额（元）
    
    # 其他
    datetime = bar.datetime    # 时间戳
```

### Bar 数据可视化

```
┌─────────────────────────────────────────────────────────────┐
│                     一根K线的数据                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│         最高价 high ─────  ┃                                │
│                            ┃                                │
│         ┌──────────────────┃                                │
│ 开盘价  │                  ┃  ← 收盘价 (绿色下跌)            │
│  open   │                  ┃                                │
│         └──────────────────┃                                │
│                            ┃                                │
│         最低价 low ──────  ┃                                │
│                                                             │
│         成交量 volume      ███████████                       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 4.6 before_trading() 和 after_trading()

### before_trading()

在每天开盘前执行，适合做：
- 调整股票池
- 检查停牌状态
- 准备当天的数据

```python
def before_trading(context):
    # 检查今天是否需要调仓
    logger.info("开盘前准备...")
    
    # 可以获取当前日期
    today = context.now.date()
    logger.info(f"今天是: {today}")
```

### after_trading()

在每天收盘后执行，适合做：
- 记录当天持仓
- 计算当天收益
- 准备第二天的操作

```python
def after_trading(context):
    logger.info("收盘后处理...")
    
    # 记录当天收益
    logger.info(f"今日盈亏: {context.portfolio.daily_pnl}")
```

---

## 4.7 实战：编写一个简单策略

让我们把学到的知识组合起来，写一个简单的策略。

### 策略逻辑

> 当股价低于 10 元时买入，高于 15 元时卖出

### 完整代码

```python
def init(context):
    """初始化函数"""
    # 设置交易标的
    context.stock = "000001.XSHE"  # 平安银行
    
    # 设置买卖阈值
    context.buy_price = 10   # 低于10元买入
    context.sell_price = 15  # 高于15元卖出
    
    logger.info("策略初始化完成")


def before_trading(context):
    """盘前处理"""
    logger.info(f"当前日期: {context.now.date()}")
    logger.info(f"可用资金: {context.portfolio.cash:.2f}")


def handle_bar(context, bar_dict):
    """核心交易逻辑"""
    stock = context.stock
    
    # 获取当前价格
    current_price = bar_dict[stock].close
    
    # 获取当前持仓
    position = get_position(stock)
    current_quantity = position.quantity
    
    # 买入逻辑：价格低于阈值且未持仓
    if current_price < context.buy_price and current_quantity == 0:
        # 计算可买数量（用80%资金）
        cash_to_use = context.portfolio.cash * 0.8
        shares = int(cash_to_use / current_price / 100) * 100  # 整百股
        
        if shares > 0:
            order_shares(stock, shares)
            logger.info(f"买入 {shares} 股，价格 {current_price:.2f}")
    
    # 卖出逻辑：价格高于阈值且有持仓
    elif current_price > context.sell_price and current_quantity > 0:
        order_shares(stock, -current_quantity)
        logger.info(f"卖出 {current_quantity} 股，价格 {current_price:.2f}")


def after_trading(context):
    """盘后处理"""
    logger.info(f"今日盈亏: {context.portfolio.daily_pnl:.2f}")
    logger.info("-" * 50)
```

### 保存并运行

1. 把上面的代码保存为 `my_first_strategy.py`
2. 运行：

```bash
rqalpha run -f my_first_strategy.py -s 2020-01-01 -e 2020-12-31 --account stock 100000 --plot
```

---

## 💡 实践任务

- [ ] 阅读并理解 `buy_and_hold.py` 的每一行代码
- [ ] 编写上面的简单策略并运行
- [ ] 尝试修改买卖阈值，观察结果变化
- [ ] 在策略中添加更多的 `logger.info()` 输出

---

## 📝 知识检查

### 基础问题

1. `init()` 函数什么时候执行？执行几次？
2. 如何获取当前可用资金？
3. `bar_dict[stock].close` 获取的是什么数据？

### 思考题

1. 为什么要在 `init()` 中设置参数，而不是在 `handle_bar()` 中？
2. context 对象为什么能在所有函数间共享数据？

<details>
<summary>💡 点击查看答案</summary>

**基础问题：**
1. `init()` 在策略启动时执行，只执行一次
2. `context.portfolio.cash`
3. 获取该股票当前的收盘价

**思考题：**
1. 在 `init()` 中设置参数只需要执行一次，效率更高。如果在 `handle_bar()` 中设置，每根K线都会重复执行，浪费资源。
2. 因为 RQAlpha 在调用每个函数时都会传入同一个 context 对象，所以在一个函数中设置的属性在其他函数中也能访问。

</details>

---

## 📌 核心要点

1. **init()**：初始化，只执行一次
2. **handle_bar()**：核心逻辑，每根K线执行
3. **context**：全局共享对象，存储自定义数据和系统信息
4. **bar_dict**：当前K线数据，包含 OHLCV
5. **portfolio**：投资组合信息，包含资金和持仓

---

## ➡️ 下一课预告

现在你已经理解了策略结构，下一课我们将学习如何获取数据和执行交易。

你将学到：
- `history_bars()` 获取历史数据
- 各种下单函数的使用
- 如何查询持仓信息

**准备工作**：
- 确保能成功运行本课的示例策略
- 思考：如何获取过去 N 天的价格数据？

👉 [**继续学习：第5课 - 数据与交易**](./lesson-05-data-and-trading.md)

---

[← 上一课](./lesson-03-first-strategy.md) | [返回目录](./README.md) | [下一课 →](./lesson-05-data-and-trading.md)
