# Components of a Trading System

This repository contains the fundamental components needed to build a cryptocurrency trading system using Bybit perpetual futures (linear futures).

## Getting Started

Sign up to Bybit using this referral link: [Bybit](https://www.bybit.com/invite?ref=MJ8JQNB)

## Components

1. **Common Types** - Shared data structures for orders, positions, and market data
2. **Order Book Streaming** - Real-time market data feed for BTC-USDT perpetual futures
3. **Order Management** - Limit and market order execution for perpetual futures
4. **Position & Order Retrieval** - Portfolio and order status monitoring

## Implementation Notes

- Built from scratch using only `requests` and `websockets` libraries
- No external trading libraries (pybit, ccxt) used
- Focuses on Bybit linear perpetual futures

## Structure

- `lectures/` - Educational materials
- `types.py` - Common data types and structures
- `orderbook_stream.py` - Real-time order book data streaming
- `order_manager.py` - Order placement and management
- `portfolio.py` - Position and order retrieval