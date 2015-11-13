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
from services.DatabaseManager import DatabaseManager
from model.Entities import ServiceInstance, Network
from util import SysUtil
from util.SysUtil import to_json
import yaml
from sm.so.service_orchestrator import LOG

__author__ = 'mpa'


class TemplateManager(object):

    @staticmethod
    def get_template(topology):
        #name = topology.name
        template = {}
        template['heat_template_version'] = '2013-05-23'
        resources = {}
        outputs = {}
        #print "create Template for Topology: %s" % name

        for service_instance in topology.service_instances:
            for unit in service_instance.units:
                #Create Ports and floating IPs for this unit
                ports = []
                floating_ips = []
                if service_instance.networks:
                    i=1
                    for network in service_instance.networks:
                        ###Creating Port for this service instance
                        new_port = None
                        #prepare port args for this service instance
                        port_args = {}
                        port_args['name'] = '%s-port-%s' % (unit.hostname, i)
                        port_args['private_net_id'] = network.private_net
                        port_args['private_subnet_id'] = network.private_subnet
                        # if "hss-1" in unit.hostname:
                        #     port_args['fixed_ip'] = "192.168.9.48"
                        # elif "hss-2" in unit.hostname:
                        #     port_args['fixed_ip'] = "192.168.9.55"
                        # else:
                        port_args['fixed_ip'] = network.fixed_ip

                        if network.security_groups:
                            port_args['security_groups'] = network.security_groups
                        new_port = Port(**port_args)
                        ports.append(new_port)
                        if network.public_net:
                            new_floating_ip_args = {}
                            new_floating_ip_args['name'] = '%s-floating_ip-%s' % (unit.hostname, i)
                            new_floating_ip_args['floating_network_id'] = network.public_net
                            new_floating_ip_args['port'] = new_port.name
                            new_floating_ip = FloatingIP(**new_floating_ip_args)
                            floating_ips.append(new_floating_ip)
                        ###Adding Security Groups
                        for _security_group in network.security_groups:
                            _new_name=_security_group.name
                            _new_rules=[]
                            _rules=_security_group.rules
                            for _rule in _rules:
                                _name = _rule.name
                                _remote_ip_prefix = _rule.remote_ip_prefix
                                _protocol = _rule.protocol
                                _port_range_max = int(_rule.port_range_max) if _rule.port_range_max else None
                                _port_range_min = int(_rule.port_range_min) if _rule.port_range_min else None
                                _new_rule = Rule(_name, _remote_ip_prefix, _protocol, _port_range_max, _port_range_min)
                                _new_rules.append(_new_rule)
                            _new_security_group = SecurityGroup(name=_new_name, rules=_new_rules)
                            resources.update(_new_security_group.dump_to_dict())
                        i += 1

                ###Create Server for this service instance
                new_server = None
                #prepare server args
                server_args = {}
                server_args['name'] = "%s" % unit.hostname
                server_args['hostname'] = "%s" % unit.hostname
                server_args['availability_zone'] = unit.availability_zone
                server_args['flavor'] = service_instance.flavor.name
                # if "hss-1" in unit.hostname:
                #     server_args['image'] = "hss-1"
                # elif "hss-2" in unit.hostname:
                #     server_args['image'] = "hss-2"
                # else:
                server_args['image'] = service_instance.image.name
                server_args['key_name'] = service_instance.key.name
                server_args['network_ports'] = ports
                server_args['user_data'] = service_instance.user_data
                server_args['requirements'] = service_instance.requirements
                new_server = Server(**server_args)

                resources.update(new_server.dump_to_dict())

                if ports:
                    for port in ports:
                        resources.update(port.dump_to_dict())
                if floating_ips:
                    for floating_ip in floating_ips:
                        resources.update(floating_ip.dump_to_dict())

        template['resources'] = resources

        ###Output section###
        db = DatabaseManager()
        for service_instance in topology.service_instances:
            for network_instance in service_instance.networks:
                if network_instance.public_net:
                    _public_network_names = [_network.name for _network in db.get_all(Network) if
                                             _network.ext_id == network_instance.public_net]
                    _public_network_name = None
                    if _public_network_names:
                        _public_network_name = _public_network_names[0]
                    else:
                        LOG.debug('ERROR: Cannot find network with id %s in Table Network' % network_instance.public_net)
                if network_instance.private_net:
                    _private_network_names = [_network.name for _network in db.get_all(Network) if
                                              _network.ext_id == network_instance.private_net]
                    _private_network_name = None
                    if _private_network_names:
                        _private_network_name = _private_network_names[0]
                    else:
                        LOG.debug('ERROR: Cannot find network with id %s in Table Network' % network_instance.net)

                for unit in service_instance.units:
                    if network_instance.public_net and _public_network_name:
                        output = {}
                        floating_name = '%s-floating_ip-1' % unit.hostname
                        output['value'] = {'get_attr': [floating_name,
                                                        'floating_ip_address']}
                        output['description'] = 'Public IP of %s.' % unit.hostname
                        outputs['mcn.endpoint.%s' % unit.hostname] = output
                    elif network_instance.private_net and _private_network_name:
                        output = {}
                        port_name = '%s-port-1' % unit.hostname
                        output['value'] = {'get_attr': [port_name, 'fixed_ips',
                                                        0, 'ip_address']}
                        output['description'] = 'Private IP of %s.' % unit.hostname
                        outputs['mcn.endpoint.%s' % unit.hostname] = output

                    if network_instance.public_net and _public_network_name:
                        network_type = "public"
                        output = {}
                        floating_name = '%s-floating_ip-1' % unit.hostname
                        output['value'] = {'get_attr': [floating_name,
                                                        'floating_ip_address']}
                        output['description'] = '%s ip of %s in %s.' % (
                            network_type.capitalize(),
                            unit.hostname,
                            network_instance.name)

                        outputs['mcn.endpoint.%s.%s.%s' % (unit.hostname,
                                                           network_instance.name,
                                                           network_type)] = output

                    if network_instance.private_net and _private_network_name:
                        network_type = "private"
                        output = {}
                        port_name = '%s-port-1' % unit.hostname
                        output['value'] = {'get_attr': [port_name, 'fixed_ips',
                                                        0, 'ip_address']}
                        output['description'] = '%s ip of %s in %s.' % (
                            network_type.capitalize(),
                            unit.hostname,
                            network_instance.name)

                        outputs['mcn.endpoint.%s.%s.%s' % (unit.hostname,
                                                           network_instance.name,
                                                           network_type)] = output

        template['outputs'] = outputs

        yaml.add_representer(unicode, lambda dumper, value: dumper.represent_scalar(u'tag:yaml.org,2002:str', value))
        yaml.add_representer(SysUtil.literal_unicode, SysUtil.literal_unicode_representer)
        LOG.debug((template))
        #LOG.debug(yaml.dumps(template))
        #f = open('/net/u/mpa/tempalte_file.yaml', 'w')
        #f.write(yaml.dump(template, indent=2))
        return yaml.dump(template)


class Server(object):
    def __init__(self, name, hostname, flavor, image, availability_zone=None, key_name = None, network_ports = [], user_data = None, requirements = []):
        ###Resource Type###
        self.type = "OS::Nova::Server"

        ###Basic parameters###
        self.name = name
        self.hostname = hostname
        self.image = image
        self.flavor = flavor
        self.key_name = key_name
        self.network_ports = network_ports
        self.user_data = user_data
        self.requirements = requirements
        self.availability_zone = availability_zone


    def dump_to_dict(self):
        db = DatabaseManager()
        resource = {}
        server_config = {}
        server_config['type'] = self.type
        properties = {}
        properties['name'] = self.name
        properties['image'] = self.image
        properties['flavor'] = self.flavor
        if self.key_name is not None: properties['key_name'] = self.key_name
        if self.availability_zone is not None: properties['availability_zone'] = self.availability_zone
        if self.network_ports is not None:
            networks = []
            LOG.debug(self.network_ports)
            for network_port in self.network_ports:
                networks.append({'port': { 'get_resource' : network_port.name}})
            properties['networks'] = networks
        if self.user_data:
            properties['user_data_format'] = 'RAW'
            properties['user_data'] = {}
            properties['user_data']['str_replace'] = {}
            properties['user_data']['str_replace']['template'] = ''
            _user_data = ''
            _user_data_list = []
            for command in self.user_data:
                _user_data += "%s\n" % command.command
            properties['user_data']['str_replace']['template'] = SysUtil.literal_unicode((_user_data))
            properties['user_data']['str_replace']['params'] = {'':''}
            if self.requirements:
                params = {}
                for requirement in self.requirements:
                    try:
                        source_service_instances = db.get_by_name(ServiceInstance,requirement.source)
                    except:
                        LOG.debug('ERROR: Entry %s was not found in Table ServiceInstance' % requirement.source)
                        raise
                    source_units = []
                    if source_service_instances:
                        source_service_instance = source_service_instances[0]
                        source_units = source_service_instance.units
                        LOG.debug(source_units)
                        if source_units:
                            if requirement.parameter == 'private_ip' or requirement.parameter == 'public_ip':
                                #Get requested network specified in the requirement
                                _networks = [network for network in source_service_instance.networks if network.name == requirement.obj_name ]
                                _network = None
                                if _networks:
                                    _network_id = _networks[0].private_net
                                else:
                                    LOG.debug('ERROR: obj_name %s was not found in networks of ServiceInstance %s' % (requirement.obj_name,source_service_instance))
                                    raise
                                #Get network name of the specified network id
                                _network_names = [network.name for network in db.get_all(Network) if network.ext_id == _network_id]
                                _network_name = None
                                if _network_names:
                                    _network_name = _network_names[0]
                                else:
                                    LOG.debug('ERROR: Cannot find network with id %s in Table Network' % _network_id)
                                if requirement.parameter == "private_ip":
                                    ip_number = 0
                                elif requirement.parameter == "public_ip":
                                    ip_number = 1
                                #Create the variable
                                _params = {}
                                _first_unit = source_units[0]
                                _template = '$%s' % _first_unit.hostname
                                _params['$%s' % _first_unit.hostname] = {'get_attr': [_first_unit.hostname, 'networks', _network_name, ip_number]}
                                for source_unit in source_units[1:]:
                                    _template += ';$%s' % source_unit.hostname
                                    _params['$%s' % source_unit.hostname] = {'get_attr': [source_unit.hostname, 'networks', _network_name, ip_number]}
                            param = {}
                            param[requirement.name] = {}
                            param[requirement.name]['str_replace'] = {}
                            param[requirement.name]['str_replace']['template'] = _template
                            param[requirement.name]['str_replace']['params'] = _params
                            params.update(param)
                        else:
                            LOG.debug('ERROR: Units for ServiceInstance %s were not found.' % requirement.source)
                            raise Exception
                    else:
                        LOG.debug('ERROR: ServiceInstance %s was not found' % requirement.source)
                        raise Exception
                properties['user_data']['str_replace']['params'] = params
        server_config['properties'] = properties
        resource[self.name] = server_config
        return resource


class Port(object):
    def __init__(self, name, private_net_id, private_subnet_id, fixed_ip=None, security_groups = []):
        self.name = name
        self.type = 'OS::Neutron::Port'
        self.private_net_id = private_net_id
        self.private_subnet_id = private_subnet_id
        self.fixed_ip = fixed_ip
        self.security_groups = security_groups

    def dump_to_dict(self):
        resource = {}
        port_config = {}
        port_config['type'] = self.type

        properties = {}
        properties['network_id'] = self.private_net_id
        if self.private_subnet_id or self.fixed_ip:
            properties['fixed_ips'] = []
        if self.fixed_ip:
            properties['fixed_ips'].append({'ip_address' : self.fixed_ip})
        elif self.private_subnet_id:
            properties['fixed_ips'].append({'subnet_id' : self.private_subnet_id})
        if self.security_groups:
            properties['security_groups'] = []
            for security_group in self.security_groups:
                properties['security_groups'].append({'get_resource': security_group.name})
        port_config['properties'] = properties
        resource[self.name] = port_config
        return resource


class FloatingIP(object):
    def __init__(self, name, floating_network_id, port):
        self.name = name
        self.type = 'OS::Neutron::FloatingIP'
        self.floating_network_id = floating_network_id
        self.port = port

    def dump_to_dict(self):
        resource = {}
        floating_ip_config = {}
        floating_ip_config['type'] = self.type

        properties = {}
        properties['floating_network_id'] = self.floating_network_id
        properties['port_id'] = {'get_resource': self.port}

        floating_ip_config['properties'] = properties
        resource[self.name] = floating_ip_config
        return resource


class SecurityGroup(object):
    def __init__(self, name, rules = []):
        self.name = name
        self.type = 'OS::Neutron::SecurityGroup'
        self.rules = rules

    def dump_to_dict(self):
        resource = {}
        security_group_config = {}
        security_group_config['type'] = self.type

        properties = {}
        properties['rules'] = []
        for rule in self.rules:
            properties['rules'].append(rule.dump_to_dict())

        security_group_config['properties'] = properties
        resource[self.name] = security_group_config
        return resource


class Rule(object):
    def __init__(self, name, remote_ip_prefix, protocol, port_range_max, port_range_min):
        self.name = name
        self.remote_ip_prefix = remote_ip_prefix
        self.protocol = protocol
        self.port_range_max = port_range_max
        self.port_range_min = port_range_min

    def dump_to_dict(self):
        rule_config = {}
        rule_config['remote_ip_prefix'] = self.remote_ip_prefix
        rule_config['protocol'] = self.protocol
        if self.port_range_min and self.port_range_max:
            rule_config['port_range_max'] = self.port_range_max
            rule_config['port_range_min'] = self.port_range_min
        return rule_config
