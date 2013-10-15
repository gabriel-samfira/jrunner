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
from oslo.config import cfg
import flask
import functools
from jrunner.openstack.common import log as logging
import traceback

LOG = logging.getLogger(__name__)

opts = [
    cfg.StrOpt(
        'auth_backend',
        default='jrunner.auth.db.redis',
        help='Authentication backend'),
]

CONF = cfg.CONF
CONF.register_opts(opts, 'DEFAULT')


def get_backend(backend=None):
    if backend is None:
        backend = CONF.DEFAULT.auth_backend
    try:
        return importlib.import_module(backend)
    except Exception as err:
        LOG.exception(err)
        raise Exception(
            "Failed to import authentication backend %s" % backend)


def login_required(func):
    @functools.wraps(func)
    def decorated(*args, **kw):
        default_auth = importlib.import_module('jrunner.auth.decorators.basic')
        auth = flask.request.headers.get('Authorization')
        if auth is None:
            return default_auth.failed_callback()
        a_type = str(auth.split()[0]).lower()

        try:
            mod = importlib.import_module(
                'jrunner.auth.decorators.%s' % a_type)
        except Exception as err:
            LOG.exception(err)
            return default_auth.failed_callback()
        if mod.check_login(flask.request):
            return func(*args, **kw)
        return mod.failed_callback()
    return decorated
