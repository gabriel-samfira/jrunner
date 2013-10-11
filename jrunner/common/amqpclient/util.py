from jrunner.common.amqpclient.client import Producer
from amqp.exceptions import *
import json
from jrunner.common import BROKER_EXCHANGE


def send_msg(msg, to, message_id=None, Q='controller'):
    pr = Producer(BROKER_EXCHANGE, myQueue=Q)
    pr.publish(msg, to, message_id)
    pr.close()
    return True


def send_msg_controller(msg, to, insist=False):
    pr = Producer(BROKER_EXCHANGE)
    if pr.is_alive() is False:
        if pr.recreate(insist=insist) is False:
            raise BrokerConnectFailed('Failed to connect to RabbitMQ server')
    pr.publish(json.dumps(msg), to, None)
    pr.close()
    return True
