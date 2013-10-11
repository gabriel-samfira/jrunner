import json
import jrunner.common.Operations as op
import requests
from jrunner.common.utils import smtp


import logging
log = logging.getLogger(__name__)
send_mail = smtp.send_email


class BaseCallback(object):

    def __init__(self, message):
        self.message_id = message.message_id
        self.message = message
        self.message_body = json.loads(self.message.body)
        self.op = op.BaseOperation.get(self.message_id)
        self.action = self.op.task.action
        self.snap = self.op.task.snapshot
        self.has_err = self.process_error()

        if self.has_err is False:
            log.debug("Processing %s" % str(self.message_id))
            action = getattr(self, str(self.action))
            action()
        else:
            log.error("ERROR: %s" % str(self.has_err))

    def execute_callbacks(self):
        try:
            callback_url = self.snap.callback_url
            email = self.snap.email
        except:
            return True
        if callback_url:
            try:
                ret = requests.post(callback_url, data=self.message.body)
                if ret.status_code != 200:
                    log.error(
                        "Callback URL %s returned error code %r" %
                        (callback_url, ret.status_code)
                    )
                else:
                    log.info("Callback URL %s returned success" % callback_url)
            except Exception as err:
                log.exception(err)
        if email:
            try:
                send_mail(
                    email,
                    "Job %s status" % self.snap.job_name,
                    "%r" % self.message.body,
                    fail_silently=False
                )
                log.info("Successfully sent email to %s" % email)
            except Exception as err:
                log.exception(err)
        return True

    def process_error(self):
        b = self.message_body
        if len(b) > 0:
            if b['error'] is not None:
                self.op.task.state = b['state']
                self.op.task.result = b['result']
                self.op.task.error = b['error']
                self.op.task.traceback = b['traceback']
                self.op.task.save()
                self.op.set_state('error')
                log.error(
                    "Task %s returned an error: %s" %
                    (str(self.message_id), str(b['error']))
                )
                if getattr(self.snap, 'state'):
                    self.snap.state = b['state']
                    self.snap.save()
                try:
                    self.execute_callbacks()
                except Exception as err:
                    log.exception(err)
                return True
        return False
