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

import importlib
import pickle as p


def process(task):
    """
        Unele task-uri au nevoie de procesare inante de a fi trimise catre MQ
        Procesatorul va adauga informatiile lipsa inainte de a face push.
    """
    procesor = None
    try:
        procesor = importlib.import_module(
            'jrunner.jobqueue.preprocesors.%s' % str(task.resource))
    except Exception as err:
        pass

    if procesor is None:
        return task

    return procesor.process(task)
