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

import jrunner.jobqueue.callbacks.controller as cb
import datetime
import jrunner.common.amqpclient.util as amqp_util
from oslo.config import cfg

opts = [
    cfg.StrOpt(
        'queue',
        default='notify',
        help='Job notify queue'),
]

CONF = cfg.CONF
CONF.register_opts(opts, 'jobnotify')


from jrunner.openstack.common import log as logging
log = logging.getLogger(__name__)


class DoTask(cb.BaseCallback):

    def _send_notify(self):
        callback_url = getattr(self.snap, 'callback_url', None)
        email = getattr(self.snap, 'email', None)
        if callback_url is None and email is None:
            return True
        msg = {
            "resource": "notify",
            "action": "create",
            "body": {
                "callback_url": callback_url,
                "job_id": self.snap.uuid,
                "email": {
                    "address": email,
                    "title": "Job %s status" % self.snap.job_name
                },
                "body": self.message.body
            }
        }
        amqp_util.send_msg(msg, CONF.jobnotify.queue, Q=None)
        return True

    def create(self):
        log.debug("Task %s finished successfully" % str(self.snap.uuid))
        try:
            self._send_notify()
        except Exception as err:
            log.exception(err)

        self.snap.save()
        self.op.confirm_task()
        return True


def process(message):
    ret = DoTask(message)
    return ret
