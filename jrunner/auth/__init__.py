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
