from oslo.config import cfg
from jrunner.openstack.common import log as logging
import jrunner.auth as auth
import jrunner.common.db.jobs as j
import jrunner.common.Operations as op
import json

backend = auth.get_backend()
User = backend.User
opts = [
    cfg.StrOpt(
        'queue',
        default='worker',
        help='Job worker queue'),
]

CONF = cfg.CONF
CONF.register_opts(opts, 'jobworker')

LOG = logging.getLogger(__name__)


class ValidateJob(object):

    def __init__(self, data):
        self.required_fields = [
            "jobs",
        ]
        self.optional_fields = [
            "callback_url",
            "email"
        ]
        if type(data) is not dict:
            raise ValueError("Invalid job data: %r" % type(data))
        for i in self.required_fields:
            if i not in data:
                raise ValueError("Invalid job. Missing %s" % i)

        self.cleaned = {}
        for i in self.optional_fields:
            if i not in data:
                data[i] = None

        for i in data.keys():
            validate = getattr(self, i, self.stub)
            self.cleaned[i] = validate(data[i])

    def stub(self, value):
        return value

    def clean_callback_url(self, value):
        val = value.split(":")
        proto = ("http", "https",)
        if val[0] not in proto:
            raise ValueError("I only know %s." % ','.join([x for x in proto]))
        return value

    def clean_jobs(self, value):
        required_fields = ("job_args", "job_name")
        if type(value) is not list:
            raise ValueError("Invalid job. Got %s" % str(type(value)))
        for i in value:
            for j in required_fields:
                if j not in i:
                    raise ValueError("Invalid job.")
        return value


class JobClass(object):

    def __init__(self, user, job=None):
        self.job = job
        self.user = user
        if isinstance(self.user, User) is False:
            raise ValueError("Invalid user object")

        if self.job is not None:
            if isinstance(self.job, Jobs) is False:
                raise ValueError("Invalid job.")
            if self.job.user != user:
                raise ValueError("Not your job")

    def create(self, data):
        data = ValidateJob(data).cleaned
        job_obj = []
        for i in data['jobs']:
            a = j.Jobs.create(
                user=self.user,
                job_name=i['job_name'],
                job_args=json.dumps(i['job_args']),
                callback_url=data['callback_url'],
                email=data['email'])
            job_obj.append(a)
        bo = op.BaseOperation()

        for i in job_obj:
            params = {
                "resource": "jobs",
                "action": "create",
                "body": {
                    "job_name": i.job_name,
                    "job_args": i.job_args,
                    "job_id": i.uuid,
                }
            }
            try:
                snap = i
                snap.state = "done"
                bo.create(
                    resource='jobs',
                    action='create',
                    queue=CONF.jobworker.queue,
                    body=params,
                    snapshot=snap)
            except Exception as err:
                log.exception(err)
                bo.purge()
                raise Exception(err)
        bo.push(insist=False)
        return "Job successfully created"
