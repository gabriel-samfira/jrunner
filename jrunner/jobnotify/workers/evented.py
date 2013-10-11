import sys

try:
    from gevent import monkey
    monkey.patch_all()
    import gevent
except ImportError:
    sys.stderr.write("gevent 1.0 required for this backend\n")
    sys.exit(1)

from jrunner.common.amqpclient.client import Consume
from jrunner.jobnotify.dispatch import dispatch
from jrunner.common import has_gevent_enabled, BROKER_EXCHANGE
from jrunner.openstack.common import log as logging
from jrunner.jobnotify.workers import *
from oslo.config import cfg
import sys
import signal

from gevent.queue import JoinableQueue as Queue

logging.setup('jrunner')

opts = [
    cfg.StrOpt(
        'queue',
        default='notify',
        help='Worker queue'),
    cfg.IntOpt(
        'gevent_workers',
        default=1,
        help='Worker queue'),
]
CONF = cfg.CONF
CONF.register_opts(opts, 'jobnotify')
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


def spawn_workers(max_wrk=CONF.jobnotify.gevent_workers):
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
            c = Consume(BROKER_EXCHANGE, CONF.jobnotify.queue)
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
