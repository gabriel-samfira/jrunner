import json
import importlib
import jrunner.common.Operations as operations
import amqp

from jrunner.openstack.common import log as logging
log = logging.getLogger(__name__)


def dispatch(message):
    log.debug(
        "Got message: %s with headers: %s" %
        (str(message.body), str(message.properties)))
    # op = None
    # snap = None
    module = None
    if isinstance(message, amqp.Message) is False:
        log.error("Invalid message received %s" % type(message))
        close_connection()
        raise ValueError("Invalid message received %s" % type(message))

    # tasks sent by nodes
    if message.properties.get('message_id') is None:
        msg_body = json.loads(message.body)
        res = msg_body['resource']
        module = 'jrunner.jobqueue.callbacks.nodes.%s' % str(res)
    else:
        # normal tasks
        t = operations.TaskObject.get(message.message_id)
        if t.resource is None:
            raise ValueError('Invalid task: %s' % str(t.id))
        module = 'jrunner.jobqueue.callbacks.controller.%s' % str(t.resource)

    try:
        mod = importlib.import_module(module)
    except Exception as err:
        # do something significant
        raise Exception("Could not get callback for task: %s" % str(err))

    try:
        ret = mod.process(message)
        if getattr(ret, 'op', None) is not None:
            if ret.op.task.state == 'finished':
                ret.op.push()
    except Exception as err:
        log.exception(err)
    return ret
