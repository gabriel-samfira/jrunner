from jrunner.common.amqpclient.client import Consume
from jrunner.jobnotify.dispatch import dispatch
from jrunner.common import has_gevent_enabled
from jrunner.openstack.common import log as logging
from jrunner.jobnotify.workers import *

from oslo.config import cfg

logging.setup('jrunner')

opts = [
    cfg.StrOpt(
        'queue',
        default='worker',
        help='Worker queue'),
]
CONF = cfg.CONF
CONF.register_opts(opts, 'jobnotify')

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
            c = Consume(BROKER_EXCHANGE, CONF.jobnotify.queue)
            c.consume(dispatch)
        except Exception as err:
            LOG.exception(err)
        finally:
            sleep(3)
