from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from enum import Enum
from decimal import Decimal
import datetime


class OrderSide(Enum):
    BUY = "Buy"
    SELL = "Sell"


class OrderType(Enum):
    MARKET = "Market"
    LIMIT = "Limit"


class OrderStatus(Enum):
    NEW = "New"
    PARTIALLY_FILLED = "PartiallyFilled"
    FILLED = "Filled"
    CANCELLED = "Cancelled"
    REJECTED = "Rejected"


class PositionSide(Enum):
    LONG = "Buy"
    SHORT = "Sell"
    NONE = "None"


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


@dataclass
class Balance:
    coin: str
    wallet_balance: Decimal
    available_balance: Decimal
    used_balance: Decimal


@dataclass
class AccountInfo:
    balances: List[Balance]
    positions: List[Position]
    total_wallet_balance: Decimal
    total_unrealized_pnl: Decimal