from interfaces.MonitoringAgent import MonitoringAgent as ABCMonitoringAgent
import logging
#from clients.ceilometer import Client as CeilometerClient
import random
from sm.so.service_orchestrator import LOG

__author__ = 'mpa'


class MonitoringAgentDummy(ABCMonitoringAgent):

    def __init__(self):
        #self.cmclient = CeilometerClient()
        LOG.debug("initialised monitoring agent")

    def deploy(self, token, tenant):
        pass

    def address(self, token):
        pass

    def get_item(self, res_id, item_name, **kwargs):
        item_value = random.randint(0,100)
        return item_value

    def dispose(self, token):
        pass