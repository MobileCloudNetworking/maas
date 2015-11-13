# Copyright 2014 Technische Universitaet Berlin
# Copyright 2014 Zuercher Hochschule fuer Angewandte Wissenschaften
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
import time

__author__ = 'giuseppe'

import os
import yaml

from emm_exceptions.NotFoundException import NotFoundException
from emm_exceptions.NotUniqueException import NotUniqueException
from emm_exceptions.NotDefinedException import NotDefinedException
from emm_exceptions.TypeErrorException import TypeErrorException
from emm_exceptions.InvalidInputException import InvalidInputException
from core.TopologyOrchestrator import TopologyOrchestrator

from util.FactoryAgent import FactoryAgent
from util.SysUtil import SysUtil as sys_util

from sdk.mcn import util

from sm.so import service_orchestrator
from sm.so.service_orchestrator import LOG

SO_DIR = os.environ.get('BUNDLE_DIR', '.')

topology_mapping = {
    'bern': 'topology-maas-bern.json',
    'bart': 'topology-maas-bart.json'
}


class SoExecution(service_orchestrator.Execution):
    """
    class docs
    """

    def __init__(self, token, tenant_name):
        """
        Constructor
        """
        super(SoExecution, self).__init__(token, tenant_name)
        # by default
        self.topology_type = "topology-maas-bern.json"
        self.token = token
        self.tenant_name = tenant_name
        self.stack_id = None
        self.maas = None
        self.location = 'bern'
        # make sure we can talk to deployer...
        LOG.debug("sending request to the url %s" % os.environ['DESIGN_URI'])

        self.conf = sys_util().get_sys_conf()
        LOG.debug("instantiating deployer %s" %self.conf['deployer'])
        self.deployer = None

    def deploy(self, attributes):
        """
        Deploy method
        """
        if self.stack_id is not None:
            pass
        parameters = {}
        # defining the location of the topology
        if 'maas.location' in attributes:
            self.location = parameters['location'] = os.environ['location'] = attributes['maas.location']
            LOG.debug("location %s passed via OCCI Attribute"%self.location)

        self.deployer = FactoryAgent().get_agent(self.conf['deployer'])
        self.topology_type = topology_mapping[self.location]
        LOG.info("deploying template %s" % (self.topology_type,))

        # read template...
        f = open(os.path.join(SO_DIR, 'data/topologies', self.topology_type))
        template = f.read()
        f.close()
        LOG.debug("content of the topology %s" % template)

        # extracting hot template
        try:
            config = yaml.load(template)
            LOG.debug(config)
        except yaml.YAMLError, exc:
            if hasattr(exc, 'problem_mark'):
                mark = exc.problem_mark
                LOG.error("Error in configuration file:", exc)
                LOG.error("Error position: (%s:%s)" % (mark.line + 1, mark.column + 1))
            else:
                LOG.error("Error in configuration file:", exc)

        # creating the topology object
        try:
            topology = TopologyOrchestrator.create(config)
        except NotFoundException, msg:
            LOG.error(msg)
            return
        except NotUniqueException, msg:
            LOG.error(msg)
            return
        except NotDefinedException, msg:
            LOG.error(msg)
            return
        except InvalidInputException, msg:
            LOG.error(msg)
            return
        except TypeErrorException, msg:
            LOG.error(msg)
            return
        except Exception, msg:
            LOG.error(msg)
            return

        # deploying the topology
        timeout = time.time() + 60*5
        while True:
            if self.stack_id is None and time.time() < timeout:
                stack_details = self.deployer.deploy(topology)
                self.stack_id = stack_details.id
                time.sleep(10)
            else:
                LOG.info("deployed topology with id %s" % self.stack_id)
                break

    def provision(self):
        """
        Provision method
        """
        pass

    def dispose(self):
        """
        Dispose method
        """
        LOG.info("deleting topology with id %s " % self.stack_id)
        if self.stack_id is not None:
            topology = TopologyOrchestrator.get(self.stack_id)
            LOG.debug("topology to be deleted %s " % topology)
            self.deployer.dispose(topology)
            TopologyOrchestrator.delete(topology)
            self.stack_id = None
            if self.maas is not None:
                util.dispose_maas(self.token, self.maas)

    def state(self):
        """
        Report on state.
        """
        LOG.info("retrieving state of the running stack with id %s" % self.stack_id)
        # LOG.info('Resolver state:')
        # LOG.info(resolver_state.__repr__())
        if self.stack_id is not None:
            topology = TopologyOrchestrator.get(self.stack_id)
            stk = self.deployer.details(topology.ext_id)
            res = {'state': stk['stack_status'],
               'name': stk['stack_name'],
               'id': stk['id']}
            if 'outputs' in stk:
                res['output'] = stk['outputs']
            output = ''
            try:
                output = res['output']
            except KeyError:
                pass

            LOG.debug(" state %s, output %s"%(res['state'],output))
            return res['state'], str(self.stack_id), output
        else:
            return 'CREATE_COMPLETE', 'N/A', ''


class ServiceOrchestrator(object):
    def __init__(self, token, tenant_name):
        os.environ['OS_AUTH_TOKEN'] = token
        self.so_e = SoExecution(token, tenant_name)





