import flask
import jrunner.auth as auth
from jrunner.openstack.common import log as logging

LOG = logging.getLogger(__name__)
backend = auth.get_backend()


def failed_callback():
    return flask.Response(
        'Valid login credentials required', 401,
        {'WWW-Authenticate': 'Basic realm="Login Required"'})


def check_login(request):
    auth = request.authorization
    if not auth:
        return False

    user = auth.username
    passwd = auth.password
    try:
        userObj = backend.User.get(user)
    except Exception as err:
        LOG.exception(err)
        return False
    if userObj.authenticate(passwd) is False:
        return False
    flask.request.user = userObj
    return True
