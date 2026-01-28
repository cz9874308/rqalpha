# 第 6 课：策略进阶

**⏱ 预计学习时间**：60 分钟  
**🎯 学习目标**：
- 学会使用技术指标
- 掌握多股票策略编写
- 了解定时任务功能
- 实现基本的风险控制

**📚 难度**：⭐⭐⭐ 进阶

---

## 📖 课程概览

恭喜你！经过前面 5 课的学习，你已经掌握了量化交易的基础知识。

这一课我们将学习一些进阶技巧：
1. 使用技术指标（如均线、RSI）
2. 管理多只股票的投资组合
3. 使用定时任务自动执行策略
4. 实现简单的风险控制

准备好进阶了吗？Let's go! 🚀

---

## 6.1 使用技术指标

### 什么是技术指标？

技术指标是通过数学公式从价格、成交量等数据中计算出来的数值，用于辅助判断买卖时机。

常见的技术指标：
- **均线（MA/EMA）**：判断趋势方向
- **RSI**：判断超买超卖
- **MACD**：判断趋势和动能
- **布林带**：判断波动范围

### 使用 TA-Lib 库

TA-Lib 是一个专业的技术分析库，提供了 150+ 种技术指标。

**安装**：

```bash
pip install TA-Lib
```

> ⚠️ **Windows 用户**：如果安装失败，需要先安装 TA-Lib 的 C 库。可以从 [这里](https://github.com/cgohlke/talib-build/releases) 下载预编译版本。

### 计算均线（SMA/EMA）

```python
import talib

def handle_bar(context, bar_dict):
    stock = context.stock
    
    # 获取历史收盘价
    prices = history_bars(stock, 30, '1d', 'close')
    
    # 计算简单移动平均线（SMA）
    ma5 = talib.SMA(prices, timeperiod=5)[-1]   # 5日均线
    ma20 = talib.SMA(prices, timeperiod=20)[-1] # 20日均线
    
    # 计算指数移动平均线（EMA）
    ema5 = talib.EMA(prices, timeperiod=5)[-1]
    ema20 = talib.EMA(prices, timeperiod=20)[-1]
    
    logger.info(f"MA5: {ma5:.2f}, MA20: {ma20:.2f}")
```

### 计算 RSI

RSI（相对强弱指数）：
- RSI > 70：超买区域，可能下跌
- RSI < 30：超卖区域，可能上涨

```python
import talib

def handle_bar(context, bar_dict):
    stock = context.stock
    prices = history_bars(stock, 20, '1d', 'close')
    
    # 计算14日RSI
    rsi = talib.RSI(prices, timeperiod=14)[-1]
    
    if rsi > 70:
        logger.info(f"RSI={rsi:.1f}，超买区域，考虑卖出")
    elif rsi < 30:
        logger.info(f"RSI={rsi:.1f}，超卖区域，考虑买入")
```

### 计算 MACD

```python
import talib

def handle_bar(context, bar_dict):
    stock = context.stock
    prices = history_bars(stock, 50, '1d', 'close')
    
    # 计算MACD
    macd, signal, hist = talib.MACD(prices)
    
    # 取最新值
    macd_value = macd[-1]
    signal_value = signal[-1]
    
    # 金叉：MACD 上穿 Signal
    if macd[-2] < signal[-2] and macd[-1] > signal[-1]:
        logger.info("MACD 金叉，买入信号")
    
    # 死叉：MACD 下穿 Signal
    if macd[-2] > signal[-2] and macd[-1] < signal[-1]:
        logger.info("MACD 死叉，卖出信号")
```

### 实战：均线交叉策略

```python
import talib

def init(context):
    context.stock = "000001.XSHE"
    context.short_period = 5   # 短期均线
    context.long_period = 20   # 长期均线


def handle_bar(context, bar_dict):
    stock = context.stock
    prices = history_bars(stock, context.long_period + 5, '1d', 'close')
    
    # 计算均线
    short_ma = talib.SMA(prices, timeperiod=context.short_period)
    long_ma = talib.SMA(prices, timeperiod=context.long_period)
    
    # 获取持仓
    position = get_position(stock)
    
    # 金叉：短均线上穿长均线
    if short_ma[-2] < long_ma[-2] and short_ma[-1] > long_ma[-1]:
        if position.quantity == 0:
            order_target_percent(stock, 0.95)
            logger.info(f"金叉买入，价格: {bar_dict[stock].close:.2f}")
    
    # 死叉：短均线下穿长均线
    elif short_ma[-2] > long_ma[-2] and short_ma[-1] < long_ma[-1]:
        if position.quantity > 0:
            order_target_percent(stock, 0)
            logger.info(f"死叉卖出，价格: {bar_dict[stock].close:.2f}")
```

---

## 6.2 多股票策略

### 股票池管理

```python
def init(context):
    # 定义股票池
    context.stocks = [
        "000001.XSHE",  # 平安银行
        "600519.XSHG",  # 贵州茅台
        "000858.XSHE",  # 五粮液
        "601318.XSHG",  # 中国平安
        "600036.XSHG",  # 招商银行
    ]
    
    # 计算每只股票的目标仓位
    context.weight = 1.0 / len(context.stocks)
```

### 等权重买入

```python
def handle_bar(context, bar_dict):
    for stock in context.stocks:
        position = get_position(stock)
        
        # 如果没有持仓，则买入
        if position.quantity == 0:
            order_target_percent(stock, context.weight)
            logger.info(f"买入 {stock}")
```

### 动态选股

```python
def init(context):
    context.stocks = []  # 初始为空


def before_trading(context):
    """每天开盘前更新股票池"""
    # 示例：获取沪深300成分股（需要 rqdatac）
    # context.stocks = index_components("000300.XSHG")
    
    # 或者手动筛选
    all_stocks = ["000001.XSHE", "600519.XSHG", "000858.XSHE"]
    
    # 根据某些条件筛选
    context.stocks = []
    for stock in all_stocks:
        prices = history_bars(stock, 20, '1d', 'close')
        if len(prices) > 0:
            ma20 = prices.mean()
            current = prices[-1]
            # 只选择在20日均线上方的股票
            if current > ma20:
                context.stocks.append(stock)
    
    logger.info(f"今日股票池: {context.stocks}")
```

---

## 6.3 定时任务（Scheduler）

### 什么是定时任务？

定时任务让你可以在特定时间执行特定逻辑，而不是每根 K 线都执行。

### run_daily() - 每日定时

```python
def init(context):
    context.stock = "000001.XSHE"
    
    # 每天 14:50 执行 rebalance 函数
    scheduler.run_daily(rebalance, time_rule=market_close(minute=10))


def rebalance(context, bar_dict):
    """收盘前10分钟执行调仓"""
    logger.info("执行每日调仓...")
    # 调仓逻辑
    order_target_percent(context.stock, 0.9)
```

### run_weekly() - 每周定时

```python
def init(context):
    context.stocks = ["000001.XSHE", "600519.XSHG"]
    
    # 每周一开盘后30分钟执行
    scheduler.run_weekly(
        weekly_rebalance,
        weekday=1,  # 周一
        time_rule=market_open(minute=30)
    )


def weekly_rebalance(context, bar_dict):
    """每周调仓"""
    logger.info("执行每周调仓...")
    weight = 1.0 / len(context.stocks)
    for stock in context.stocks:
        order_target_percent(stock, weight)
```

### run_monthly() - 每月定时

```python
def init(context):
    # 每月第一个交易日开盘执行
    scheduler.run_monthly(
        monthly_rebalance,
        tradingday=1,  # 第1个交易日
        time_rule=market_open(minute=30)
    )


def monthly_rebalance(context, bar_dict):
    """每月调仓"""
    logger.info("执行每月调仓...")
```

### 时间规则

| 规则 | 含义 | 示例 |
|------|------|------|
| `market_open(minute=N)` | 开盘后 N 分钟 | `market_open(minute=30)` |
| `market_close(minute=N)` | 收盘前 N 分钟 | `market_close(minute=10)` |

---

## 6.4 风险控制

### 止损策略

```python
def init(context):
    context.stock = "000001.XSHE"
    context.stop_loss = 0.05  # 5%止损


def handle_bar(context, bar_dict):
    stock = context.stock
    position = get_position(stock)
    
    if position.quantity > 0:
        # 计算当前亏损比例
        current_price = bar_dict[stock].close
        cost = position.avg_price
        loss_ratio = (cost - current_price) / cost
        
        # 如果亏损超过5%，止损
        if loss_ratio > context.stop_loss:
            order_target_percent(stock, 0)
            logger.info(f"触发止损，亏损 {loss_ratio:.2%}，卖出")
```

### 止盈策略

```python
def init(context):
    context.stock = "000001.XSHE"
    context.take_profit = 0.20  # 20%止盈


def handle_bar(context, bar_dict):
    stock = context.stock
    position = get_position(stock)
    
    if position.quantity > 0:
        # 计算当前盈利比例
        current_price = bar_dict[stock].close
        cost = position.avg_price
        profit_ratio = (current_price - cost) / cost
        
        # 如果盈利超过20%，止盈
        if profit_ratio > context.take_profit:
            order_target_percent(stock, 0)
            logger.info(f"触发止盈，盈利 {profit_ratio:.2%}，卖出")
```

### 最大仓位限制

```python
def init(context):
    context.stock = "000001.XSHE"
    context.max_position = 0.3  # 单只股票最多30%仓位


def handle_bar(context, bar_dict):
    stock = context.stock
    
    # 计算当前仓位比例
    position = get_position(stock)
    current_ratio = position.market_value / context.portfolio.total_value
    
    # 如果仓位过高，不再买入
    if current_ratio >= context.max_position:
        logger.info(f"{stock} 仓位已达上限 {context.max_position:.0%}")
        return
    
    # 正常交易逻辑...
```

### 综合风控示例

```python
def init(context):
    context.stock = "000001.XSHE"
    context.stop_loss = 0.05      # 5%止损
    context.take_profit = 0.15    # 15%止盈
    context.max_position = 0.3    # 最大仓位30%


def handle_bar(context, bar_dict):
    stock = context.stock
    position = get_position(stock)
    current_price = bar_dict[stock].close
    
    # 如果有持仓，检查止损止盈
    if position.quantity > 0:
        cost = position.avg_price
        pnl_ratio = (current_price - cost) / cost
        
        # 止损
        if pnl_ratio < -context.stop_loss:
            order_target_percent(stock, 0)
            logger.info(f"止损卖出，亏损 {pnl_ratio:.2%}")
            return
        
        # 止盈
        if pnl_ratio > context.take_profit:
            order_target_percent(stock, 0)
            logger.info(f"止盈卖出，盈利 {pnl_ratio:.2%}")
            return
    
    # 其他交易逻辑...
```

---

## 💡 实践任务

- [ ] 使用 TA-Lib 计算 RSI 指标
- [ ] 实现一个均线交叉策略
- [ ] 编写一个管理 5 只股票的投资组合策略
- [ ] 给策略加上 5% 止损和 15% 止盈

---

## 📝 知识检查

### 基础问题

1. 如何使用 TA-Lib 计算 20 日均线？
2. `scheduler.run_weekly()` 的 `weekday=1` 表示什么？
3. 止损比例设置为 5%，买入价 100 元，什么价格触发止损？

### 思考题

1. 均线周期选 5 日还是 20 日，会有什么区别？
2. 止损设置太紧会有什么问题？

<details>
<summary>💡 点击查看答案</summary>

**基础问题：**
1. `talib.SMA(prices, timeperiod=20)[-1]`
2. 每周一执行
3. 100 × (1 - 5%) = 95 元

**思考题：**
1. 5日均线更灵敏，信号更多但假信号也更多；20日均线更平滑，信号更可靠但反应较慢
2. 止损太紧会频繁被震出场，可能错过后续上涨

</details>

---

## 📌 核心要点

1. **技术指标**：使用 TA-Lib 计算各种指标
2. **多股票策略**：用列表管理股票池，循环处理
3. **定时任务**：`scheduler.run_daily/weekly/monthly`
4. **止损止盈**：计算盈亏比例，设置阈值
5. **仓位控制**：限制单只股票最大仓位

---

## ➡️ 下一课预告

恭喜！你已经学完了所有核心内容！

最后一课我们将介绍：
- Mod 扩展系统
- 进阶学习路径
- 社区资源
- 下一步建议

👉 [**继续学习：第7课 - 下一步学习**](./lesson-07-next-steps.md)

---

[← 上一课](./lesson-05-data-and-trading.md) | [返回目录](./README.md) | [下一课 →](./lesson-07-next-steps.md)
