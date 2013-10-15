#!/usr/bin/env python

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

from oslo.config import cfg
from jrunner.openstack.common import log as logging
import sys

opts = [
    cfg.IntOpt('http_port', default=8080, help='Http listen port'),
    cfg.StrOpt('http_host', default='0.0.0.0', help='Http listen host'),
]

CONF = cfg.CONF
CONF.register_opts(opts, 'web')
CONF(sys.argv[1:])
logging.setup('jrunner')

import jrunner.auth as auth
import jrunner.auth.decorators.rest as rest
import flask
import jrunner.jobpublisher.jobs as j
import jrunner.common.Operations

LOG = logging.getLogger(__name__)
app = flask.Flask(__name__)


@app.route('/', methods=['POST', ])
@rest.serialize
@auth.login_required
def jobs():
    req = flask.request
    data = req.data
    obj = j.JobClass(req.user)
    return {"detail": obj.create(data)}


def main():
    app.run(host=CONF.web.http_host,
            port=CONF.web.http_port,
            debug=True)

if __name__ == '__main__':
    main()
