import traceback
from random import choice
import string
import StringIO
import os
import hashlib
from jrunner.common import has_gevent_enabled

from jrunner.openstack.common import log as logging
log = logging.getLogger(__name__)

if has_gevent_enabled():
    from gevent.subprocess import Popen, PIPE
else:
    from subprocess import Popen, PIPE


def execute_cmd(cmd, stdin=None, stdout=None, stderr=None):
    p = Popen(
        cmd, bufsize=-1, stdout=stdout, stderr=stderr, stdin=stdin).wait()
    return p


def execute_cmd_with_output(cmd, stdin=None):
    log.debug("Running command: %r" % cmd)
    p = Popen(cmd, bufsize=-1, stdout=PIPE, stderr=PIPE, stdin=stdin)
    (msgs, errs) = p.communicate()
    if p.returncode != 0:
        raise Exception('Failed to run command')
    return (msgs, errs)


def fbuffer(f, chunk_size=8388608):
    while True:
        chunk = f.read(chunk_size)
        if not chunk:
            break
        yield chunk


def file_md5(_file):
    md5 = hashlib.md5()
    for i in fbuffer(_file, chunk_size=128):
        md5.update(i)
    return md5.hexdigest()


def stack_as_string():
    return traceback.format_exc()


def GenRand(r=32):
    chars = string.letters + string.digits
    randStr = ""
    for i in range(r):
        randStr = randStr + choice(chars)
    return randStr
