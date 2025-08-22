import asyncio
import websockets
import json
from decimal import Decimal
from typing import Callable, Optional
from trading_types import OrderBook, OrderBookLevel
from logging_utils import setup_orderbook_logger

logger = setup_orderbook_logger()


class BybitOrderBookStream:
    def __init__(self, symbol: str = "BTCUSDT"):
        self.symbol = symbol
        self.ws_url = "wss://stream.bybit.com/v5/public/linear"
        self.websocket = None
        self.orderbook = None
        self.callback: Optional[Callable[[OrderBook], None]] = None
        
        # Local variables to track latest bid/ask data
        self.best_bid_price: Optional[Decimal] = None
        self.best_bid_size: Optional[Decimal] = None
        self.best_ask_price: Optional[Decimal] = None
        self.best_ask_size: Optional[Decimal] = None
        
    def set_callback(self, callback: Callable[[OrderBook], None]):
        self.callback = callback
        
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
            
    async def _process_message(self, data: dict):
        if data.get("topic", "").startswith("tickers"):
            ticker_data = data.get("data", {})
            
            if ticker_data:
                timestamp = data.get("ts", 0)
                
                # Update local variables when new data is available
                if ticker_data.get("bid1Price") and ticker_data.get("bid1Size"):
                    self.best_bid_price = Decimal(ticker_data["bid1Price"])
                    self.best_bid_size = Decimal(ticker_data["bid1Size"])
                
                if ticker_data.get("ask1Price") and ticker_data.get("ask1Size"):
                    self.best_ask_price = Decimal(ticker_data["ask1Price"])
                    self.best_ask_size = Decimal(ticker_data["ask1Size"])
                
                # Create OrderBookLevel objects from current best bid/ask
                bids = []
                asks = []
                
                if self.best_bid_price is not None and self.best_bid_size is not None:
                    bids.append(OrderBookLevel(price=self.best_bid_price, size=self.best_bid_size))
                
                if self.best_ask_price is not None and self.best_ask_size is not None:
                    asks.append(OrderBookLevel(price=self.best_ask_price, size=self.best_ask_size))
                
                self.orderbook = OrderBook(
                    symbol=ticker_data.get("symbol", self.symbol),
                    bids=bids,
                    asks=asks,
                    timestamp=timestamp
                )
                
                if self.callback:
                    self.callback(self.orderbook)
                
    async def disconnect(self):
        if self.websocket:
            await self.websocket.close()
            logger.info("Disconnected from WebSocket")
    
    def get_latest_orderbook(self) -> Optional[OrderBook]:
        return self.orderbook


async def main():
    def on_orderbook_update(orderbook: OrderBook):
        logger.info(f"{orderbook.timestamp}|{orderbook.symbol}|{orderbook.bids[0].size if orderbook.bids else 'N/A'}|{orderbook.bids[0].price if orderbook.bids else 'N/A'}|{orderbook.asks[0].price if orderbook.asks else 'N/A'}|{orderbook.asks[0].size if orderbook.asks else 'N/A'}")
    
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
        # Disconnect all streams
        await asyncio.gather(*[stream.disconnect() for stream in streams])


if __name__ == "__main__":
    asyncio.run(main())