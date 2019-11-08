import asyncio

from notifier.tron import TronNotifier
from notifier.ethereum import EthereumNotifier


loop = asyncio.get_event_loop()

tron = TronNotifier()
ethereum = EthereumNotifier()

ethereum.prepare_loop_to_start(loop)
tron.prepare_loop_to_start(loop)

loop.run_forever()