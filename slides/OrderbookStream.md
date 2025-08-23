---
marp: true
theme: funnel-magic
paginate: true
header: coder-trader.com
style: |
    @import './funnel-magic.css';
---

# Orderbook Streaming

## Real-time Market Data Feed

WebSocket connections for live trading data from Bybit

---

# BybitOrderBookStream Class

```python
class BybitOrderBookStream:
    def __init__(self, symbol: str = "BTCUSDT"):
        self.symbol = symbol
        self.ws_url = "wss://stream.bybit.com/v5/public/linear"
        self.websocket = None
        self.orderbook = None
        self.callback: Optional[Callable[[OrderBook], None]] = None
        
        # Track latest bid/ask data
        self.best_bid_price: Optional[Decimal] = None
        self.best_bid_size: Optional[Decimal] = None
        self.best_ask_price: Optional[Decimal] = None
        self.best_ask_size: Optional[Decimal] = None
```

---
**Key Components:**
- WebSocket URL for Bybit public stream
- Symbol-specific connection
- Callback pattern for data handling

---

# WebSocket Connection

```python
async def connect(self):
    try:
        self.websocket = await websockets.connect(self.ws_url)
        logger.info(f"Connected to Bybit WebSocket")
        
        subscribe_msg = {
            "op": "subscribe",
            "args": [f"tickers.{self.symbol}"]
        }
        
        await self.websocket.send(json.dumps(subscribe_msg))
        logger.info(f"Subscribed to {self.symbol} ticker")
        
    except Exception as e:
        logger.error(f"Failed to connect: {e}")
        raise
```
---
**Process:**
1. Establish WebSocket connection
2. Send subscription message for symbol ticker
3. Log connection status and errors

---

# Message Processing Loop

```python
async def listen(self):
    if not self.websocket:
        await self.connect()
        
    try:
        async for message in self.websocket:
            data = json.loads(message)
            await self._process_message(data)
            
    except websockets.exceptions.ConnectionClosed:
        logger.warning("WebSocket connection closed")
    except Exception as e:
        logger.error(f"Error in listen: {e}")
```
---
**Features:**
- Auto-connect if not connected
- Continuous message processing
- Graceful error handling
- Connection closed detection

---

# Data Processing

```python
async def _process_message(self, data: dict):
    if data.get("topic", "").startswith("tickers"):
        ticker_data = data.get("data", {})
        
        if ticker_data:
            # Update bid data
            if ticker_data.get("bid1Price") and ticker_data.get("bid1Size"):
                self.best_bid_price = Decimal(ticker_data["bid1Price"])
                self.best_bid_size = Decimal(ticker_data["bid1Size"])
            
            # Update ask data  
            if ticker_data.get("ask1Price") and ticker_data.get("ask1Size"):
                self.best_ask_price = Decimal(ticker_data["ask1Price"])
                self.best_ask_size = Decimal(ticker_data["ask1Size"])
```
---
**Key Points:**
- Filter for ticker messages
- Extract best bid/ask prices and sizes
- Use Decimal for precise financial data

---

# OrderBook Construction

```python
# Create OrderBookLevel objects
bids = []
asks = []

if self.best_bid_price is not None and self.best_bid_size is not None:
    bids.append(OrderBookLevel(
        price=self.best_bid_price, 
        size=self.best_bid_size
    ))

if self.best_ask_price is not None and self.best_ask_size is not None:
    asks.append(OrderBookLevel(
        price=self.best_ask_price, 
        size=self.best_ask_size
    ))

self.orderbook = OrderBook(
    symbol=ticker_data.get("symbol", self.symbol),
    bids=bids,
    asks=asks,
    timestamp=timestamp
)
```

---

# Callback Pattern

```python
# In _process_message method
if self.callback:
    self.callback(self.orderbook)

# Setting callback
def set_callback(self, callback: Callable[[OrderBook], None]):
    self.callback = callback

# Usage example
def on_orderbook_update(orderbook: OrderBook):
    logger.info(f"{orderbook.timestamp}|{orderbook.symbol}|"
                f"{orderbook.bids[0].price}|{orderbook.asks[0].price}")

stream = BybitOrderBookStream("BTCUSDT")
stream.set_callback(on_orderbook_update)
```
---
**Benefits:**
- Decoupled data processing
- Flexible response handling
- Easy to extend functionality

---

# Multiple Symbol Streaming

```python
async def main():
    # Create streams for multiple symbols
    streams = [
        BybitOrderBookStream("BTCUSDT"),
        BybitOrderBookStream("ETHUSDT"), 
        BybitOrderBookStream("SOLUSDT"),
        BybitOrderBookStream("XRPUSDT")
    ]
    
    # Set callback for all streams
    for stream in streams:
        stream.set_callback(on_orderbook_update)
    
    try:
        # Run all streams concurrently
        await asyncio.gather(*[stream.listen() for stream in streams])
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    finally:
        await asyncio.gather(*[stream.disconnect() for stream in streams])
```

---

# Data Format Example

**Structured Log Output:**
```
1705312215123|BTCUSDT|1.5|42150.50|42151.00|2.3
1705312215456|ETHUSDT|5.2|2580.25|2580.50|3.1
1705312215789|SOLUSDT|100|95.75|95.80|200
```

**Format:** `timestamp|symbol|bid_size|bid_price|ask_price|ask_size`

**Perfect for:**
- Real-time monitoring
- Data analysis
- Strategy backtesting
- Performance metrics

---

# Running the Stream

**Start streaming:**
```bash
python orderbook_stream.py
```

**Monitor in real-time:**
```bash
# Tail today's orderbook log
tail -f logs/orderbook_$(date +%Y-%m-%d).log

# Filter specific symbol
tail -f logs/orderbook_$(date +%Y-%m-%d).log | grep BTCUSDT

# Monitor spread changes
tail -f logs/orderbook_$(date +%Y-%m-%d).log | \
  awk -F'|' '{print $2 " spread: " ($5-$4)}'
```

---

# Key Features Summary

✅ **Async WebSocket** - Non-blocking real-time data
✅ **Multiple Symbols** - Concurrent streams
✅ **Callback Pattern** - Flexible data handling  
✅ **Error Recovery** - Connection management
✅ **Decimal Precision** - Accurate financial data
✅ **Structured Logging** - Parseable data format
✅ **Graceful Shutdown** - Clean disconnection

---
**Use Cases:**
- Market making strategies
- Arbitrage detection  
- Real-time price monitoring
- Spread analysis
- Market data recording