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

import json
import functools
import flask

try:
    import yaml
except:
    yaml = False

deserializer = {
    'yaml': yaml.safe_load if yaml else json.loads,
    'json': json.loads
}

serializer = {
    'yaml': yaml.dump if yaml else json.dumps,
    'json': json.dumps
}


def serialize(func):
    @functools.wraps(func)
    def decorated(*args, **kw):
        content_type = flask.request.headers.get('Content-type')
        if content_type is None or len(content_type) == 0:
            ser = 'json'
        else:
            ser = content_type.split('/')[-1]
        if ser not in ('yaml', 'json'):
            return flask.Response('Invalid content_type', 400)
        if flask.request.method.upper() in ('POST', 'PUT'):
            try:
                loaded = deserializer[ser](flask.request.data)
            except Exception as err:
                return flask.Response('Invalid post data', 400)
            flask.request.data = loaded

        ret = func(*args, **kw)
        if type(ret) in (list, dict, tuple, str, int):
            data = serializer[ser](ret)
            return flask.Response(
                data,
                200,
                {'Content-type': 'application/%s' % ser}
            )
        return ret
    return decorated
