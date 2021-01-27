from MegafonAPI import VATS
import pika
import os
import logging
import json
import time
from config import DATA_ACCESS

RABBIT_HOST = os.environ.get('RABBIT_HOST')
RABBIT_QUEUE = os.environ.get('RABBIT_QUEUE')
LOG_LEVEL = os.environ.get('LOG_LEVEL') if os.environ.get('LOG_LEVEL') is not None else 'WARNING'
TIMEOUT_REQUEST = int(os.environ.get('TIMEOUT_REQUEST')) if os.environ.get('TIMEOUT_REQUEST') is not None else 0

logger = logging.getLogger('TRUNK-INFO')  # создаем логгер приложения
logger.setLevel(LOG_LEVEL)
logger.propagate = False  # отключаем стрим сообщений в корневой логгер
console_handler = logging.StreamHandler()  # создаем объект Stream для вывода логов только на экран
logger.addHandler(console_handler)
formatter = logging.Formatter(fmt='%(levelname)s:[%(name)s]:%(message)s')
console_handler.setFormatter(formatter)


def smart_timeout(attempts):
    if attempts <= 10:
        return time.sleep(10)
    else:
        return time.sleep(60)


def connect_rabbit_queue(fn):
    def wrapped():
        attempts = 0
        while True:
            try:
                connection = pika.BlockingConnection(pika.ConnectionParameters(RABBIT_HOST))
                channel = connection.channel()
                logger.debug(f'Connect to RabbitMQ address: {RABBIT_HOST}')
                attempts = 0
                break
            except:
                logger.error(f'RabbitMQ CONNECTION ERROR: {RABBIT_HOST}')
                smart_timeout(attempts)
                attempts += 1

        """# создать проверку существования очереди"""
        channel.queue_declare(queue=RABBIT_QUEUE)
        logger.debug(f'Queue select: {RABBIT_QUEUE}')
        fn(channel)
        connection.close()

    return wrapped


@connect_rabbit_queue
def request_api(channel):
    for contract in DATA_ACCESS:
        logger.info(f" Request to contract: {contract['name']} - provider: {contract['provider']}")
        vats = VATS(address=contract['address'],
                    user=contract['login'],
                    password=contract['password'])

        if vats.getSimCards():
            for sim in vats.simcards:
                try:
                    sim['provider'] = contract['provider']
                    sim['contract'] = contract['name']
                    message = json.dumps(sim)
                except:
                    logger.warning(f'Sim: {sim} incorrect JSON don`t send RabbitMQ')
                    continue
                channel.basic_publish(exchange='', routing_key='hello', body=message)
                logger.info(f'Send phone: {sim["tn"]} queue: {RABBIT_QUEUE}')
        else:
            logger.warning(f'NO CONNECTION to {contract["provider"]} OR no SIM to {contract["name"]}')


def main_loop():
    while True:
        request_api()
        time.sleep(TIMEOUT_REQUEST)


if __name__ == '__main__':
    main_loop()
