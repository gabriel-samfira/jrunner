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

from jrunner.common.utils import stack_as_string
import os
import jrunner.common.utils as util
from jrunner.common.utils import smtp
from oslo.config import cfg
from jrunner.openstack.common import log as logging
import requests

opts = [
    cfg.StrOpt(
        'job_dir',
        default='/',
        help='Scripts location'),
]

CONF = cfg.CONF
CONF.register_opts(opts, 'jobnotify')

log = logging.getLogger(__name__)


class DoTask():
    # Must return a tuple in the form of (result,state,error,strace)
    def __init__(self, message):
        self.message = message
        if type(message) is not dict:
            raise ValueError('Message must be dictionary')

        self.handlers = {
            'create': self.create,
        }
        self.result = None
        self.state = None
        self.error = None
        self.strace = None

    def _execute_callbacks(self, msg):
        print ">>>>>>>>>>>>>>>>", smtp
        try:
            callback_url = msg.get('callback_url')
            email = msg.get('email')
        except:
            return True
        if callback_url:
            try:
                ret = requests.post(callback_url, data=msg['body'])
                if ret.status_code != 200:
                    log.error(
                        "Callback URL %s returned error code %r" %
                        (callback_url, ret.status_code)
                    )
                else:
                    log.info("Callback URL %s returned success" % callback_url)
            except Exception as err:
                log.exception(err)
        if email:
            try:
                smtp.send_email(
                    email['address'],
                    "%s" % email['title'],
                    "%r" % msg['body'],
                    fail_silently=False
                )
                log.info("Successfully sent email to %s" % email)
            except Exception as err:
                log.exception(err)
        return True

    def create(self, msg):
        try:
            log.info("Got msg %r" % msg)
            self._execute_callbacks(msg)
            self.state = 'finished'
        except Exception as err:
            log.exception(err)
            self.error = str(err)
            self.state = 'error'
            self.strace = stack_as_string()
        return (self.result, self.state, self.error, self.strace)

    def run(self):
        try:
            action = str(self.message['action'])
            body = self.message['body']
        except Exception as err:
            self.error = 'Got invalid message. Error was: %s' % str(err)
            self.state = 'error'
            self.strace = stack_as_string()
            return (self.result, self.state, self.error, self.strace)
        return self.handlers[action](body)


def process(message):
    task = DoTask(message)
    ret = task.run()
    return ret
