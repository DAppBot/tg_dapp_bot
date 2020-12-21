# `🤖 Blockchain Telegram Bot`

This telegram bot allows the user to easily and conveniently communicate with blockchains

## Features:
- supporting for **two** blockchains: `Tron` and `Ethereum`
- wallet manager
  - **subscription to events** of added wallets
  - **creating a wallet** and obtaining a private key via **a one-time link**
- **multilingual** (Russian and English are supported)



## Technologies
#### Main infrastructure:
- `asyncio` - for everything asynchronous in the project
- `asyncpg` - to interact with the `PostgreSQL`
- `aiohttp` - for a small web application to get private keys
- `aiogram` - the bot is based on an asynchronous framework for interacting with the `Telegram Bot API`
#### Blockchain infrastructure:
> **network asynchronous interaction with blockchain nodes is written independently (HTTP, WS)**
- [`eth_account`](https://github.com/ethereum/eth-account) - to create Ethereum wallets
- [`eth_utils`](https://github.com/ethereum/eth-utils) - to work with the Ethereum ecosystem (address validating, `base58` encoding/decoding, `ABI` decoding)
- [`tronapi`](https://github.com/iexbase/tron-api-python) - to create Tron wallets
- [`trx_utils`](https://github.com/iexbase/trx-utils) - to work with the Ethereum ecosystem (the Tron blockchain is similar to Ethereum, so everything is almost similar)
