from interfaces.MonitoringAgent import MonitoringAgent as ABCMonitoringAgent
import logging
from clients.ceilometer import Client as CeilometerClient
from sm.so.service_orchestrator import LOG

__author__ = 'mpa'


class MonitoringAgent(ABCMonitoringAgent):

    def __init__(self):
        self.cmclient = CeilometerClient()
        LOG.debug("initialised monitoring agent")

    def deploy(self, token, tenant):
        pass

    def address(self, token):
        pass

    def get_item(self, res_id, item_name, **kwargs):
        LOG.debug("Monitor: request resource %s for %s" % (res_id, item_name))
        item_value = self.cmclient.get_statitics(resource_id=res_id, meter_name=item_name, period=kwargs.get('period') or 60)
        LOG.debug("Monitor: received %s" % item_value)
        return item_value

    def dispose(self, token):
        pass