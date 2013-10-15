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

import importlib
import json
from jrunner.common import BROKER_EXCHANGE
import jrunner.common.amqpclient.client as client
from jrunner.common.utils import stack_as_string

from jrunner.openstack.common import log as logging
log = logging.getLogger(__name__)


def send_reply(reply, msg):
    pr = client.Producer(BROKER_EXCHANGE)
    if pr.is_alive() is False:
        pr.recreate()

    reply_to = msg.properties.get('reply_to', None)
    if reply_to is None:
        return True

    message_id = msg.properties.get('message_id', None)
    try:
        pr.publish(reply, reply_to, message_id)
    except Exception as err:
        log.error("Failed to send reply. Error was: %s\n" % str(err))
    finally:
        pr.close()
    return True


def build_response(result, state, error=None, strace=None):
    ret = {
        'error': error,
        'state': state,
        'traceback': strace,
        'result': result
    }
    return json.dumps(ret, indent=2)


def dispatch(message):
    # Must return a tuple in the form of (result,state,error,strace)
    try:
        msg_body = json.loads(message.body)
    except Exception as err:
        log.exception(err)
        strace = stack_as_string()
        return (
            None,
            'error',
            'Callback got invalid message: %s' % str(err),
            '%s' % strace)

    log.debug("Got message. Processing: %s" % msg_body)
    resource = msg_body['resource']

    try:
        mod = importlib.import_module(
            'jrunner.jobworker.callbacks.%s' % str(resource))
    except Exception as err:
        log.exception(err)
        strace = stack_as_string()
        return (
            None,
            'error',
            "Failed to import callback %s: %s" % (str(resource), str(err)),
            "%s" % strace)

    try:
        ret = mod.process(msg_body)
    except Exception as err:
        log.exception(err)
        strace = stack_as_string()
        ret = (
            None,
            'error',
            "Failed to process message. Error was: %s" % str(err),
            "%s" % strace)
    # Send reply here
    rsp = build_response(*ret)
    send_reply(rsp, message)
    return True
