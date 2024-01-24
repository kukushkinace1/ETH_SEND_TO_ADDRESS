from web3 import Web3
import random
import time
from loguru import logger
from sys import stderr

# Определение диапазона суммы перевода и времени задержки
min_balance = 0.0004  # минимальная сумма остатка ETH, меньше опасно ставить может не хватить на транзакцию, который стоит 0.0002 при газе 8 гвей
max_balance = 0.0005  # максимальная
min_delay = 250  # минимальное время задержки в секундах
max_delay = 350  # максимальное время задержки в секундах
GWEI_CONTROL = 20

logger.remove()
logger.add(stderr, format="<white>{time:HH:mm:ss}</white> | <level>{level: <3}</level> | <level>{message}</level>")

web3 = Web3(Web3.HTTPProvider('https://ethereum.publicnode.com'))

with open('private_keys.txt', 'r') as file:
    private_keys = file.read().splitlines()

with open('to_address.txt', 'r') as file:
    WITHDRAW = [line.strip() for line in file]

WITHDRAW_ACC = {}
if len(WITHDRAW) == len(private_keys):
    wal_data = list(zip(WITHDRAW, private_keys))
    for address, acc in wal_data:
        WITHDRAW_ACC[acc] = address
else:
    logger.error("Количество приватников и кошельков разное")


def cheker_gwei():
    max_gwei = GWEI_CONTROL * 10 ** 9
    if web3.eth.gas_price > max_gwei:
        logger.info('Газ большой, пойду спать')
        while web3.eth.gas_price > max_gwei:
            time.sleep(60)
        logger.info('Газ в норме. Продолжаю работу')


for private in private_keys:
    cheker_gwei()

    wallet = web3.eth.account.from_key(private).address
    all_balance = web3.eth.get_balance(wallet)
    amount_to_send = all_balance - web3.to_wei(random.uniform(min_balance, max_balance), 'ether')

    if amount_to_send < 0:
        logger.warning(f'{wallet} мало баланса, пропускаем')
        continue

    try:
        # Подготовьте данные для транзакции
        tx = {
            'from': wallet,
            'to': web3.to_checksum_address(WITHDRAW_ACC[private]),
            'chainId': web3.eth.chain_id,
            'nonce': web3.eth.get_transaction_count(wallet),
            'value': amount_to_send,
            'gasPrice': int(web3.eth.gas_price*1.1),
            }
        gasLimit = web3.eth.estimate_gas(tx)
        tx['gas'] = int(gasLimit * 1.2)

        signed_tx = web3.eth.account.sign_transaction(tx, private)
        tx_hash = web3.eth.send_raw_transaction(signed_tx.rawTransaction)
        logger.info(f"{wallet} send to {WITHDRAW_ACC[private]}")
        status = web3.eth.wait_for_transaction_receipt(tx_hash, timeout=360).status
        if status == 1:
            logger.success(f"tx: https://etherscan.io/tx/{tx_hash.hex()}")
        else:
            logger.error(f'[{wallet}] transaction failed!')
    except Exception as err:
        print(err)

    time.sleep(random.randint(min_delay, max_delay))


