import requests
import hashlib
import hmac
import time
import json
import logging
from decimal import Decimal
from typing import List, Optional, Dict, Any
from trading_types import Position, Order, Balance, AccountInfo, PositionSide, OrderSide, OrderType, OrderStatus
import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BybitPortfolioManager:
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
        param_str = timestamp + self.api_key + str(self.recv_window) + params
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
        params_str = ""
        
        if method.upper() == "GET" and params:
            params_str = "&".join([f"{k}={v}" for k, v in params.items()])
        elif method.upper() == "POST" and params:
            params_str = json.dumps(params)
        
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
    
    def get_positions(self, symbol: Optional[str] = None) -> List[Position]:
        params = {
            "category": "linear"
        }
        
        if symbol:
            params["symbol"] = symbol
        
        try:
            response = self._make_request("GET", "/v5/position/list", params)
            
            if response.get("retCode") == 0:
                positions_data = response.get("result", {}).get("list", [])
                positions = []
                
                for pos_data in positions_data:
                    position = self._parse_position(pos_data)
                    if position.size != Decimal("0"):  # Only include non-zero positions
                        positions.append(position)
                
                return positions
            else:
                logger.error(f"Failed to get positions: {response}")
                return []
                
        except Exception as e:
            logger.error(f"Error getting positions: {e}")
            return []
    
    def get_orders(
        self,
        symbol: Optional[str] = None,
        order_status: Optional[str] = None,
        limit: int = 50
    ) -> List[Order]:
        params = {
            "category": "linear",
            "limit": limit
        }
        
        if symbol:
            params["symbol"] = symbol
        if order_status:
            params["orderStatus"] = order_status
        
        try:
            response = self._make_request("GET", "/v5/order/realtime", params)
            
            if response.get("retCode") == 0:
                orders_data = response.get("result", {}).get("list", [])
                orders = []
                
                for order_data in orders_data:
                    order = self._parse_order(order_data)
                    orders.append(order)
                
                return orders
            else:
                logger.error(f"Failed to get orders: {response}")
                return []
                
        except Exception as e:
            logger.error(f"Error getting orders: {e}")
            return []
    
    def get_order_history(
        self,
        symbol: Optional[str] = None,
        limit: int = 50
    ) -> List[Order]:
        params = {
            "category": "linear",
            "limit": limit
        }
        
        if symbol:
            params["symbol"] = symbol
        
        try:
            response = self._make_request("GET", "/v5/order/history", params)
            
            if response.get("retCode") == 0:
                orders_data = response.get("result", {}).get("list", [])
                orders = []
                
                for order_data in orders_data:
                    order = self._parse_order(order_data)
                    orders.append(order)
                
                return orders
            else:
                logger.error(f"Failed to get order history: {response}")
                return []
                
        except Exception as e:
            logger.error(f"Error getting order history: {e}")
            return []
    
    def get_account_info(self) -> Optional[AccountInfo]:
        try:
            response = self._make_request("GET", "/v5/account/wallet-balance", {"accountType": "UNIFIED"})
            
            if response.get("retCode") == 0:
                account_data = response.get("result", {}).get("list", [])
                
                if account_data:
                    wallet_data = account_data[0]
                    
                    balances = []
                    for coin_data in wallet_data.get("coin", []):
                        balance = Balance(
                            coin=coin_data.get("coin", ""),
                            wallet_balance=Decimal(coin_data.get("walletBalance", "0")),
                            available_balance=Decimal(coin_data.get("availableToWithdraw", "0")),
                            used_balance=Decimal(coin_data.get("locked", "0"))
                        )
                        balances.append(balance)
                    
                    positions = self.get_positions()
                    
                    return AccountInfo(
                        balances=balances,
                        positions=positions,
                        total_wallet_balance=Decimal(wallet_data.get("totalWalletBalance", "0")),
                        total_unrealized_pnl=Decimal(wallet_data.get("totalUnrealisedPnl", "0"))
                    )
            
            logger.error(f"Failed to get account info: {response}")
            return None
            
        except Exception as e:
            logger.error(f"Error getting account info: {e}")
            return None
    
    def _parse_position(self, pos_data: Dict[str, Any]) -> Position:
        size = Decimal(pos_data.get("size", "0"))
        side_str = pos_data.get("side", "None")
        
        if size == Decimal("0"):
            side = PositionSide.NONE
        else:
            side = PositionSide(side_str)
        
        return Position(
            symbol=pos_data.get("symbol", ""),
            side=side,
            size=size,
            entry_price=Decimal(pos_data.get("avgPrice", "0")) if pos_data.get("avgPrice") else None,
            mark_price=Decimal(pos_data.get("markPrice", "0")) if pos_data.get("markPrice") else None,
            unrealized_pnl=Decimal(pos_data.get("unrealisedPnl", "0")) if pos_data.get("unrealisedPnl") else None,
            realized_pnl=Decimal(pos_data.get("cumRealisedPnl", "0")) if pos_data.get("cumRealisedPnl") else None,
            leverage=Decimal(pos_data.get("leverage", "0")) if pos_data.get("leverage") else None,
            margin=Decimal(pos_data.get("positionIM", "0")) if pos_data.get("positionIM") else None
        )
    
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
    
    portfolio = BybitPortfolioManager(API_KEY, API_SECRET, testnet=TESTNET)
    
    # Get account info
    account_info = portfolio.get_account_info()
    if account_info:
        print(f"Total Wallet Balance: {account_info.total_wallet_balance}")
        print(f"Total Unrealized PnL: {account_info.total_unrealized_pnl}")
        
        print("\nBalances:")
        for balance in account_info.balances:
            if balance.wallet_balance > Decimal("0"):
                print(f"{balance.coin}: {balance.wallet_balance}")
    
    # Get positions
    positions = portfolio.get_positions()
    if positions:
        print("\nPositions:")
        for position in positions:
            print(f"{position.symbol}: {position.side.value} {position.size} @ {position.entry_price}")
    
    # Get active orders
    orders = portfolio.get_orders()
    if orders:
        print("\nActive Orders:")
        for order in orders:
            print(f"{order.symbol}: {order.side.value} {order.quantity} @ {order.price} ({order.status.value})")


if __name__ == "__main__":
    main()