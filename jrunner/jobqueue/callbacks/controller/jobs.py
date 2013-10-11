import jrunner.jobqueue.callbacks.controller as cb
import datetime
import jrunner.common.amqpclient.util as amqp_util
from oslo.config import cfg

opts = [
    cfg.StrOpt(
        'queue',
        default='notify',
        help='Job notify queue'),
]

CONF = cfg.CONF
CONF.register_opts(opts, 'jobnotify')


from jrunner.openstack.common import log as logging
log = logging.getLogger(__name__)


class DoTask(cb.BaseCallback):

    def _send_notify(self):
        callback_url = getattr(self.snap, 'callback_url', None)
        email = getattr(self.snap, 'email', None)
        if callback_url is None and email is None:
            return True
        msg = {
            "resource": "notify",
            "action": "create",
            "body": {
                "callback_url": callback_url,
                "job_id": self.snap.uuid,
                "email": {
                    "address": email,
                    "title": "Job %s status" % self.snap.job_name
                },
                "body": self.message.body
            }
        }
        amqp_util.send_msg(msg, CONF.jobnotify.queue, Q=None)
        return True

    def create(self):
        log.debug("Task %s finished successfully" % str(self.snap.uuid))
        try:
            self._send_notify()
        except Exception as err:
            log.exception(err)

        self.snap.save()
        self.op.confirm_task()
        return True


def process(message):
    ret = DoTask(message)
    return ret
