#!/usr/bin/env python

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
