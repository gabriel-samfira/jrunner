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

import amqp
import time
import json
import pickle
from oslo.config import cfg
from amqp.exceptions import *
from jrunner.common import Queue
from jrunner.openstack.common import log as logging
from jrunner.common import *
import socket

log = logging.getLogger(__name__)
HOSTNAME = socket.getfqdn()


class LocalStore(object):
    def __init__(self, msg):
        if isinstance(msg, amqp.Message) is False:
            raise ValueError('Invalid message received')
        self.discard = False
        self.task_id = msg.properties.get('message_id', None)
        if self.task_id is None:
            raise NameError('Invalid message. No message_id')
        self.msg = None
        self.init_msg(msg)

    def init_msg(self, msg):
        self.body = pickle.dumps(msg.body)
        self.prop = pickle.dumps(msg.properties)
        tmp = Messages.objects.filter(task_id=self.task_id)
        if tmp.count() > 0:
            self.discard = True
            return True
        self.msg = Messages.objects.create(
            task_id=self.task_id,
            reply_sent=False,
            body=self.body,
            properties=self.prop)
        return True

    def delete(self):
        if self.msg is not None:
            self.msg.delete()
        return True


class Connection(object):

    def __init__(self,
                 host=BROKER_HOST,
                 userid=BROKER_USER,
                 password=BROKER_PASSWD,
                 virtual_host=BROKER_VHOST,
                 insist=False,
                 ssl=BROKER_SSL_OPTS):
        self.host = host
        self.user = userid
        self.passwd = password
        self.vhost = virtual_host
        self.insist = insist
        self.ssl = ssl

        self.is_connected = False
        self.log = log
        self.stamp = time.time()
        self.connect()

    def connect(self):
        try:
            self.connection = amqp.Connection(
                host=self.host,
                userid=self.user,
                password=self.passwd,
                virtual_host=self.vhost,
                insist=self.insist,
                ssl=self.ssl)
            self.is_connected = True
        except Exception as err:
            self.log.error(
                "Failed to connect to RabbitMQ. Error was: %s" % str(err))
            self.is_connected = False
        return self

    def is_alive(self):
        if self.is_connected:
            try:
                ch = self.connection.channel()
                ch.close()
            except:
                self.is_connected = False
                return False
            return True
        self.is_connected = False
        return False

    def recreate(self, insist=True):
        if self.is_alive():
            return self
        count = 0
        while 1:
            if self.is_connected is False:
                self.connect()
                if self.is_connected is True:
                    self.channel = self.connection.channel()
                    break
                if insist is False:
                    if count > 0:
                        return False
                time.sleep(int(BROKER_RETRY_INTERVAL))
            else:
                break
            count = count + 1
        return self


class BaseQueue(Connection):

    def declare_exchange(self, durable=True, auto_delete=False):
        self.channel.exchange_declare(
            exchange=self.exchange_name,
            type='direct',
            durable=durable,
            auto_delete=auto_delete)
        return True

    def declare_queue(self, queue_name, routing_key, durable=True,
                      exclusive=False, auto_delete=False):

        self.queue_name = queue_name
        self.routing_key = routing_key
        self.channel.queue_declare(
            queue=self.queue_name,
            durable=durable,
            exclusive=exclusive,
            auto_delete=auto_delete)
        self.channel.queue_bind(
            queue=self.queue_name,
            exchange=self.exchange_name,
            routing_key=self.routing_key)


class Consume(BaseQueue):

    def __init__(self, exchange_name, myQueue):
        self.Q = myQueue
        self.exchange_name = exchange_name
        super(Consume, self).__init__()
        self.ext_callback = None
        self.log = log
        if self.is_alive() is False:
            if self.recreate() is False:
                raise IOError('Failed to connect to RabbitMQ server')
        self.channel = self.connection.channel()
        #declare exchange
        self.declare_exchange()
        self.declare_queue(self.Q, self.Q)

    def helper_callback(self, msg):
        if self.ext_callback is None:
            self.log.error("No callback was given")
            return False
        try:
            self.ext_callback(msg)
        except Exception as err:
            log.exception(err)
        self.channel.basic_ack(msg.delivery_tag)
        return True

    def process_unsent(self):
        """
        Process any unsent messages from local storage.
        """
        pass

    def consume(self, callback):
        # register callback
        self.ext_callback = callback
        #send unsent messagess
        self.process_unsent()
        # start consuming
        self.channel.basic_consume(
            queue=self.Q,
            callback=self.helper_callback,
            consumer_tag=HOSTNAME
        )
        notif_sent = False
        while 1:
            self.channel.wait()
        return False

    def cancel_consume(self):
        self.channel.basic_cancel(HOSTNAME)
        return True

    def process_waiting_msgs(self, callback):
        if self.is_alive() is False:
            if self.recreate() is False:
                raise IOError('Failed to connect to RabbitMQ server')
        while 1:
            # reply_sent = False
            msg = self.channel.basic_get(self.Q)
            if msg is None:
                break
            try:
                callback(msg)
                self.channel.basic_ack(msg.delivery_tag)
            except Exception as err:
                self.log.error(
                    'Callback returned error: %s' % str(err))
        return True

    def close(self):
        self.channel.close()
        self.connection.close()


class Producer(BaseQueue):

    def __init__(self, exchange_name, myQueue=None):
        self.exchange_name = exchange_name
        self.Q = myQueue
        super(Producer, self).__init__()
        #create channel
        if self.is_alive() is False:
            if self.recreate() is False:
                raise IOError('Failed to connect to RabbitMQ server')
        self.channel = self.connection.channel()
        #declare exchange
        self.declare_exchange()

    def check_message(self, msg):
        if type(msg) is str:
            try:
                json.loads(msg)
            except Exception as err:
                log.exception(err)
                raise ValueError("Message must be json")
            return msg
        else:
            return json.dumps(msg)

    def generate_headers(self):
        hostname = HOSTNAME
        tstamp = int(time.time())
        return {'hostname': hostname, 'time': tstamp}

    def publish(self, message, routing_key,
                message_id=None, extra_headers=None):
        #check message
        m = self.check_message(message)
        #declare remote queue
        self.declare_queue(routing_key, routing_key)
        #declare return queue. This queue will be used to receive responses
        if self.Q is not None:
            self.declare_queue(self.Q, self.Q)

        #create amqp message
        headers = self.generate_headers()
        if extra_headers is not None:
            if type(extra_headers) is dict:
                headers.update(extra_headers)

        msg = amqp.Message(m, application_headers=headers)
        msg.properties["content_type"] = "application/json"
        msg.properties["delivery_mode"] = 2
        if message_id:
            msg.properties['message_id'] = message_id

        if self.Q is not None:
            #add reply_to field
            msg.properties['reply_to'] = self.Q

        self.channel.basic_publish(
            exchange=self.exchange_name,
            routing_key=routing_key,
            msg=msg
        )
        return True

    def close(self):
        self.channel.close()
        self.connection.close()
