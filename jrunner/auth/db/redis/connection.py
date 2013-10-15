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

import redis
from oslo.config import cfg
from jrunner.openstack.common import log as logging

opts = [
    cfg.IntOpt('port', default=6379, help='redis port'),
    cfg.IntOpt('db', default=0, help='redis database'),
    cfg.StrOpt('host', default='0.0.0.0', help='redis host'),
    cfg.StrOpt('passwd', default=None, help='redis passwd'),
]

CONF = cfg.CONF
CONF.register_opts(opts, 'redis')

LOG = logging.getLogger(__name__)

_HOST_ = CONF.redis.host
_PORT_ = CONF.redis.port
_DB_ = CONF.redis.db
_PASSWD_ = CONF.redis.passwd

redis_pool = redis.ConnectionPool(
    host=_HOST_,
    port=_PORT_,
    db=_DB_,
    password=_PASSWD_)

db = redis.StrictRedis(connection_pool=redis_pool)
