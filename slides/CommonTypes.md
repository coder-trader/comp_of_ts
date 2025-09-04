---
marp: true
theme: funnel-magic
paginate: true
header: coder-trader.com
style: |
    @import './funnel-magic.css';
---

# Common Types

## Building Type-Safe Trading Systems

Essential data structures and enums for reliable trading infrastructure

---

# Enums - Core States

```python
class OrderSide(Enum):
    BUY = "Buy"
    SELL = "Sell"

class OrderType(Enum):
    MARKET = "Market"
    LIMIT = "Limit"
```
---

```python
class OrderStatus(Enum):
    NEW = "New"
    PARTIALLY_FILLED = "PartiallyFilled"
    FILLED = "Filled"
    CANCELLED = "Cancelled"
    REJECTED = "Rejected"
```

---

# Position

```python
class PositionSide(Enum):
    LONG = "Buy"
    SHORT = "Sell" 
    NONE = "None"
```

---

# Market Data Types
```python
@dataclass
class OrderBookLevel:
    price: Decimal
    size: Decimal

@dataclass
class OrderBook:
    symbol: str
    bids: List[OrderBookLevel]
    asks: List[OrderBookLevel]
    timestamp: int
```

---

# Order Management Types

```python
@dataclass
class Order:
    order_id: str
    symbol: str
    side: OrderSide
    order_type: OrderType
    quantity: Decimal
    price: Optional[Decimal]
    status: OrderStatus
    filled_quantity: Decimal
    average_price: Optional[Decimal]
    created_time: datetime.datetime
    updated_time: datetime.datetime
    time_in_force: str = "GTC"
```

---

# Portfolio & Account Types

```python
@dataclass
class Position:
    symbol: str
    side: PositionSide
    size: Decimal
    entry_price: Optional[Decimal]
    mark_price: Optional[Decimal]
    unrealized_pnl: Optional[Decimal]
    realized_pnl: Optional[Decimal]
    leverage: Optional[Decimal]
    margin: Optional[Decimal]
```

---

# Trade
```python
@dataclass
class Trade:
    trade_id: str
    order_id: str
    symbol: str
    side: OrderSide
    quantity: Decimal
    price: Decimal
    fee: Decimal
    timestamp: datetime.datetime
```

---

# Balance Types
```python
@dataclass
class Balance:
    coin: str
    wallet_balance: Decimal
    available_balance: Decimal
    used_balance: Decimal
```

---

# Account Information

```python
@dataclass
class AccountInfo:
    balances: List[Balance]
    positions: List[Position]
    total_wallet_balance: Decimal
    total_unrealized_pnl: Decimal
```

---

**Key Benefits:**
- Type safety with dataclasses and enums
- Decimal precision for financial calculations
- Clear separation of concerns
- Consistent data models across components

---

# Why Use Strong Types?

✅ **Type Safety** - Catch errors at compile time
✅ **Precision** - Decimal for accurate financial math
✅ **Clarity** - Self-documenting code structure
✅ **Consistency** - Uniform data models
✅ **Maintainability** - Easy to refactor and extend

**Remember:** Financial data requires precision - always use `Decimal` for prices and quantities!