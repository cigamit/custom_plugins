# Copyright (c) 2022 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)

__metaclass__ = type

DOCUMENTATION = '''
    name: controllerx
    plugin_type: inventory
    author:
      - Matthew Jones (@matburt)
      - Yunfan Zhang (@YunfanZhang42)
    short_description: Ansible dynamic inventory plugin for Ansible Controller.
    version_added: "2.7"
    description:
        - Reads inventories from Ansible Controller.
        - Supports reading configuration from both YAML config file and environment variables.
        - If reading from the YAML file, the file name must end with controllerx.(yml|yaml) or controllerx_inventory.(yml|yaml),
          the path in the command would be /path/to/controllerx_inventory.(yml|yaml). If some arguments in the config file
          are missing, this plugin will try to fill in missing arguments by reading from environment variables.
        - If reading configurations from environment variables, the path in the command must be @controllerx_inventory.
    options:
        plugin:
            description: the name of this plugin, it should always be set to 'controllerx'
                for this plugin to recognize it as it's own.
            env:
                - name: ANSIBLE_INVENTORY_ENABLED
            required: True
            choices: ['controllerx']
        host:
            description: The network address of your Ansible Controller host.
            type: string
            env:
                - name: CONTROLLER_HOST
            required: True
        username:
            description: The user that you plan to use to access inventories on Ansible Controller.
            type: string
            env:
                - name: CONTROLLER_USERNAME
            required: True
        password:
            description: The password for your Ansible Controller user.
            type: string
            env:
                - name: CONTROLLER_PASSWORD
            required: True
        inventory_name:
            description:
                - The ID of the Ansible Controller inventory that you wish to import.
                - This is allowed to be either the inventory primary key or its named URL slug.
                - Primary key values will be accepted as strings or integers, and URL slugs must be strings.
                - Named URL slugs follow the syntax of "inventory_name++organization_name".
            type: string
            env:
                - name: CONTROLLER_INVENTORY
            required: True
        hosts_filter:
            description:
                - a Python regex to filter hosts, only matching hosts will be left.
            type: string
            env:
                - name: HOSTS_FILTER
            required: False
        hostgroups_filter:
            description:
                - a Python regex to filter hosts, only hosts in matching groups will be left.
                - This regex is expected to be a sub-set of the groups_filter or results will be wrong.
            type: string
            env:
                - name: HOSTGROUPS_FILTER
            required: False
        groups_filter:
            description:
                - a Python regex to filter groups, only matching groups will be left.
                - If hostgroups_filter isn't defined, it acts as such, i.e. only hosts in those groups will remain.
                - Notice that empty groups won't be filtered out.
            type: string
            env:
                - name: GROUPS_FILTER
            required: False
        validate_certs:
            description: Specify whether Ansible should verify the SSL certificate of Ansible Controller host.
            type: bool
            default: True
            env:
                - name: CONTROLLER_VERIFY_SSL
            required: False
            aliases: [ verify_ssl ]
        include_metadata:
            description: Make extra requests to provide all group vars with metadata about the source Ansible Controller host.
            type: bool
            env:
                - name: METADATA_ENABLED
            default: False
            version_added: "2.8"
    Notes:
      - 2022-07-20 -- Scott Parker (@gearboxscott) Modified to work with AAP Controller.
      - 2022-07-22 -- Scott Parker (@gearboxscott) Modified to query inventory by name.
'''

EXAMPLES = '''
# Before you execute the following commands, you should make sure this file is in your plugin path,
# and you enabled this plugin.

# Example for using controllerx_inventory.yml file

plugin: controllerx
host: your_ansible_controller_server_network_address
username: your_ansible_controller_username
password: your_ansible_controller_password
inventory_name: the_name_of_targeted_ansible_controller_inventory_to_be_filtered
hosts_filter: a Python regex to filter hosts
hostgroups_filter: a Python regex to filter hosts based on their group(s)
groups_filter: a Python regex to filter groups (and hosts if hostgroups_filter isn't defined)
# Then you can run the following command.
# If some of the arguments are missing, Ansible will attempt to read them from environment variables.
# ansible-inventory -i /path/to/controllerx_inventory.yml --list

For example, the following filters would only keep hosts containing the `important` string in their
hostname and being in the `meta-keep-them` group, whereas all groups starting with `meta-` or ending
with `nova` will be kept:

    hosts_filter: important
    hostgroups_filter: "^meta-keep-them$"
    groups_filter: "^meta-.*|nova$"

# Example for reading from environment variables:

# Set environment variables:
# export CONTROLLER_HOST=YOUR_CONTROLLER_HOST_ADDRESS
# export CONTROLLER_USERNAME=YOUR_CONTROLLER_USERNAME
# export CONTROLLER_PASSWORD=YOUR_CONTROLLER_PASSWORD
# export CONTROLLER_INVENTORY=THE_ID_OF_TARGETED_INVENTORY
# Read the inventory specified in CONTROLLER_INVENTORY from Ansible Controller, and list them.
# The inventory path must always be @controllerx_inventory if you are reading all settings from environment variables.
# ansible-inventory -i @controllerx_inventory --list
'''

import re
import os
import json
from ansible.module_utils import six
from ansible.module_utils.urls import Request, urllib_error, ConnectionError, socket, httplib
from ansible.module_utils._text import to_text, to_native
from ansible.errors import AnsibleParserError, AnsibleOptionsError
from ansible.plugins.inventory import BaseInventoryPlugin
from ansible.config.manager import ensure_type

# Python 2/3 Compatibility
try:
    from urlparse import urljoin
except ImportError:
    from urllib.parse import urljoin


class InventoryModule(BaseInventoryPlugin):
    NAME = 'controllerx'
    # Stays backward compatible with Controller inventory script.
    # If the user supplies '@controller_inventory' as path, the plugin will read from environment variables.
    no_config_file_supplied = False

    def make_request(self, request_handler, controller_url):
        """Makes the request to given URL, handles errors, returns JSON
        """
        try:
            response = request_handler.get(controller_url)
        except (ConnectionError, urllib_error.URLError, socket.error, httplib.HTTPException) as e:
            n_error_msg = 'Connection to remote host failed: {err}'.format(err=to_native(e))
            # If Controller gives a readable error message, display that message to the user.
            if callable(getattr(e, 'read', None)):
                n_error_msg += ' with message: {err_msg}'.format(err_msg=to_native(e.read()))
            raise AnsibleParserError(n_error_msg)

        # Attempt to parse JSON.
        try:
            return json.loads(response.read())
        except (ValueError, TypeError) as e:
            # If the JSON parse fails, print the ValueError
            raise AnsibleParserError('Failed to parse json from host: {err}'.format(err=to_native(e)))

    def verify_file(self, path):
        if path.endswith('@controllerx_inventory'):
            self.no_config_file_supplied = True
            return True
        elif super(InventoryModule, self).verify_file(path):
            return path.endswith(('controllerx_inventory.yml', 'controllerx_inventory.yaml', 'controllerx.yml', 'controllerx.yaml'))
        else:
            return False

    def parse(self, inventory, loader, path, cache=True):
        super(InventoryModule, self).parse(inventory, loader, path)
        if not self.no_config_file_supplied and os.path.isfile(path):
            self._read_config_data(path)
        # Read inventory from Controller server.
        # Note the environment variables will be handled automatically by InventoryManager.
        controller_host = self.get_option('host')
        if not re.match('(?:http|https)://', controller_host):
            controller_host = 'https://{controller_host}'.format(controller_host=controller_host)

        request_handler = Request(url_username=self.get_option('username'),
                                  url_password=self.get_option('password'),
                                  force_basic_auth=True,
                                  validate_certs=self.get_option('validate_certs'))

        # validate type of inventory_name because we allow two types as special case
        inventory_name = self.get_option('inventory_name')
        if isinstance(inventory_name, str):
            inventory_id = to_text(inventory_name, nonstring='simplerepr')
        else:
            try:
                inventory_name = ensure_type(inventory_name, 'str')
            except ValueError as e:
                raise AnsibleOptionsError(
                    'Invalid type for configuration option inventory_name, '
                    'not integer, and cannot convert to string: {err}'.format(err=to_native(e))
                )

        # get the inventory id by name
        inventory_name = inventory_name.replace(' ', '%20')
        inventory_name_url = '/api/v2/inventories/?name={inv_name}'.format(inv_name=inventory_name)
        inventory_name_url = urljoin(controller_host, inventory_name_url)
        inventory_data = self.make_request(request_handler, inventory_name_url)
        inventory_id = str( inventory_data['results'][0]['id'])

        inventory_id = inventory_id.replace('/', '')
        inventory_url = '/api/v2/inventories/{inv_id}/script/?hostvars=1&controllervars=1&all=1'.format(inv_id=inventory_id)
        inventory_url = urljoin(controller_host, inventory_url)

        # gather and compile the different filter options
        hosts_filter = self.get_option('hosts_filter')
        if hosts_filter:
            hosts_pattern = re.compile(hosts_filter)
        else:
            hosts_pattern = None
        hostgroups_filter = self.get_option('hostgroups_filter')
        if hostgroups_filter:
            hostgroups_pattern = re.compile(hostgroups_filter)
        else:
            hostgroups_pattern = None
        groups_filter = self.get_option('groups_filter')
        if groups_filter:
            groups_pattern = re.compile(groups_filter)
        else:
            groups_pattern = None

        inventory = self.make_request(request_handler, inventory_url)
        allowed_hosts = set()
        allowed_groups = set()
        # To start with, create all the groups, and identify allowed hosts/groups.
        for group_name, group_content in six.iteritems(inventory):
            if groups_pattern and not groups_pattern.search(group_name) and group_name != 'all':
                continue
            if group_name != '_meta':
                allowed_groups.add(group_name)
                self.inventory.add_group(group_name)
                if not hostgroups_pattern or hostgroups_pattern.search(group_name):
                    if not hosts_pattern:  # add all hosts at once
                        allowed_hosts.update(group_content.get('hosts', []))
                    else:   # loop through the hosts and filter them
                        for host_name in group_content.get('hosts', []):
                            if hosts_pattern.search(host_name):
                                allowed_hosts.add(host_name)

        # Then, create all hosts and add the host vars.
        all_hosts = inventory['_meta']['hostvars']
        for host_name, host_vars in six.iteritems(all_hosts):
            if host_name not in allowed_hosts:
                continue
            self.inventory.add_host(host_name)
            for var_name, var_value in six.iteritems(host_vars):
                self.inventory.set_variable(host_name, var_name, var_value)

        # Lastly, create to group-host and group-group relationships, and set group vars.
        for group_name, group_content in six.iteritems(inventory):
            if group_name not in allowed_groups:
                continue
            if group_name != 'all' and group_name != '_meta':
                # First add hosts to groups
                for host_name in group_content.get('hosts', []):
                    if host_name not in allowed_hosts:
                        continue
                    self.inventory.add_host(host_name, group_name)
                # Then add the parent-children group relationships.
                for child_group_name in group_content.get('children', []):
                    if child_group_name not in allowed_groups:
                        continue
                    self.inventory.add_child(group_name, child_group_name)
            # Set the group vars. Note we should set group var for 'all', but not '_meta'.
            if group_name != '_meta':
                for var_name, var_value in six.iteritems(group_content.get('vars', {})):
                    self.inventory.set_variable(group_name, var_name, var_value)

        # Fetch extra variables if told to do so
        if self.get_option('include_metadata'):
            config_url = urljoin(controller_host, '/api/v2/config/')
            config_data = self.make_request(request_handler, config_url)
            server_data = {}
            server_data['license_type'] = config_data.get('license_info', {}).get('license_type', 'unknown')
            for key in ('version', 'ansible_version'):
                server_data[key] = config_data.get(key, 'unknown')
            self.inventory.set_variable('all', 'controller_metadata', server_data)

        # Clean up the inventory.
        self.inventory.reconcile_inventory()