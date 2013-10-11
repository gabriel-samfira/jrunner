import importlib
from jrunner.common import *
from oslo.config import cfg

opts = [
    cfg.StrOpt(
        'worker_module',
        default='jrunner.jobqueue.workers.simple',
        help='Worker module'),
]

CONF = cfg.CONF
CONF.register_opts(opts, 'jobqueue')


def get_worker_module():
    try:
        return importlib.import_module(CONF.jobqueue.worker_module)
    except Exception as err:
        LOG.exception(err)
    raise Exception("Failed to import worker module")
