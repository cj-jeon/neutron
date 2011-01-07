#vim: tabstop=4 shiftwidth=4 softtabstop=4
#copyright 2011 Cisco Systems, Inc.  All rights reserved.
#
#    Licensed under the Apache License, Version 2.0(the "License"); you may
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
#
# @author: Shubhangi Satras, Cisco Systems, Inc.
#          Shweta Padubidri, Cisco Systems, Inc.
#
import unittest
import logging as LOG
from quantum.common import exceptions as exc
from quantum.plugins.cisco.common import cisco_constants as const
from quantum.plugins.cisco.ucs import cisco_ucs_plugin
from quantum.plugins.cisco.ucs import cisco_ucs_configuration  as conf
from quantum.plugins.cisco.common import cisco_credentials as cred

from quantum.plugins.cisco.db import api as db
from quantum.plugins.cisco.db import l2network_db as cdb
from quantum.plugins.cisco.common import cisco_exceptions as c_exc

from quantum.plugins.cisco.ucs import cisco_ucs_inventory as ucsinv

LOG.basicConfig(level=LOG.WARN)
LOG.getLogger("cisco_ucs_plugin")


class UCSVICTestPlugin(unittest.TestCase):

    def setUp(self):

        self.tenant_id = "test_tenant_cisco12"
        self.net_name = "test_network_cisco12"
        self.net_id = 000011
        self.vlan_name = conf.DEFAULT_VLAN_NAME
        self.vlan_id = conf.DEFAULT_VLAN_ID
        self.port_id = "4"
        cdb.initialize()
        cred.Store.initialize()
        self._cisco_ucs_plugin = cisco_ucs_plugin.UCSVICPlugin()
        self.device_ip = conf.UCSM_IP_ADDRESS
        self._ucs_inventory = ucsinv.UCSInventory()
        self.chassis_id = '1'
        self.blade_id = '5'
        self.blade_intf_distinguished_name = 'sys/chassis-1/blade-5/'\
                                             'adaptor-1/host-eth-6'

    def test_create_network(self):
        """
        Tests creation of new Virtual Network.
        """
        LOG.debug("UCSVICTestPlugin:_test_create_network() called\n")
        new_network = db.network_create(self.tenant_id, self.net_name)
        cdb.add_vlan_binding(str(self.vlan_id), self.vlan_name,
                             new_network[const.UUID])
        new_net_dict = self._cisco_ucs_plugin.create_network(
                self.tenant_id, new_network[const.NETWORKNAME],
                new_network[const.UUID], self.vlan_name, self.vlan_id,
                device_ip=self.device_ip)
        self.assertEqual(new_net_dict[const.NET_ID], new_network[const.UUID])
        self.assertEqual(new_net_dict[const.NET_NAME],
                         new_network[const.NETWORKNAME])
        self.tearDownNetwork(self.tenant_id, new_network[const.UUID])

    def test_delete_network(self):
        """
        Tests deletion of  the network with the specified network identifier
        belonging to the specified tenant.
        """
        LOG.debug("UCSVICTestPlugin:test_delete_network() called\n")
        new_network = db.network_create(self.tenant_id, self.net_name)
        cdb.add_vlan_binding(str(self.vlan_id), self.vlan_name,
                             new_network[const.UUID])
        new_net_dict = self._cisco_ucs_plugin.create_network(
                self.tenant_id, new_network[const.NETWORKNAME],
                new_network[const.UUID], self.vlan_name, self.vlan_id,
                device_ip=self.device_ip)
        new_net_dict = self._cisco_ucs_plugin.delete_network(
           self.tenant_id, new_network[const.UUID], device_ip=self.device_ip)
        self.assertEqual(new_net_dict[const.NET_ID], new_network[const.UUID])

    def test_get_network_details(self):
        """
        Tests the deletion the Virtual Network belonging to a the
        spec
        """
        LOG.debug("UCSVICTestPlugin:test_get_network_details() called\n")
        new_network = db.network_create(self.tenant_id, self.net_name)
        cdb.add_vlan_binding(str(self.vlan_id), self.vlan_name,
                             new_network[const.UUID])
        new_net_dict = self._cisco_ucs_plugin.create_network(
                self.tenant_id, new_network[const.NETWORKNAME],
                new_network[const.UUID], self.vlan_name, self.vlan_id,
                device_ip=self.device_ip)
        new_net_dict = self._cisco_ucs_plugin.get_network_details(
                   self.tenant_id, new_network[const.UUID],
                   device_ip=self.device_ip)
        self.assertEqual(new_net_dict[const.NET_ID], new_network[const.UUID])
        self.assertEqual(new_net_dict[const.NET_NAME],
                         new_network[const.NETWORKNAME])
        self.tearDownNetwork(self.tenant_id, new_network[const.UUID])

    def test_get_all_networks(self):
        """
        Tests whether  dictionary is returned containing all
        <network_uuid, network_name> for
        the specified tenant.
        """
        LOG.debug("UCSVICTestPlugin:test_get_all_networks() called\n")
        new_network1 = db.network_create(self.tenant_id, self.net_name)
        cdb.add_vlan_binding(str(self.vlan_id), self.vlan_name,
                             new_network1[const.UUID])
        new_net_dict1 = self._cisco_ucs_plugin.create_network(
                self.tenant_id, new_network1[const.NETWORKNAME],
                new_network1[const.UUID], self.vlan_name, self.vlan_id,
                device_ip=self.device_ip)
        new_network2 = db.network_create(self.tenant_id, "test_network2")
        cdb.add_vlan_binding("6", "q-000006vlan", new_network2[const.UUID])
        new_net_dict2 = self._cisco_ucs_plugin.create_network(
                self.tenant_id, new_network2[const.NETWORKNAME],
                new_network2[const.UUID], "q-000006vlan", "6",
                device_ip=self.device_ip)

        net_list = self._cisco_ucs_plugin.get_all_networks(
                                self.tenant_id, device_ip=self.device_ip)
        net_id_list = [new_net_dict1, new_net_dict2]

        self.assertTrue(net_list[0] in net_id_list)
        self.assertTrue(net_list[1] in net_id_list)
        self.tearDownNetwork(self.tenant_id, new_network1[const.UUID])
        self.tearDownNetwork(self.tenant_id, new_network2[const.UUID])

    def test_get_all_ports(self):
        """
        Retrieves all port identifiers belonging to the
        specified Virtual Network.
        """
        LOG.debug("UCSVICPlugin:get_all_ports() called\n")
        new_network = db.network_create(self.tenant_id, self.net_name)
        cdb.add_vlan_binding(str(self.vlan_id), self.vlan_name,
                             new_network[const.UUID])
        new_net_dict = self._cisco_ucs_plugin.create_network(
                self.tenant_id, new_network[const.NETWORKNAME],
                new_network[const.UUID], self.vlan_name, self.vlan_id,
                device_ip=self.device_ip)
        new_port1 = db.port_create(new_network[const.UUID], const.PORT_UP)
        port_dict1 = self._cisco_ucs_plugin.create_port(
                            self.tenant_id, self.net_id, const.PORT_UP,
                            new_port1[const.UUID], device_ip=self.device_ip,
                            ucs_inventory=self._ucs_inventory,
                            least_rsvd_blade_dict=self._ucs_inventory.\
                            get_least_reserved_blade())
        new_port2 = db.port_create(new_network[const.UUID], const.PORT_UP)
        port_dict2 = self._cisco_ucs_plugin.create_port(
                               self.tenant_id, self.net_id, const.PORT_UP,
                               new_port2[const.UUID], device_ip=self.device_ip,
                               ucs_inventory=self._ucs_inventory,
                               least_rsvd_blade_dict=self._ucs_inventory.\
                               get_least_reserved_blade())
        ports_on_net = self._cisco_ucs_plugin.get_all_ports(
                           self.tenant_id, new_net_dict[const.NET_ID],
                           device_ip=self.device_ip,
                           ucs_inventory=self._ucs_inventory,
                           least_rsvd_blade_dict=self._ucs_inventory.\
                           get_least_reserved_blade())
        port_list = [port_dict1, port_dict2]
        self.assertTrue(str(ports_on_net[1]) == str(port_list[1]) or
                        str(ports_on_net[1]) == str(port_list[0]))
        self.assertTrue(str(ports_on_net[0]) == str(port_list[1]) or
                        str(ports_on_net[0]) == str(port_list[0]))

        self._cisco_ucs_plugin.delete_port(
                     self.tenant_id, new_net_dict[const.NET_ID],
                     port_dict1[const.PORTID], device_ip=self.device_ip,
                     ucs_inventory=self._ucs_inventory,
                     chassis_id=self.chassis_id, blade_id=self.blade_id,
                     blade_intf_distinguished_name=self.\
                     blade_intf_distinguished_name,
                     least_rsvd_blade_dict=self._ucs_inventory.\
                     get_least_reserved_blade())
        self.tearDownNetworkPort(
                 self.tenant_id, new_net_dict[const.NET_ID],
                 port_dict2[const.PORTID])

    def test_create_port(self):
        """
        Tests creation of a port on the specified Virtual Network.
        """
        LOG.debug("UCSVICTestPlugin:_test_create_port() called\n")

        new_network = db.network_create(self.tenant_id, self.net_name)
        cdb.add_vlan_binding(str(self.vlan_id), self.vlan_name,
                             new_network[const.UUID])
        new_net_dict = self._cisco_ucs_plugin.create_network(
                self.tenant_id, new_network[const.NETWORKNAME],
                new_network[const.UUID], self.vlan_name, self.vlan_id,
                device_ip=self.device_ip)
        new_port = db.port_create(new_network[const.UUID], const.PORT_UP)
        port_dict = self._cisco_ucs_plugin.create_port(
                            self.tenant_id, self.net_id, const.PORT_UP,
                            new_port[const.UUID], device_ip=self.device_ip,
                            ucs_inventory=self._ucs_inventory,
                            least_rsvd_blade_dict=self._ucs_inventory.\
                            get_least_reserved_blade())
        self.assertEqual(port_dict[const.PORTID], new_port[const.UUID])
        profile_name = self._cisco_ucs_plugin.\
                           _get_profile_name(port_dict[const.PORTID])
        self.assertTrue(profile_name != None)
        self.tearDownNetworkPort(
                 self.tenant_id, new_net_dict[const.NET_ID],
                 port_dict[const.PORTID])

    def test_delete_port(self):
        """
        Tests Deletion of a port on a specified Virtual Network,
        if the port contains a remote interface attachment,
        the remote interface should first be un-plugged and
        then the port can be deleted.
        """
        LOG.debug("UCSVICTestPlugin:_test_delete_port() called\n")
        new_network = db.network_create(self.tenant_id, self.net_name)
        cdb.add_vlan_binding(str(self.vlan_id), self.vlan_name,
                             new_network[const.UUID])
        new_net_dict = self._cisco_ucs_plugin.create_network(
                self.tenant_id, new_network[const.NETWORKNAME],
                new_network[const.UUID], self.vlan_name, self.vlan_id,
                device_ip=self.device_ip)
        new_port = db.port_create(new_network[const.UUID], const.PORT_UP)
        port_dict = self._cisco_ucs_plugin.create_port(
                            self.tenant_id, self.net_id, const.PORT_UP,
                            new_port[const.UUID], device_ip=self.device_ip,
                            ucs_inventory=self._ucs_inventory,
                            least_rsvd_blade_dict=self._ucs_inventory.\
                            get_least_reserved_blade())
        port_bind = self._cisco_ucs_plugin.delete_port(
                         self.tenant_id, new_net_dict[const.NET_ID],
                         port_dict[const.PORTID], device_ip=self.device_ip,
                         ucs_inventory=self._ucs_inventory,
                         chassis_id=self.chassis_id, blade_id=self.blade_id,
                         blade_intf_distinguished_name=self.\
                         blade_intf_distinguished_name,
                         least_rsvd_blade_dict=self._ucs_inventory.\
                         get_least_reserved_blade())

        self.assertEqual(port_bind[const.PORTID], new_port[const.UUID])
        self.tearDownNetwork(self.tenant_id, new_net_dict[const.NET_ID])

    def _test_get_port_details(self, port_state):
        """
        Tests whether  user is able  to retrieve a remote interface
        that is attached to this particular port when port state is Up.
        """
        LOG.debug("UCSVICTestPlugin:_test_get_port_details() called\n")
        new_network = db.network_create(self.tenant_id, self.net_name)
        cdb.add_vlan_binding(str(self.vlan_id), self.vlan_name,
                             new_network[const.UUID])
        new_net_dict = self._cisco_ucs_plugin.create_network(
                self.tenant_id, new_network[const.NETWORKNAME],
                new_network[const.UUID], self.vlan_name, self.vlan_id,
                device_ip=self.device_ip)
        new_port = db.port_create(new_network[const.UUID], port_state)
        port_dict = self._cisco_ucs_plugin.create_port(
                            self.tenant_id, self.net_id, port_state,
                            new_port[const.UUID], device_ip=self.device_ip,
                            ucs_inventory=self._ucs_inventory,
                            least_rsvd_blade_dict=self._ucs_inventory.\
                            get_least_reserved_blade())

        port_detail = self._cisco_ucs_plugin.get_port_details(
                            self.tenant_id, new_net_dict[const.NET_ID],
                            port_dict[const.PORTID], device_ip=self.device_ip)
        self.assertEqual(str(port_dict), str(port_detail))
        self.tearDownNetworkPort(
                 self.tenant_id, new_net_dict[const.NET_ID],
                 port_dict[const.PORTID])

    def test_get_port_details_state_up(self):
        self._test_get_port_details(const.PORT_UP)

    def test_show_port_state_down(self):
        self._test_get_port_details(const.PORT_DOWN)

    def test_create_port_profile(self):
        LOG.debug("UCSVICTestPlugin:test_create_port_profile() called\n")
        new_network = db.network_create(self.tenant_id, self.net_name)
        cdb.add_vlan_binding(str(self.vlan_id), self.vlan_name,
                             new_network[const.UUID])
        new_port = db.port_create(new_network[const.UUID], const.PORT_UP)
        self._cisco_ucs_plugin._set_ucsm(self.device_ip)
        new_port_profile = self._cisco_ucs_plugin._create_port_profile(
                                self.tenant_id, new_network[const.UUID],
                                new_port[const.UUID], self.vlan_name,
                                self.vlan_id)
        profile_name = self._cisco_ucs_plugin.\
                            _get_profile_name(new_port[const.UUID])
        self.assertEqual(new_port_profile[const.PROFILE_NAME], profile_name)
        self.assertEqual(new_port_profile[const.PROFILE_VLAN_NAME],
                         self.vlan_name)
        self.assertEqual(new_port_profile[const.PROFILE_VLAN_ID], self.vlan_id)
        self._cisco_ucs_plugin._delete_port_profile(new_port[const.UUID],
                                                    profile_name)

    def test_delete_port_profile(self):
        LOG.debug("UCSVICTestPlugin:test_delete_port_profile() called\n")
        new_network = db.network_create(self.tenant_id, self.net_name)
        cdb.add_vlan_binding(str(self.vlan_id), self.vlan_name,
                             new_network[const.UUID])
        new_port = db.port_create(new_network[const.UUID], const.PORT_UP)
        self._cisco_ucs_plugin._set_ucsm(self.device_ip)
        self._cisco_ucs_plugin._create_port_profile(
                                self.tenant_id, new_network[const.UUID],
                                new_port[const.UUID], self.vlan_name,
                                self.vlan_id)
        profile_name = self._cisco_ucs_plugin.\
                            _get_profile_name(new_port[const.UUID])

        counter1 = self._cisco_ucs_plugin._port_profile_counter
        self._cisco_ucs_plugin._delete_port_profile(new_port[const.UUID],
                                                    profile_name)
        counter2 = self._cisco_ucs_plugin._port_profile_counter
        self.assertEqual(counter1 - 1, counter2)

    def test_plug_interface(self, remote_interface_id=None,
                            new_vlanid=10, new_vlan_name='new_vlan'):
        """
        Attaches a remote interface to the specified port on the
        specified Virtual Network.
        """
        LOG.debug("UCSVICTestPlugin:_test_plug_interface() called\n")
        new_network = db.network_create(self.tenant_id, self.net_name)
        cdb.add_vlan_binding(str(self.vlan_id), self.vlan_name,
                             new_network[const.UUID])
        new_net_dict = self._cisco_ucs_plugin.create_network(
                self.tenant_id, new_network[const.NETWORKNAME],
                new_network[const.UUID], self.vlan_name, self.vlan_id,
                device_ip=self.device_ip)
        new_port = db.port_create(new_network[const.UUID], const.PORT_UP)
        port_dict = self._cisco_ucs_plugin.create_port(
                            self.tenant_id, new_net_dict[const.NET_ID],
                            const.PORT_UP, new_port[const.UUID],
                            device_ip=self.device_ip,
                            ucs_inventory=self._ucs_inventory,
                            least_rsvd_blade_dict=self._ucs_inventory.\
                            get_least_reserved_blade())
        cdb.update_vlan_binding(new_network[const.UUID],
                                str(new_vlanid), new_vlan_name)
        port_bind = self._cisco_ucs_plugin.plug_interface(
                           self.tenant_id, new_net_dict[const.NET_ID],
                           port_dict[const.PORTID], remote_interface_id,
                           device_ip=self.device_ip)
        self.assertEqual(port_bind[const.VLANNAME], new_vlan_name)
        self.assertEqual(port_bind[const.VLANID], new_vlanid)
        self.tearDownNetworkPortInterface(
                                   self.tenant_id, new_net_dict[const.NET_ID],
                                   new_port[const.UUID])

    def test_unplug_interface(self, remote_interface_id=None,
                              new_vlanid=10, new_vlan_name='new_vlan'):
        """
        Tests whether remote interface detaches from the specified port on the
        specified Virtual Network.
        """
        LOG.debug("UCSVICTestPlugin:_test_unplug_interface() called\n")
        new_network = db.network_create(self.tenant_id, self.net_name)
        cdb.add_vlan_binding(str(self.vlan_id), self.vlan_name,
                             new_network[const.UUID])
        new_net_dict = self._cisco_ucs_plugin.create_network(
                self.tenant_id, new_network[const.NETWORKNAME],
                new_network[const.UUID], self.vlan_name, self.vlan_id,
                device_ip=self.device_ip)
        new_port = db.port_create(new_network[const.UUID], const.PORT_UP)
        port_dict = self._cisco_ucs_plugin.create_port(
                            self.tenant_id, new_net_dict[const.NET_ID],
                            const.PORT_UP, new_port[const.UUID],
                            device_ip=self.device_ip,
                            ucs_inventory=self._ucs_inventory,
                            least_rsvd_blade_dict=self._ucs_inventory.\
                            get_least_reserved_blade())
        cdb.update_vlan_binding(new_network[const.UUID],
                                str(new_vlanid), new_vlan_name)
        self._cisco_ucs_plugin.plug_interface(
                           self.tenant_id, new_net_dict[const.NET_ID],
                           port_dict[const.PORTID], remote_interface_id,
                           device_ip=self.device_ip)

        port_bind = self._cisco_ucs_plugin.unplug_interface(
                           self.tenant_id, new_net_dict[const.NET_ID],
                           port_dict[const.PORTID], device_ip=self.device_ip)
        self.assertEqual(port_bind[const.VLANNAME], self.vlan_name)
        self.assertEqual(port_bind[const.VLANID], self.vlan_id)
        self.tearDownNetworkPortInterface(
                                   self.tenant_id, new_net_dict[const.NET_ID],
                                   new_port[const.UUID])

    def test_get_vlan_name_for_network(self):
        LOG.debug("UCSVICTestPlugin:test_get_vlan_name_for_network() called\n")
        new_network = db.network_create(self.tenant_id, self.net_name)
        cdb.add_vlan_binding(str(self.vlan_id), self.vlan_name,
                             new_network[const.UUID])
        vlan_bind_name = self._cisco_ucs_plugin._get_vlan_name_for_network(
                                    self.tenant_id, new_network[const.UUID])

        self.assertEqual(vlan_bind_name, self.vlan_name)

    def test_get_vlan_id_for_network(self):
        LOG.debug("UCSVICTestPlugin:test_get_vlan_id_for_network() called\n")
        new_network = db.network_create(self.tenant_id, self.net_name)
        cdb.add_vlan_binding(str(self.vlan_id), self.vlan_name,
                             new_network[const.UUID])
        vlan_bind_id = self._cisco_ucs_plugin._get_vlan_id_for_network(
                                    self.tenant_id, new_network[const.UUID])
        self.assertEqual(str(vlan_bind_id), self.vlan_id)

    def test_show_network_NetworkNotFound(self):
        self.assertRaises(exc.NetworkNotFound,
                          self._cisco_ucs_plugin.get_network_details,
                          self.tenant_id, self.net_id,
                          device_ip=self.device_ip)

    def test_delete_network_NetworkNotFound(self):
        self.assertRaises(exc.NetworkNotFound,
                          self._cisco_ucs_plugin.delete_network,
                          self.tenant_id, self.net_id,
                          device_ip=self.device_ip)

    def test_delete_port_PortNotFound(self):
        new_network = db.network_create(self.tenant_id, self.net_name)
        cdb.add_vlan_binding(str(self.vlan_id), self.vlan_name,
                             new_network[const.UUID])
        new_net_dict = self._cisco_ucs_plugin.create_network(
                self.tenant_id, new_network[const.NETWORKNAME],
                new_network[const.UUID], self.vlan_name, self.vlan_id,
                device_ip=self.device_ip)

        self.assertRaises(c_exc.PortVnicNotFound,
                          self._cisco_ucs_plugin.delete_port,
                          self.tenant_id, new_net_dict[const.NET_ID],
                          self.port_id, device_ip=self.device_ip,
                          ucs_inventory=self._ucs_inventory,
                          chassis_id=self.chassis_id, blade_id=self.blade_id,
                          blade_intf_distinguished_name=self.\
                          blade_intf_distinguished_name,
                          least_rsvd_blade_dict=self._ucs_inventory.\
                          get_least_reserved_blade())

        self.tearDownNetwork(self.tenant_id, new_net_dict[const.NET_ID])

    def tearDown(self):
        """Clear the test environment"""
        # Remove database contents
        db.clear_db()

    def tearDownNetwork(self, tenant_id, net_id):
        self._cisco_ucs_plugin.delete_network(tenant_id, net_id,
                                              device_ip=self.device_ip)

    def tearDownNetworkPort(self, tenant_id, net_id, port_id):
        self._cisco_ucs_plugin.delete_port(
                    tenant_id, net_id, port_id, device_ip=self.device_ip,
                    ucs_inventory=self._ucs_inventory,
                    chassis_id=self.chassis_id, blade_id=self.blade_id,
                    blade_intf_distinguished_name=self.\
                    blade_intf_distinguished_name,
                    least_rsvd_blade_dict=self._ucs_inventory.\
                    get_least_reserved_blade())
        self.tearDownNetwork(tenant_id, net_id)

    def tearDownNetworkPortInterface(self, tenant_id, net_id, port_id):
        self._cisco_ucs_plugin.unplug_interface(
                                   tenant_id, net_id, port_id,
                                   device_ip=self.device_ip)
        self.tearDownNetworkPort(tenant_id, net_id, port_id)
