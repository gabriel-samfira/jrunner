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
