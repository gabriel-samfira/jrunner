#!/usr/bin/env python

from oslo.config import cfg
from jrunner.openstack.common import log as logging
import sys
import rlcompleter
import readline

readline.parse_and_bind("tab: complete")

CONF = cfg.CONF
CONF(sys.argv[1:])

import jrunner.auth as auth

backend = auth.get_backend()

import code

code.interact(local=locals())
