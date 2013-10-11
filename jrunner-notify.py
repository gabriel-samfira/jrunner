#!/usr/bin/env python

from oslo.config import cfg
import importlib
import sys
from jrunner.openstack.common import log as logging


opts = [
    cfg.StrOpt(
        'worker_module',
        default='jrunner.jobnotify.workers.simple',
        help='Worker module'),
]

CONF = cfg.CONF
CONF.register_opts(opts, 'jobnotify')

if __name__ == "__main__":
    CONF(sys.argv[1:])
    main = importlib.import_module(CONF.jobnotify.worker_module)
    main.main()
