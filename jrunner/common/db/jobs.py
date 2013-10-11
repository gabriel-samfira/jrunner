import jrunner.auth as auth
import json
import uuid
from jrunner.openstack.common import log as logging

LOG = logging.getLogger(__name__)
backend = auth.get_backend()

User = backend.User


class Jobs(object):

    job_data = {
        "uuid": None,
        "user": None,
        "job_name": None,
        "job_args": None,
        "callback_url": None,
        "email": None,
        "state": None
    }

    job_counter = "jrunner:jobs:counter"
    job_index = "jrunner:jobs:index"

    user_job_counter = 'jrunner:user:%s:jobs:count'
    user_jobs = "jrunner:user:%s:jobs"

    def __init__(self, user, job):
        self.user = user
        if isinstance(user, backend.User) is False:
            raise ValueError("Invalid user object")

        self.job_data = {
            "uuid": None,
            "user": None,
            "job_name": None,
            "job_args": None,
            "callback_url": None,
            "email": None,
            "state": None
        }
        self.j_uuid = job
        self.user_job_counter = self.user_job_counter % self.user.user
        self.user_jobs = self.user_jobs % self.user.user

        self.job_id = "jrunner:user:%s:job:%s" % (self.user.user, self.j_uuid)
        self.jobObj = backend.db.get(self.job_id)
        if self.jobObj is None:
            raise ValueError("No such job")
        self.jobObj = json.loads(self.jobObj)

        if backend.db.get(self.job_counter) is None:
            backend.db.set(job_counter, 0)
        if backend.db.get(self.user_job_counter) is None:
            backend.db.set(self.user_job_counter, 0)

    def __getattr__(self, name):
        if 'jobObj' not in self.__dict__:
            raise AttributeError()
        if name not in self.jobObj:
            raise AttributeError()
        return self.jobObj[name]

    def __setattr__(self, name, value):
        if 'jobObj' not in self.__dict__:
            return dict.__setattr__(self, name, value)
        if name in self.jobObj:
            self.jobObj[name] = value
        elif name in ('uuid',):
            raise ValueError("Readonly property: %s" % value)
        else:
            object.__setattr__(self, name, value)

    @classmethod
    def create(cls, *args, **kw):
        required = (
            'user', 'job_name', 'job_args',
            'callback_url', 'email'
        )
        for i in required:
            if i not in kw:
                raise ValueError("Missing required field: %s" % str(i))
        # remove bogus kwargs
        for i in kw.keys():
            if i not in required:
                del kw[i]
        if isinstance(kw['user'], User) is False:
            raise ValueError("Invalid user object")
        user = kw['user']
        kw['user'] = user.user
        kw['uuid'] = uuid.uuid4().hex
        kw['state'] = 'pending'
        cls.job_data.update(kw)
        _id = "jrunner:user:%s:job:%s" % (kw['user'], kw['uuid'])
        user_jobs = cls.user_jobs % kw['user']
        user_job_counter = cls.user_job_counter % kw['user']
        backend.db.zadd(
            user_jobs,
            backend.db.incr(user_job_counter),
            kw['uuid'])
        backend.db.set(
            _id,
            json.dumps(cls.job_data)
        )
        backend.db.zadd(
            cls.job_index,
            backend.db.incr(cls.job_counter),
            kw['uuid'])
        return cls(user, kw['uuid'])

    def save(self):
        backend.db.set(self.job_id, json.dumps(self.jobObj))
        return True

    def delete(self):
        backend.db.zrem(
            self.user_jobs,
            self.uuid)
        backend.db.delete(
            self.job_id,
        )
        backend.db.zrem(
            self.job_index,
            self.uuid)
        return True

    @property
    def is_idle(self):
        if not self.id:
            return None
        return backend.db.exists('backend:lock:%s' % self.uuid) is False

    def lock(self):
        if not self.id:
            return None
        return backend.db.smembers('backend:lock:%s' % self.uuid)
