import httplib
import json
import os

from services.DatabaseManager import DatabaseManager
from model.Entities import SecurityGroup, AlchemyEncoder, Service


__author__ = 'lto'

import logging

PATH = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir))
HOST = 'localhost'

def setup_logger():
    global logger
    logging.basicConfig(format='%(asctime)s_%(process)d:%(pathname)s:%(lineno)d [%(levelname)s] %(message)s',
                        level=logging.DEBUG)
    logger = logging.getLogger("EMMLogger")
    handler = logging.FileHandler('%s/logs/%s.log' % (PATH, os.path.basename(__file__)))
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s_%(process)d:%(pathname)s:%(lineno)d [%(levelname)s] %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)


def create_sec_groups():
    global new_secgroup_json
    new_secgroup = {}
    new_secgroup["name"] = "secgroup"
    new_secgroup['rules'] = []
    new_secgroup['rules'].append(
        {'name': 'tcp', 'remote_ip_prefix': '0.0.0.0/0', 'protocol': 'tcp', 'port_range_min': 1,
         'port_range_max': 65535})
    new_secgroup['rules'].append(
        {'name': 'udp', 'remote_ip_prefix': '0.0.0.0/0', 'protocol': 'udp', 'port_range_min': 1,
         'port_range_max': 65535})
    new_secgroup_json = json.dumps(new_secgroup, cls=AlchemyEncoder)
    return new_secgroup_json


def create_service(security_group_ids):
    global new_service_json
    new_service = {}
    new_service["service_type"] = "controller"
    new_service['image'] = "nubomedia-broker"
    new_service['flavor'] = "m1.medium"
    new_service['size'] = {'def': 1, 'max': 1, 'min': 1}
    new_service['config'] = {'hostname': 'ControlServer'}

    new_service['security_groups'] = ['1']
    new_service_json = json.dumps(new_service)
    return new_service_json

if __name__ == '__main__':

    setup_logger()

    _json = create_sec_groups()

    #Establish connection to EMM
    connection = httplib.HTTPConnection('%s:8090' % HOST)
    headers = {'Content-type': 'application/json'}

    logger.debug('\n###################CREATE SECURITY GROUPS###################')
    connection.request('POST', '/secgroups', _json, headers)
    response = connection.getresponse()
    resp = (response.read())

    logger.debug(resp)

    logger.debug('\n###################CREATE SECURITY GROUPS###################')
    connection.request('GET', '/secgroups')
    response = connection.getresponse()
    resp = (response.read())

    logger.debug(resp)

    logger.debug('\n###################CREATE SERVICE###########################')

    db = DatabaseManager()

    lst = [db.get_all(SecurityGroup)]
    _json = create_service(lst)

    connection.request('POST', '/services', _json, headers)
    response = connection.getresponse()
    resp = (response.read())

    logger.debug(resp)


    logger.debug('\n####################GET SERVICES############################')
    connection.request('GET', '/services')

    response = connection.getresponse()
    resp = (response.read())

    logger.debug(resp)

    logger.debug('\n####################DELETE SERVICE############################')

    for s in db.get_all(Service):
        logger.debug(repr(s))
    connection.request('DELETE', '/services/1')
    resp = (response.read())

    logger.debug(resp)