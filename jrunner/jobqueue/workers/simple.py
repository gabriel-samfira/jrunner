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
