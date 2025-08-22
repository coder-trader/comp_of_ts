import requests
import hashlib
import hmac
import time
import json
import logging
from decimal import Decimal
from typing import Optional, Dict, Any
from trading_types import Order, OrderSide, OrderType, OrderStatus
import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BybitOrderManager:
    def __init__(self, api_key: str, api_secret: str, testnet: bool = True):
        self.api_key = api_key
        self.api_secret = api_secret
        self.testnet = testnet
        
        if testnet:
            self.base_url = "https://api-testnet.bybit.com"
        else:
            self.base_url = "https://api.bybit.com"
            
        self.session = requests.Session()
        self.recv_window = 5000
    
    def _generate_signature(self, timestamp: str, params: str) -> str:
        param_str = timestamp + self.api_key + self.recv_window + params
        signature = hmac.new(
            bytes(self.api_secret, "utf-8"),
            param_str.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()
        return signature
    
    def _get_headers(self, params: str) -> Dict[str, str]:
        timestamp = str(int(time.time() * 1000))
        signature = self._generate_signature(timestamp, params)
        
        return {
            "X-BAPI-API-KEY": self.api_key,
            "X-BAPI-SIGN": signature,
            "X-BAPI-SIGN-TYPE": "2",
            "X-BAPI-TIMESTAMP": timestamp,
            "X-BAPI-RECV-WINDOW": str(self.recv_window),
            "Content-Type": "application/json"
        }
    
    def _make_request(self, method: str, endpoint: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        url = f"{self.base_url}{endpoint}"
        params_str = json.dumps(params) if params else ""
        headers = self._get_headers(params_str)
        
        try:
            if method.upper() == "GET":
                response = self.session.get(url, headers=headers, params=params)
            elif method.upper() == "POST":
                response = self.session.post(url, headers=headers, json=params)
            else:
                raise ValueError(f"Unsupported method: {method}")
                
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
            raise
    
    def place_market_order(
        self,
        symbol: str,
        side: OrderSide,
        quantity: Decimal,
        reduce_only: bool = False
    ) -> Optional[Order]:
        params = {
            "category": "linear",
            "symbol": symbol,
            "side": side.value,
            "orderType": OrderType.MARKET.value,
            "qty": str(quantity),
            "reduceOnly": reduce_only
        }
        
        try:
            response = self._make_request("POST", "/v5/order/create", params)
            
            if response.get("retCode") == 0:
                result = response.get("result", {})
                logger.info(f"Market order placed successfully: {result.get('orderId')}")
                
                return Order(
                    order_id=result.get("orderId", ""),
                    symbol=symbol,
                    side=side,
                    order_type=OrderType.MARKET,
                    quantity=quantity,
                    price=None,
                    status=OrderStatus.NEW,
                    filled_quantity=Decimal("0"),
                    average_price=None,
                    created_time=datetime.datetime.now(),
                    updated_time=datetime.datetime.now()
                )
            else:
                logger.error(f"Failed to place market order: {response}")
                return None
                
        except Exception as e:
            logger.error(f"Error placing market order: {e}")
            return None
    
    def place_limit_order(
        self,
        symbol: str,
        side: OrderSide,
        quantity: Decimal,
        price: Decimal,
        time_in_force: str = "GTC",
        reduce_only: bool = False
    ) -> Optional[Order]:
        params = {
            "category": "linear",
            "symbol": symbol,
            "side": side.value,
            "orderType": OrderType.LIMIT.value,
            "qty": str(quantity),
            "price": str(price),
            "timeInForce": time_in_force,
            "reduceOnly": reduce_only
        }
        
        try:
            response = self._make_request("POST", "/v5/order/create", params)
            
            if response.get("retCode") == 0:
                result = response.get("result", {})
                logger.info(f"Limit order placed successfully: {result.get('orderId')}")
                
                return Order(
                    order_id=result.get("orderId", ""),
                    symbol=symbol,
                    side=side,
                    order_type=OrderType.LIMIT,
                    quantity=quantity,
                    price=price,
                    status=OrderStatus.NEW,
                    filled_quantity=Decimal("0"),
                    average_price=None,
                    created_time=datetime.datetime.now(),
                    updated_time=datetime.datetime.now(),
                    time_in_force=time_in_force
                )
            else:
                logger.error(f"Failed to place limit order: {response}")
                return None
                
        except Exception as e:
            logger.error(f"Error placing limit order: {e}")
            return None
    
    def cancel_order(self, symbol: str, order_id: str) -> bool:
        params = {
            "category": "linear",
            "symbol": symbol,
            "orderId": order_id
        }
        
        try:
            response = self._make_request("POST", "/v5/order/cancel", params)
            
            if response.get("retCode") == 0:
                logger.info(f"Order cancelled successfully: {order_id}")
                return True
            else:
                logger.error(f"Failed to cancel order: {response}")
                return False
                
        except Exception as e:
            logger.error(f"Error cancelling order: {e}")
            return False
    
    def get_order_status(self, symbol: str, order_id: str) -> Optional[Order]:
        params = {
            "category": "linear",
            "symbol": symbol,
            "orderId": order_id
        }
        
        try:
            response = self._make_request("GET", "/v5/order/realtime", params)
            
            if response.get("retCode") == 0:
                orders = response.get("result", {}).get("list", [])
                if orders:
                    order_data = orders[0]
                    return self._parse_order(order_data)
            
            logger.error(f"Order not found: {order_id}")
            return None
            
        except Exception as e:
            logger.error(f"Error getting order status: {e}")
            return None
    
    def _parse_order(self, order_data: Dict[str, Any]) -> Order:
        return Order(
            order_id=order_data.get("orderId", ""),
            symbol=order_data.get("symbol", ""),
            side=OrderSide(order_data.get("side", "")),
            order_type=OrderType(order_data.get("orderType", "")),
            quantity=Decimal(order_data.get("qty", "0")),
            price=Decimal(order_data.get("price", "0")) if order_data.get("price") else None,
            status=OrderStatus(order_data.get("orderStatus", "")),
            filled_quantity=Decimal(order_data.get("cumExecQty", "0")),
            average_price=Decimal(order_data.get("avgPrice", "0")) if order_data.get("avgPrice") else None,
            created_time=datetime.datetime.fromtimestamp(int(order_data.get("createdTime", "0")) / 1000),
            updated_time=datetime.datetime.fromtimestamp(int(order_data.get("updatedTime", "0")) / 1000),
            time_in_force=order_data.get("timeInForce", "GTC")
        )


def main():
    from decouple import config
    
    API_KEY = config('BYBIT_API_KEY')
    API_SECRET = config('BYBIT_API_SECRET')
    TESTNET = config('BYBIT_TESTNET', default=True, cast=bool)
    
    order_manager = BybitOrderManager(API_KEY, API_SECRET, testnet=TESTNET)
    
    # Example usage - place a limit buy order
    order = order_manager.place_limit_order(
        symbol="BTCUSDT",
        side=OrderSide.BUY,
        quantity=Decimal("0.001"),
        price=Decimal("30000")
    )
    
    if order:
        print(f"Order placed: {order}")
        
        # Check order status
        status = order_manager.get_order_status("BTCUSDT", order.order_id)
        if status:
            print(f"Order status: {status}")


if __name__ == "__main__":
    main()