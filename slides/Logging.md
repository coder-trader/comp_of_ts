---
marp: true
theme: funnel-magic
paginate: true
header: coder-trader.com
style: |
    @import './funnel-magic.css';
---

# Logging in Trading Systems

## Essential for Monitoring & Debugging

Structured logging approach for reliable trading infrastructure

---

# Logger Setup Function

```python
def setup_orderbook_logger():
    """Setup a custom logger for orderbook data with date-based log files."""
    # Create logs directory if it doesn't exist
    logs_dir = "logs"
    os.makedirs(logs_dir, exist_ok=True)
    
    # Create logger
    logger = logging.getLogger("orderbook")
    logger.setLevel(logging.INFO)
    
    # Remove existing handlers to avoid duplicates
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
```
---

**Key Features:**
- Creates `logs/` directory automatically
- Named logger for specific components
- Prevents handler duplication

---

# File & Console Handlers

```python
# Create file handler with date-based filename
date_str = datetime.now().strftime("%Y-%m-%d")
log_file = os.path.join(logs_dir, f"orderbook_{date_str}.log")

file_handler = logging.FileHandler(log_file)
file_handler.setLevel(logging.INFO)

# Create console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
```

**Dual Output:**
- **File**: `logs/orderbook_2024-01-15.log` (date-based rotation)
- **Console**: Real-time terminal output

---

# Formatter & Logger Assembly

```python
# Create formatter
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

# Add handlers to logger
logger.addHandler(file_handler)
logger.addHandler(console_handler)

return logger
```
---
**Log Format:**
```
2024-01-15 10:30:15,123 - orderbook - INFO - Connected to Bybit WebSocket
```

---

# Logger Usage in Practice

```python
# Import and setup at module level
from logging_utils import setup_orderbook_logger
logger = setup_orderbook_logger()

class BybitOrderBookStream:
    async def connect(self):
        try:
            self.websocket = await websockets.connect(self.ws_url)
            logger.info(f"Connected to Bybit WebSocket")
            
            # Subscribe to ticker
            await self.websocket.send(json.dumps(subscribe_msg))
            logger.info(f"Subscribed to {self.symbol} ticker")
            
        except Exception as e:
            logger.error(f"Failed to connect: {e}")
            raise
```

---

# Structured Orderbook Logging

```python
def on_orderbook_update(orderbook: OrderBook):
    logger.info(
        f"{orderbook.timestamp}|"
        f"{orderbook.symbol}|"
        f"{orderbook.bids[0].size if orderbook.bids else 'N/A'}|"
        f"{orderbook.bids[0].price if orderbook.bids else 'N/A'}|"
        f"{orderbook.asks[0].price if orderbook.asks else 'N/A'}|"
        f"{orderbook.asks[0].size if orderbook.asks else 'N/A'}"
    )
```

**Pipe-Delimited Format:**
```
1705312215123|BTCUSDT|1.5|42150.50|42151.00|2.3
```

Perfect for data analysis and monitoring!

---

# Running & Monitoring Logs

**Start the orderbook stream:**
```bash
python orderbook_stream.py
```

**Tail logs in real-time (separate terminal):**
```bash
# Follow today's log file
tail -f logs/orderbook_$(date +%Y-%m-%d).log

# Follow with grep filtering
tail -f logs/orderbook_$(date +%Y-%m-%d).log | grep BTCUSDT

# Show last 100 lines and follow
tail -n 100 -f logs/orderbook_$(date +%Y-%m-%d).log
```
---
**Alternative monitoring:**
```bash
# Watch log file size grow
watch -n 1 'ls -la logs/'

# Monitor multiple files
tail -f logs/*.log
```

---

# Log File Organization

```
logs/
├── orderbook_2024-01-15.log    # Today's logs
├── orderbook_2024-01-14.log    # Yesterday's logs  
├── orderbook_2024-01-13.log    # Historical logs
└── ...
```

**Benefits:**
✅ **Daily Rotation** - Automatic date-based files
✅ **Historical Data** - Keep logs for analysis
✅ **Easy Navigation** - Find specific day's activity
✅ **Manageable Size** - Prevent huge single files

---

# Logging Best Practices

**✅ DO:**
- Use structured, parseable log formats
- Include timestamps and component names
- Log connection events and errors
- Use appropriate log levels (INFO, ERROR, DEBUG)
- Create logs directory automatically

**❌ DON'T:**
- Log sensitive data (API keys, secrets)
- Create overly verbose logs in production
- Forget to handle log file rotation
- Mix different data formats in same log

**Remember:** Good logging is essential for debugging production trading systems!