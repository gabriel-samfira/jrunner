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

from jrunner.common.utils import stack_as_string
import os
import jrunner.common.utils as util
from oslo.config import cfg
from jrunner.openstack.common import log as logging
import json

opts = [
    cfg.StrOpt(
        'job_dir',
        default='/',
        help='Scripts location'),
]

CONF = cfg.CONF
CONF.register_opts(opts, 'jobworker')

log = logging.getLogger(__name__)


class DoTask():
    # Must return a tuple in the form of (result,state,error,strace)
    def __init__(self, message):
        self.message = message
        if type(message) is not dict:
            raise ValueError('Message must be dictionary')

        self.handlers = {
            'create': self.create,
        }
        self.result = None
        self.state = None
        self.error = None
        self.strace = None

    def _get_jobs(self):
        jobs = {}
        for i in os.listdir(CONF.jobworker.job_dir):
            a = i.split('.')
            new_name = '.'.join(a[:-1])
            jobs[new_name] = os.path.join(CONF.jobworker.job_dir, i)
            if os.access(jobs[new_name], os.X_OK) is False:
                os.chmod(jobs[new_name], 00755)
        return jobs

    def create(self, msg):
        try:
            log.info("Got msg %r" % msg)
            jobs = self._get_jobs()
            job_name = msg['job_name']
            job_args = msg['job_args']
            if job_name not in jobs:
                raise Exception("Job %s cannot be executed" % job_name)
            cmd = [jobs[job_name], ]
            job_args = json.loads(job_args)
            if type(job_args) is list:
                cmd.extend(job_args)
                if msg.get('job_id'):
                    cmd.append(" %s" % msg['job_id'])
            if type(job_args) is dict:
                if msg.get('job_id'):
                    cmd.append(" --job_id %s" % msg['job_id'])
                cmd.extend(["--%s %s" % (x, job_args[x]) for x in job_args])
                # cmd += " %s" % ' '.join(
                #     ["--%s %s" % (x, job_args[x]) for x in job_args]
                # )
            msgs, errs = util.execute_cmd_with_output(cmd)
            self.result = {
                "stdout": msgs,
                "stderr": errs,
            }
            if msg.get('job_id'):
                self.result['job_id'] = msg['job_id']
            self.state = 'finished'
        except Exception as err:
            log.exception(err)
            self.error = str(err)
            self.state = 'error'
            self.strace = stack_as_string()
        return (self.result, self.state, self.error, self.strace)

    def run(self):
        try:
            action = str(self.message['action'])
            body = self.message['body']
        except Exception as err:
            self.error = 'Got invalid message. Error was: %s' % str(err)
            self.state = 'error'
            self.strace = stack_as_string()
            return (self.result, self.state, self.error, self.strace)
        return self.handlers[action](body)


def process(message):
    task = DoTask(message)
    ret = task.run()
    return ret
