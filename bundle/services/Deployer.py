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

import logging

from interfaces.Deployer import Deployer as ABCDeployer
from services.DatabaseManager import DatabaseManager
from services import TemplateManager
from util.FactoryAgent import FactoryAgent
from util.SysUtil import SysUtil
from clients.heat import Client as HeatClient
from heatclient.exc import HTTPNotFound
from util.SysUtil import translate
from sm.so.service_orchestrator import LOG

__author__ = 'mpa'



class Deployer(ABCDeployer):
    def __init__(self):
        self.heatclient = HeatClient()
        conf = SysUtil().get_sys_conf()
        LOG.debug("Get runtime agent: " + conf['runtime_agent'])
        self.runtime_agent = FactoryAgent().get_agent(conf['runtime_agent'])
        #self.register_agent = FactoryAgent().get_agent(conf['register_agent'])
        self.template_manager = FactoryAgent().get_agent(conf['template_manager'])
        self.db = FactoryAgent().get_agent(conf['database_manager'])
        self.checker = FactoryAgent().get_agent(conf['checker'])

    def deploy(self, topology):
        #deploy only when the ext_id is None otherwise the topology is already deployed
        if topology.ext_id is None:
            LOG.debug("Start Deploying topology %s" % topology.name)
            _name = topology.ext_name
            _template = self.template_manager.get_template(topology)
            LOG.debug("Stack name: %s" % _name)
            LOG.debug("Template: %s" % _template)
            try:
                stack_details = self.heatclient.deploy(name=_name, template=_template)
                LOG.debug("stack details after deploy: %s" % stack_details)
                if stack_details:
                    topology.ext_id = stack_details['stack'].get('id')
                    LOG.debug("stack id: %s" % topology.ext_id)
                else:
                    raise Exception('Error during deployment on the testbed.')
            except Exception, exc:
                LOG.exception(exc)
                topology.state = 'ERROR'
                topology.ext_id = None
                raise
        else:
            LOG.debug("Restart topology %s" % topology.name)
            #check that the topology is still valid
            try:
                self.checker.check(topology=topology)
                print "finish check"
            except Exception, exc:
                exc.message = 'Topology \"%s\" is not valid anymore. (%s)' % (topology.name, exc.message)
                topology.state = 'ERROR'
                topology.detailed_state = exc.message
                self.db.update(topology)
                LOG.error(exc.message)
                raise exc
            #check that the topology already exists on OpenStack
            try:
                stack_details = self.heatclient.show(topology.ext_id)
            except HTTPNotFound, exc:
                exc.message = 'Topology \"%s\" was not found on OpenStack anymore. (%s)' % (topology.name, exc.message)
                topology.state = 'DELETED'
                topology.detailed_state = exc.message
                self.db.update(topology)
                LOG.error(exc.message)
                raise exc
        LOG.debug("Starting RuntimeAgent for topology %s." % topology.id)
        self.runtime_agent.start(topology)
        #self.register_agent.start()
        return topology

    def dispose(self, topology):
        # checker_thread = self.checker_thread
        # LOG.debug("Get RuntimeAgent for topology %s" % topology.id)
        # runtime_agent = self.runtime_agents.get(topology.id)
        #LOG.debug("Got RuntimeAgent: %s" % self.runtime_agent)
        stack_details = None
        topology.state = 'DELETING'
        self.db.update(topology)
        if self.runtime_agent:
            self.runtime_agent.stop(topology.id)
            try:
                stack_details = self.heatclient.delete(topology.ext_id)
            except HTTPNotFound, exc:
                exc.message = 'Topology \"%s\" was not found on OpenStack anymore. (%s)' % (topology.name, exc.message)
                topology.state = 'DELETED'
                topology.detailed_state = exc.message
                self.db.update(topology)
                LOG.error(exc.message)
                raise exc
            except Exception, msg:
                LOG.error(msg)
                topology.state = 'ERROR'
            LOG.debug("stack details after delete: %s" % stack_details)
        return stack_details

    def update(self, topology):
        if self.runtime_agent:
            self.runtime_agent.stop(topology.id)
        LOG.debug("Start Updating topology %s" % topology.name)
        _name = topology.ext_name
        _template = self.template_manager.get_template(topology)
        LOG.debug("Stack name: %s" % _name)
        LOG.debug("Template: %s" % _template)
        try:
            stack_details = self.heatclient.update(stack_id=topology.ext_id, template=_template)
            LOG.debug("stack details after update: %s" % stack_details)
            LOG.debug("stack id: %s" % topology.ext_id)
        except Exception, msg:
            LOG.error(msg)
            topology.state = 'ERROR'
            topology.ext_id = None
            return topology
        LOG.debug("Starting RuntimeAgent for topology %s." % topology.id)
        self.runtime_agent.start(topology)
        #self.register_agent.start()
        return topology


    def details(self, topology_id):
        stack_details = self.heatclient.show(topology_id)
        LOG.debug("Stack actually running %s" % stack_details)
        return stack_details