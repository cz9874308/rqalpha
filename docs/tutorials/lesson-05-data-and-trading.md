# 第 5 课：数据与交易

**⏱ 预计学习时间**：45 分钟  
**🎯 学习目标**：
- 掌握历史数据获取方法
- 学会使用各种下单函数
- 理解持仓查询方法
- 了解账户信息获取

**📚 难度**：⭐⭐ 基础

---

## 📖 课程概览

上一课我们学习了策略的结构，但还不知道如何获取历史数据和执行交易。这一课我们将学习：

1. 如何获取历史 K 线数据
2. 各种下单函数的使用
3. 如何查询持仓信息
4. 如何获取账户资金信息

这些是量化交易最核心的操作！

---

## 5.1 获取历史数据

### history_bars() 函数

这是获取历史数据最重要的函数：

```python
history_bars(order_book_id, bar_count, frequency, fields)
```

### 参数说明

| 参数 | 含义 | 示例 |
|------|------|------|
| `order_book_id` | 股票代码 | `"000001.XSHE"` |
| `bar_count` | 获取多少根K线 | `10` |
| `frequency` | K线周期 | `"1d"`（日线） |
| `fields` | 需要的字段 | `"close"` 或多个字段 |

### 使用示例

#### 获取单个字段

```python
def handle_bar(context, bar_dict):
    stock = "000001.XSHE"
    
    # 获取最近10天的收盘价
    close_prices = history_bars(stock, 10, '1d', 'close')
    
    # 返回的是 numpy 数组
    print(close_prices)
    # [10.5, 10.8, 10.2, 10.9, 11.0, ...]
    
    # 计算均值
    avg_price = close_prices.mean()
```

#### 获取多个字段

```python
def handle_bar(context, bar_dict):
    stock = "000001.XSHE"
    
    # 获取多个字段
    bars = history_bars(stock, 10, '1d', ['open', 'high', 'low', 'close', 'volume'])
    
    # 返回的是结构化数组
    print(bars['close'])  # 收盘价数组
    print(bars['volume']) # 成交量数组
```

### 可用的字段

| 字段 | 含义 |
|------|------|
| `open` | 开盘价 |
| `high` | 最高价 |
| `low` | 最低价 |
| `close` | 收盘价 |
| `volume` | 成交量 |
| `total_turnover` | 成交额 |

### 实际应用：计算均线

```python
def handle_bar(context, bar_dict):
    stock = context.stock
    
    # 获取20日收盘价
    prices = history_bars(stock, 20, '1d', 'close')
    
    # 计算20日均线
    ma20 = prices.mean()
    
    # 当前价格
    current_price = bar_dict[stock].close
    
    # 判断是否在均线上方
    if current_price > ma20:
        logger.info(f"价格 {current_price:.2f} 在20日均线 {ma20:.2f} 上方")
```

---

## 5.2 下单函数

RQAlpha 提供了多种下单方式，满足不同的交易需求。

### 下单函数一览

```
┌─────────────────────────────────────────────────────────────┐
│                     股票下单函数                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   order_shares()      按股数下单                             │
│   order_value()       按金额下单                             │
│   order_percent()     按资金比例下单                         │
│   order_target_value()    调整到目标市值                     │
│   order_target_percent()  调整到目标比例                     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### order_shares() - 按股数下单

```python
order_shares(order_book_id, amount)
```

**示例**：

```python
def handle_bar(context, bar_dict):
    # 买入1000股
    order_shares("000001.XSHE", 1000)
    
    # 卖出500股（用负数）
    order_shares("000001.XSHE", -500)
    
    # 全部卖出
    position = get_position("000001.XSHE")
    order_shares("000001.XSHE", -position.quantity)
```

> 💡 **注意**：A股必须是100的整数倍（整手交易）

### order_value() - 按金额下单

```python
order_value(order_book_id, value)
```

**示例**：

```python
def handle_bar(context, bar_dict):
    # 买入价值5万元的股票
    order_value("000001.XSHE", 50000)
    
    # 卖出价值3万元的股票
    order_value("000001.XSHE", -30000)
```

### order_percent() - 按资金比例下单

```python
order_percent(order_book_id, percent)
```

**示例**：

```python
def handle_bar(context, bar_dict):
    # 用总资产的20%买入
    order_percent("000001.XSHE", 0.2)
    
    # 卖出持仓的50%
    order_percent("000001.XSHE", -0.1)
```

### order_target_value() - 调整到目标市值

```python
order_target_value(order_book_id, value)
```

**示例**：

```python
def handle_bar(context, bar_dict):
    # 调整持仓市值到10万元
    # 如果现在持仓5万，会自动买入5万
    # 如果现在持仓15万，会自动卖出5万
    order_target_value("000001.XSHE", 100000)
    
    # 清仓：目标市值为0
    order_target_value("000001.XSHE", 0)
```

### order_target_percent() - 调整到目标比例

```python
order_target_percent(order_book_id, percent)
```

**示例**：

```python
def handle_bar(context, bar_dict):
    # 调整持仓到总资产的30%
    order_target_percent("000001.XSHE", 0.3)
    
    # 清仓
    order_target_percent("000001.XSHE", 0)
```

### 下单函数对比

| 函数 | 参数含义 | 适用场景 |
|------|----------|----------|
| `order_shares` | 股数 | 知道要买多少股 |
| `order_value` | 金额 | 知道要投入多少钱 |
| `order_percent` | 比例 | 按资金比例分配 |
| `order_target_value` | 目标市值 | 调仓到指定市值 |
| `order_target_percent` | 目标比例 | 调仓到指定比例 |

---

## 5.3 查询持仓

### get_position() 函数

```python
get_position(order_book_id)
```

**示例**：

```python
def handle_bar(context, bar_dict):
    # 获取持仓信息
    position = get_position("000001.XSHE")
    
    # 持仓数量
    quantity = position.quantity
    
    # 可卖数量（T+1限制）
    sellable = position.sellable
    
    # 持仓成本
    avg_price = position.avg_price
    
    # 持仓市值
    market_value = position.market_value
    
    # 盈亏金额
    pnl = position.pnl
```

### Position 常用属性

| 属性 | 含义 |
|------|------|
| `quantity` | 持仓数量 |
| `sellable` | 可卖数量 |
| `avg_price` | 持仓均价 |
| `market_value` | 持仓市值 |
| `pnl` | 盈亏金额 |
| `last_price` | 最新价格 |

### 判断是否持仓

```python
def handle_bar(context, bar_dict):
    stock = "000001.XSHE"
    position = get_position(stock)
    
    if position.quantity > 0:
        logger.info(f"持有 {stock}，数量: {position.quantity}")
    else:
        logger.info(f"未持有 {stock}")
```

---

## 5.4 账户信息

### context.portfolio

投资组合的完整信息：

```python
def handle_bar(context, bar_dict):
    portfolio = context.portfolio
    
    # 可用资金
    cash = portfolio.cash
    
    # 总资产
    total = portfolio.total_value
    
    # 持仓市值
    market_value = portfolio.market_value
    
    # 当日盈亏
    daily_pnl = portfolio.daily_pnl
    
    # 累计收益率
    returns = portfolio.total_returns
    
    logger.info(f"总资产: {total:.2f}, 可用: {cash:.2f}")
```

### 常用属性表

| 属性 | 含义 |
|------|------|
| `cash` | 可用资金 |
| `frozen_cash` | 冻结资金 |
| `total_value` | 总资产 |
| `market_value` | 持仓市值 |
| `daily_pnl` | 当日盈亏 |
| `daily_returns` | 当日收益率 |
| `total_returns` | 累计收益率 |
| `positions` | 所有持仓 |

### 遍历所有持仓

```python
def handle_bar(context, bar_dict):
    # 遍历所有持仓
    for stock, position in context.portfolio.positions.items():
        if position.quantity > 0:
            logger.info(f"{stock}: {position.quantity}股, 市值{position.market_value:.2f}")
```

---

## 5.5 实战：买入持有策略

让我们用学到的知识写一个完整的买入持有策略：

```python
def init(context):
    """初始化"""
    # 设置股票池
    context.stocks = ["000001.XSHE", "600519.XSHG"]  # 平安银行、贵州茅台
    
    # 设置每只股票的目标仓位
    context.target_percent = 1.0 / len(context.stocks)
    
    logger.info(f"股票池: {context.stocks}")
    logger.info(f"每只股票目标仓位: {context.target_percent:.1%}")


def handle_bar(context, bar_dict):
    """交易逻辑"""
    for stock in context.stocks:
        # 获取当前持仓
        position = get_position(stock)
        
        # 如果没有持仓，则买入
        if position.quantity == 0:
            # 调整到目标仓位
            order_target_percent(stock, context.target_percent)
            
            price = bar_dict[stock].close
            logger.info(f"买入 {stock}，价格: {price:.2f}")


def after_trading(context):
    """盘后汇总"""
    logger.info("=" * 50)
    logger.info(f"总资产: {context.portfolio.total_value:.2f}")
    logger.info(f"可用资金: {context.portfolio.cash:.2f}")
    logger.info(f"累计收益: {context.portfolio.total_returns:.2%}")
    
    for stock, pos in context.portfolio.positions.items():
        if pos.quantity > 0:
            logger.info(f"  {stock}: {pos.quantity}股, 盈亏{pos.pnl:.2f}")
```

---

## 💡 实践任务

- [ ] 使用 `history_bars()` 获取股票近 20 天的收盘价
- [ ] 尝试使用不同的下单函数
- [ ] 编写代码打印当前持仓的详细信息
- [ ] 修改买入持有策略，改成买入 3 只股票

---

## 📝 知识检查

### 基础问题

1. 如何获取某只股票最近 10 天的收盘价？
2. `order_shares()` 和 `order_target_percent()` 有什么区别？
3. 如何判断当前是否持有某只股票？

### 思考题

1. 为什么 T+1 交易制度下，买入当天不能卖出？
2. `order_target_percent(stock, 0.3)` 如果当前已经持有 40% 会发生什么？

<details>
<summary>💡 点击查看答案</summary>

**基础问题：**
1. `history_bars(stock, 10, '1d', 'close')`
2. `order_shares()` 是买入/卖出指定股数，`order_target_percent()` 是调整到目标比例（可能买入也可能卖出）
3. `get_position(stock).quantity > 0`

**思考题：**
1. T+1 是 A 股市场的交易规则，防止过度投机。在 RQAlpha 中，买入当天的股票 `sellable` 为 0。
2. 会自动卖出 10%，使持仓从 40% 降到 30%。

</details>

---

## 📌 核心要点

1. **history_bars()**：获取历史 K 线数据
2. **order_shares()**：按股数下单
3. **order_target_percent()**：调整到目标比例
4. **get_position()**：查询持仓信息
5. **context.portfolio**：查询账户资金

---

## ➡️ 下一课预告

基础知识已经学完，下一课我们将学习一些进阶技巧！

你将学到：
- 使用技术指标（TA-Lib）
- 编写多股票策略
- 使用定时任务
- 实现风险控制

**准备工作**：
- 安装 TA-Lib 库：`pip install TA-Lib`
- 复习前面学过的内容

👉 [**继续学习：第6课 - 策略进阶**](./lesson-06-advanced.md)

---

[← 上一课](./lesson-04-strategy-basics.md) | [返回目录](./README.md) | [下一课 →](./lesson-06-advanced.md)
