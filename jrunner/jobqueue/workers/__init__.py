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
