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
from jrunner.common.amqpclient.client import *

from redis.exceptions import *
import jrunner.jobqueue.preprocesors as proc
import jrunner.auth as auth
import jrunner.common.utils as util
import jrunner.common.amqpclient.util as amqp_util
import datetime
import pickle as p
import uuid
import base64
import socket

from jrunner.openstack.common import log as logging
log = logging.getLogger(__name__)

auth_backend = auth.get_backend()
backend = auth_backend.connection

HOSTNAME = socket.getfqdn()


class TaskValidator(object):

    def __init__(self, data):
        if type(data) != dict:
            raise ValueError('Invalid task data')
        self.data = data
        self.task = {}

        for i in self.data.keys():
            meth = getattr(self, 'clean_%s' % str(i), self.stub)
            self.task[i] = meth(self.data[i])

    def clean_snapshot(self, val):
        if val is None:
            return None
        if hasattr(val, 'uuid') is False:
            raise ValueError('Invalid snapshot. Must have uuid set')
        return base64.b64encode(p.dumps(val, 2))

    def clean_body(self, val):
        if type(val) != dict:
            raise ValueError('Body must be dict')
        return val

    def stub(self, val):
        return val

    def cleaned_data(self):
        log.debug('%r' % self.task)
        return self.task


class TaskObject(object):
    red = backend.db
    required_fields = (
        'task_id',
        'queue',
        'action',
        'resource',
        'timestamp',
        'description',
        'state',
        'body',
        'result',
        'traceback',
        'error',
        'snapshot',
        'grp_id',
        'prio',)

    def __init__(self, task, pipe=None):
        self.lock_name = None
        # pipe poate fi pasat pentru comenzi buffered. Mare atentie insa,
        # daca folositi parametrul pipe, va trebui ca la final sa rulati
        # si pipe.execute()
        if pipe is not None:
            if isinstance(pipe, redis.client.StrictPipeline) is False:
                raise Exception(
                    'pipe must be of type redis.client.StrictPipeline')
            self.red = pipe

        self.task = task
        self.name = 'backend:tasks:%s' % str(self.task['task_id'])
        for i in self.required_fields:
            if i not in self.task:
                raise ValueError(
                    'Invalid task. Required field %s not found' % str(i))
        if self.lock is True and self.task['snapshot'] is not None:
            try:
                self.lock_name = 'backend:lock:%s' % str(self.snapshot.uuid)
            except:
                self.lock_name = None

    def __getattr__(self, name):
        if 'task' not in self.__dict__:
            raise AttributeError()
        if name == 'snapshot':
            if self.task['snapshot'] is None:
                return None
            try:
                snapshot = p.loads(base64.b64decode(self.task['snapshot']))
                object.__setattr__(self, 'snapshot', snapshot)
                return snapshot
            except Exception as err:
                raise ValueError('Invalid snapshot: %s' % str(err))

        if name not in self.task:
            raise AttributeError()
        return self.task[name]

    def set_state(self, state, error=None, strace=None):
        self.state = str(state)
        self.error = error
        self.traceback = strace
        self.save()

    def __setattr__(self, name, value):
        if 'name' not in self.__dict__:
            return dict.__setattr__(self, name, value)
        if name in self.task:
            if name == 'snapshot':
                self.task['snapshot'] = p.dumps(value, 2)
            else:
                self.task[name] = value
        else:
            if name == 'snapshot':
                self.task['snapshot'] = p.dumps(value, 2)
            if name in ('name', 'task_id'):
                raise ValueError('This attribute cannot be changed')
            object.__setattr__(self, name, value)

    @classmethod
    def create(cls, action, resource, body, grp_id,
               description=None, queue=None, snapshot=None, lock=True, prio=1):
        tbody = {
            'action': action,
            'resource': resource,
            'body': body,
            'grp_id': grp_id,
            'description': description,
            'queue': queue,
            'snapshot': snapshot,
            'task_id': uuid.uuid4().hex,
            'timestamp': int(datetime.datetime.now().strftime('%s')),
            'state': 'not_started',
            'result': None,
            'traceback': None,
            'error': None,
            'lock': lock,
            'prio': prio,
        }
        #clean task
        validate = TaskValidator(tbody)
        tbody = validate.cleaned_data()
        name = 'backend:tasks:%s' % str(tbody['task_id'])

        # locking
        if snapshot is not None:
            try:
                lock_name = 'backend:lock:%s' % str(snapshot.uuid)
            except:
                # No locking can be done without a uuid
                lock = False
        # add lock
        if lock is True:
            cls.red.sadd(lock_name, tbody['task_id'])
            tbody['lock'] = True

        # create task in redis
        cls.red.set(name, json.dumps(tbody))
        cls.red.sadd('backend:index', tbody['task_id'])
        return cls(tbody)

    @classmethod
    def get(cls, task_id, pipe=None):
        """
            Instantiem clasa TaskObject folosind obiectul returnat de redis
            via task_id
        """
        name = 'backend:tasks:%s' % str(task_id)
        if pipe is None:
            task = cls.red.get(name)
        else:
            if isinstance(pipe, redis.client.StrictPipeline) is False:
                raise Exception(
                    'pipe must be of type redis.client.StrictPipeline')
            task = pipe.get(name)

        if task is None:
            raise ValueError('No such task')

        try:
            body = json.loads(task)
        except Exception as err:
            log.exception(err)
            raise Exception('Invalid task body')
        return cls(body)

    def delete(self):
        """
            Stergem task-ul din redis. Un save() il va readauga :)
        """
        self.red.delete(self.name)

        if self.lock_name is not None:
            self.red.srem(self.lock_name, self.task['task_id'])
        self.red.srem('backend:index', self.task['task_id'])
        return True

    def save(self):
        """
            salveaza in redis self.task
        """
        self.red.set(self.name, json.dumps(self.task))
        if self.lock_name is not None and self.task['lock'] is True:
            self.red.sadd(self.lock_name, self.task['task_id'])
        self.red.sadd('backend:index', self.task['task_id'])
        return self


class BaseOperation(object):
    red = redis.StrictRedis(connection_pool=backend.redis_pool)

    def __init__(self, task=None):
        self.task = task
        if task is None:
            # counter pentru prioritatea task-urilor
            self.counter = "backend:group:counter:%s" % str(uuid.uuid4().hex)
            self.red.set(self.counter, 1)
            self.red.expire(self.counter, 30)
            # numele grupului. Va fi un ordered set, deci odata ce
            # toate elementele sunt scoase, va fi sters automat.
            self.grp_id = str(uuid.uuid4().hex)
            self.group_name = 'backend:group:%s' % self.grp_id
            self.group_name_finished = 'backend:group:%s:finished' % \
                self.grp_id
        else:
            if isinstance(task, TaskObject) is False:
                raise ValueError('Invalid task object')
            self.counter = None
            self.grp_id = self.task.grp_id
            self.group_name = 'backend:group:%s' % str(self.grp_id)
            self.group_name_finished = 'backend:group:%s:finished' % \
                str(self.grp_id)

    @classmethod
    def get(cls, task_id):
        task = TaskObject.get(task_id)
        return cls(task=task)

    def group(self):
        pending = self.red.zrange(self.group_name, 0, -1)
        finished = self.red.zrange(self.group_name_finished, 0, -1)
        return [pending, finished, ]

    def set_state(self, state):
        pass

    def confirm_task(self, push=False):
        self.task.set_state('finished')
        self.red.zrem(self.group_name, self.task.task_id)
        self.red.zadd(
            self.group_name_finished,
            self.task.prio,
            self.task.task_id)

        if self.red.exists(self.group_name) is False:
            # we were the last task
            self.purge()
            return True
        if push is True:
            self.push()
        return True

    def task_group_by_prio(self, prio, pipe=None):
        if pipe is not None:
            if isinstance(pipe, redis.client.StrictPipeline) is False:
                raise Exception(
                    'pipe must be of type redis.client.StrictPipeline')
            grp = pipe.zrangebyscore(self.group_name, prio, prio)
        else:
            grp = self.red.zrangebyscore(self.group_name, prio, prio)
        ret = {'names': [], 'objects': [], 'ids': []}
        for i in grp:
            t = TaskObject.get(i)
            ret['names'].append(t.name)
            ret['objects'].append(t)
            ret['ids'].append(t.task_id)
        return ret

    def push(self, insist=True):
        task_id = self.red.zrange(self.group_name, 0, -1)
        if len(task_id) == 0:
            return True
        task = TaskObject.get(task_id[0])
        if task.state == 'finished' or task.state == 'started':
            return True
        to_be_pushed = []
        # Get initial names
        t_grp = self.task_group_by_prio(task.prio)
        with self.red.pipeline() as pipe:
            try:
                pipe.watch(t_grp['names'])
                for i in t_grp['objects']:
                    t = TaskObject.get(i.task_id, pipe=pipe)
                    if t.state != 'started' and t.state != 'finished':
                        to_be_pushed.append(t)
                pipe.multi()
                for i in to_be_pushed:
                    # marcam taskurile ca fiind started
                    i.state = 'started'
                    i.save()
                pipe.execute()
            except WatchError:
                # altcineva a confirmat unul din task-urile
                # ce urmau a fi pornite
                return True
        # Urmatoarele task-uri au fost marcate ca fiind started.
        for i in t_grp['ids']:
            t = TaskObject.get(i)
            t = proc.process(t)
            try:
                log.debug("Determining queue to send task %s to" % t.task_id)
                if t.queue is None:
                    log.debug("Sending task %s to controller" % t.task_id)
                    q = HOSTNAME
                else:
                    log.debug(
                        "Sending task %s to queue %s" %
                        (t.task_id, t.queue)
                    )
                    q = t.queue
                amqp_util.send_msg(t.body, q, t.task_id)
            except Exception as err:
                log.exception(err)
                strace = util.stack_as_string()
                t.set_state("error", error=str(err), strace=strace)
                raise Exception(strace)
        return True

    def create(self, **kw):
        if self.counter is None:
            raise Exception(
                'You may not add new tasks to existing group')
        prio = kw.get('prio', None)
        if prio is None:
            prio = self.red.incr(self.counter)
        kw['grp_id'] = self.grp_id
        kw['prio'] = prio
        log.debug("sending parameters to TaskObject: %r" % kw)
        t = TaskObject.create(**kw)
        self.red.zadd(self.group_name, prio, t.task_id)
        return True

    def createGroup(self, data):
        prio = self.red.incr(self.counter)
        for i in data:
            i['prio'] = prio
            self.create(**i)
        return True

    def purge(self):
        for i in self.red.zrange(self.group_name, 0, -1):
            try:
                t = TaskObject.get(i)
                t.delete()
            except Exception as err:
                log.exception(err)
                pass
        for i in self.red.zrange(self.group_name_finished, 0, -1):
            try:
                t = TaskObject.get(i)
                t.delete()
            except Exception as err:
                log.exception(err)
                pass
        self.red.delete(self.group_name)
        self.red.delete(self.group_name_finished)
        self.red.delete(self.counter)
        return True
