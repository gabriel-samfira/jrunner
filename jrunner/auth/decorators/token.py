import flask
import jrunner.auth as auth
from jrunner.openstack.common import log as logging

LOG = logging.getLogger(__name__)
backend = auth.get_backend()


def failed_callback():
    return flask.Response(
        'Could not verify your access level for that URL.\n'
        'You have to login with proper credentials', 401,
        {})


def check_login(request):
    auth = flask.request.headers.get('Authorization')

    if auth is None:
        return False

    token = auth.split()
    if len(token) != 2:
        return False

    try:
        userObj = backend.Token.authenticate(token[1])
    except Exception as err:
        LOG.exception(err)
        return False
    flask.request.user = userObj
    return True
