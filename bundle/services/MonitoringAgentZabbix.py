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
import sys
import os
from util.zabbix_api import ZabbixAPI
from clients.ceilometer import Client as CeilometerClient
from interfaces.MonitoringAgent import MonitoringAgent as ABCMonitoringAgent
from sm.so.service_orchestrator import LOG

__author__ = 'mpa'


# class Singleton(object):
#   _instance = None
#   def __new__(class_, *args, **kwargs):
#     if not isinstance(class_._instance, class_):
#         class_._instance = object.__new__(class_, *args, **kwargs)
#     return class_._instance

class MonitoringAgentZabbix(ABCMonitoringAgent):


    def __init__(self):
        pass

    def start(self):
        pass
        # zabbix_ip = '127.0.0.1'
        # self.zabbix = ZabbixAPI(server="http://%s/zabbix" %zabbix_ip, log_level=logging.DEBUG)
        # self.username = "Admin"
        # self.password = "zabbix"
        # LOG.debug("initialised monitoring agent")
        # try:
        #     LOG.debug('*** Connecting to MaaS')
        #     self.zabbix.login(self.username, self.password)
        #     LOG.debug('*** Connected to MaaS')
        # except Exception as e:
        #     LOG.error('*** Caught exception: %s: %s' % (e.__class__, e))
        #     sys.exit(1)


    def deploy(self, token, tenant):
        pass

    def address(self, token):
        pass

    def get_item(self, res_id, item_name, **kwargs):
        LOG.debug("Monitor: request resource %s for %s" % (res_id, item_name))
        #item_value = self.cmclient.get_statitics(resource_id=res_id, meter_name=item_name, period=kwargs.get('period') or 60)

        try:
            hostid = self.zabbix.host.get({"filter":{"host":res_id}})[0]["hostid"]
        except:
            print "WARNING: Hostname " + res_id + " not found"
            return

        try:
            item_value = self.zabbix.item.get({"output":"extend","hostids":hostid,"filter":{"key_":item_name}})[0]["lastvalue"]
        except Exception as e:
            print "ERROR: User metric not found"

        LOG.debug("Idle value received %s" % item_value)
        item_value = 100 - float(item_value)
        LOG.debug("real cpu usage %s" % item_value)
        return item_value

    def dispose(self, token):
        pass


if __name__ == "__main__":
    logging.basicConfig(format='%(asctime)s_%(process)d:%(pathname)s:%(lineno)d [%(levelname)s] %(message)s',level=logging.DEBUG)

    zabi = MonitoringAgentZabbix()
    zabi.get_item("cscfs-1", "system.cpu.util[,idle]")