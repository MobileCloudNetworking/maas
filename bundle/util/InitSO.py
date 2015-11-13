# Copyright 2014 Technische Universitaet Berlin
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.


import json
import logging
import os

from core.SecurityGroupOrchestrator import SecurityGroupOrchestrator
from core.ServiceOrchestrator import ServiceOrchestrator
from sm.so.service_orchestrator import LOG


PATH = os.environ.get('BUNDLE_DIR', '.')


__author__ = 'gca'


class InitSO:

    def __init__(self):
        self.__init_security_groups()
        self.__init_services()

    def __init_security_groups(self):
            LOG.debug("=============Add SecurityGroups ===============")

            ###Get the config file for testing purposes
            f = open(os.path.join('%s/data/security_group/' % PATH, 'SecurityGroup-maas.json'))
            config_file = f.read()
            f.close()
            json_file = config_file
            resp = SecurityGroupOrchestrator.create(json.loads(json_file))
            LOG.debug('response: %s' % resp)

    def __init_services(self):
            LOG.debug("=============Add Services ===============")

            for file in os.listdir(os.path.join('%s/data/services/' % PATH)):
                LOG.debug("creating service from file %s" %file)
                f = open(os.path.join('%s/data/services/' % PATH, file))
                config_file = f.read()
                f.close()
                json_file = config_file
                resp = ServiceOrchestrator.create(json.loads(json_file))
                LOG.debug('response: %s' % resp)


