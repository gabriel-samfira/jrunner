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

import sys

try:
    from gevent import monkey
    monkey.patch_all()
    import gevent
except ImportError:
    sys.stderr.write("gevent 1.0 required for this backend\n")
    sys.exit(1)

from jrunner.common.amqpclient.client import Consume
from jrunner.jobworker.dispatch import dispatch
from jrunner.common import has_gevent_enabled, BROKER_EXCHANGE
from jrunner.openstack.common import log as logging
from jrunner.jobworker.workers import *
from oslo.config import cfg
import sys
import signal

from gevent.queue import JoinableQueue as Queue

logging.setup('jrunner')

opts = [
    cfg.StrOpt(
        'queue',
        default='controller',
        help='Worker queue'),
    cfg.IntOpt(
        'gevent_workers',
        default=1,
        help='Worker queue'),
]
CONF = cfg.CONF
CONF.register_opts(opts, 'jobworker')
log = logging.getLogger(__name__)
Q = Queue(maxsize=20)


def sigHan():
    sys.exit(0)


def worker_function(wrk):
    while True:
        try:
            task = Q.get()
        except Exception as err:
            log.exception(err)
        log.info("Worker %s: got new task." % (str(wrk)))
        try:
            dispatch(task)
        except Exception as err:
            log.exception(err)
    return True


def spawn_workers(max_wrk=CONF.jobworker.gevent_workers):
    for i in xrange(0, max_wrk):
        log.info("Spawning worker %r" % i)
        gevent.spawn(worker_function, i)
    return True


def dispatch_to_workers(msg):
    Q.put(msg)
    return True


def foreman():
    while True:
        try:
            log.debug("Starting AMQP consume")
            c = Consume(BROKER_EXCHANGE, CONF.jobworker.queue)
            c.consume(dispatch_to_workers)
        except Exception as err:
            log.exception(err)
        finally:
            sleep(3)


def main():
    gevent.signal(signal.SIGINT, sigHan)
    gevent.signal(signal.SIGTERM, sigHan)
    gevent.signal(signal.SIGQUIT, sigHan)
    gevent.joinall([gevent.spawn(foreman), gevent.spawn(spawn_workers)])
