#!/usr/bin/python
# Copyright 2014 Technische Universitaet Berlin
# All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
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
from model.Entities import Subnet, Network, Port
from neutronclient.neutron import client
from sm.so.service_orchestrator import LOG

__author__ = 'lto'



class Client:
    def __init__(self, endpoint, token):
        self.neutron = client.Client('2.0', endpoint_url=endpoint, token=token)



    def list_ports(self):
        res = []
        lst = self.neutron.list_ports()
        for pt in lst.get('ports'):
            LOG.debug(pt)

            ips = {}
            for _ips in pt.get('fixed_ips'):
                ips[_ips.get('subnet_id')] = _ips.get('ip_address')
            res.append(Port(pt.get('name'), pt.get('id'), pt.get('mac_address'), ips=ips))
        return res

    def get_ports(self, unit):
        ports = []
        lst = self.neutron.list_ports()
        for pt in lst.get('ports'):
            for subnet, ip in unit.ips.iteritems():
                for net in pt.get('fixed_ips'):
                    if ip == net.get('ip_address'):
                        ips = {net.get('subnet_id'): ip}
                        p = Port(pt.get('name'), pt.get('id'), pt.get('mac_address'), ips=ips)
                        LOG.debug("Adding port " + str(p) + " to unit " + unit.hostname)
                        ports.append(p)
            for subnet, ip in unit.floating_ips.iteritems():
                for net in pt.get('fixed_ips'):
                    if ip == net.get('ip_address'):
                        ips = {net.get('subnet_id'): ip}
                        p = Port(pt.get('name'), pt.get('id'), pt.get('mac_address'), ips=ips)
                        LOG.debug("Adding port " + str(p) + " to unit " + unit.hostname)
                        ports.append(p)
        return ports

    def list_net(self):
        res = []
        LOG.debug('Requesting list of networks...')
        lst = self.neutron.list_networks()
        for net in lst.get('networks'):
            res.append(Network(net.get('name'), net.get('id'), net.get('router:external')))
        return res

    def list_subnet(self):
        res = []
        try:
            LOG.debug('Requesting list of subnetworks...')
            lst = self.neutron.list_subnets()
            for net in lst.get('subnets'):
                res.append(
                    Subnet(net.get('name'), net.get('id'), net.get('cidr'), net.get('allocation_pools')[0].get('start'),
                           net.get('allocation_pools')[0].get('end')))
            return res
        except Exception as e:
            LOG.warning("There was an error trying to collect subnets. The message is: " + e.message)
            raise e

    def get_networks(self):
        res = []
        try:
            subnets = self.list_subnet()
            lst = self.neutron.list_networks()
            for net in lst.get('networks'):
                n = Network(net.get('name'), net.get('id'), net.get('router:external'))
                for subnet in subnets:
                    if subnet.ext_id in net.get('subnets'):
                        n.subnets.append(subnet)
                res.append(n)
        except Exception as e:
            LOG.warning("There was an error while trying to connect to \"neutron\". The message is: " + e.message)
        return res