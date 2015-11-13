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
from interfaces.ConnectivityManager import ConnectivityManager as ABCConnectivityManager
from sm.so.service_orchestrator import LOG

__author__ = 'beb'



class ConnectivityManager(ABCConnectivityManager):

    def __init__(self):
        pass

    def set_host(self, topology):
        pass

    def set_qos(self, topology):
        pass