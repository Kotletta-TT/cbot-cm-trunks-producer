from MegafonAPI import VATS
import pika
import json
import time
import re
from models import Trunk
from config import RABBIT_HOST, RABBIT_PORT, RABBIT_QUEUE, LOG_NAME, TIMEOUT_REQUEST, conf_parser
from log_init import log_on

logger = log_on(LOG_NAME)
DATA_ACCESS = conf_parser('contracts.yaml')


def smart_timeout(attempts):
    if attempts <= 10:
        return time.sleep(10)
    else:
        return time.sleep(60)


def check_trunk(trunk_username):
    return re.match(r'^[0-9]*admin[0-9]+$', trunk_username)


def connect_rabbit_queue(fn):
    def wrapped():
        attempts = 0
        while True:
            try:
                connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBIT_HOST, port=RABBIT_PORT))
                channel = connection.channel()
                logger.debug(f'Connect to RabbitMQ address: {RABBIT_HOST}')
                attempts = 0
                break
            except:
                logger.error(f'RabbitMQ CONNECTION ERROR: {RABBIT_HOST}')
                smart_timeout(attempts)
                attempts += 1

        channel.queue_declare(queue=RABBIT_QUEUE)
        logger.debug(f'Queue select: {RABBIT_QUEUE}')
        fn(channel)
        connection.close()

    return wrapped


@connect_rabbit_queue
def request_api(channel):
    for obj in DATA_ACCESS:
        logger.info(f" Request to object: {obj['obj']} - provider: {obj['provider']}")
        vats = VATS(address=obj['address'],
                    user=obj['login'],
                    password=obj['password'])

        if vats.getUsers():
            for trunk in vats.users:
                try:
                    trunk_username = trunk['n']
                    phone = trunk['tn'][0] if 'tn' in trunk else None
                    if check_trunk(trunk_username):
                        send_trunk = Trunk(provider=obj['provider'],
                                           obj=obj['obj'],
                                           trunk_username=trunk_username,
                                           trunk_password=obj['trunk_password'],
                                           phone=phone,
                                           attributes={})  # Надо ли что-то из Мегафона класть в атрибуты
                        message = json.dumps(send_trunk.__dict__)
                        channel.basic_publish(exchange='', routing_key=RABBIT_QUEUE, body=message)
                        logger.info(f'Send trunk: {trunk["n"]} - {phone} queue: {RABBIT_QUEUE}')
                except:
                    logger.warning(f'Trunk: {trunk} incorrect JSON don`t send RabbitMQ')
                    continue
        else:
            logger.warning(f'NO CONNECTION to {obj["provider"]} OR no TRUNKS to {obj["obj"]}')


def main_loop():
    while True:
        request_api()
        time.sleep(TIMEOUT_REQUEST)


if __name__ == '__main__':
    main_loop()
