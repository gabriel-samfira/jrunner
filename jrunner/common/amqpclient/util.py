# Copyright 2013 Cloudbase Solutions Srl
# All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

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
