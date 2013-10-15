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

from jrunner.common.amqpclient.client import Consume
from jrunner.jobqueue.dispatch import dispatch
from jrunner.common import has_gevent_enabled
from jrunner.openstack.common import log as logging
from jrunner.jobqueue.workers import *

from oslo.config import cfg

logging.setup('jrunner')

opts = [
    cfg.StrOpt(
        'queue',
        default='controller',
        help='Worker queue'),
]
CONF = cfg.CONF
CONF.register_opts(opts, 'jobqueue')

LOG = logging.getLogger(__name__)

if has_gevent_enabled():
    import gevent
    sleep = gevent.sleep
else:
    import time
    sleep = time.sleep


def main():
    while True:
        try:
            c = Consume(BROKER_EXCHANGE, CONF.jobqueue.queue)
            c.consume(dispatch)
        except Exception as err:
            LOG.exception(err)
        finally:
            sleep(3)
