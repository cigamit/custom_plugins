# Custom Plugins

Custom Plugins is a project for different custom Ansible Plugins that can be used by Ansible and Ansible Controller.
This plugin repository will work with execution environments found in Ansible Automation Platform 1.x and 2.x and the command-line.

Current Plugins in this Repository:

| Plugin | Type | Description |
| :--- | :--- | :-- |
| `controllerx` | inventory | Ansible dynamic inventory plugin for Ansible Controller's Inventories.

## Requirements
---

This section will list out requirements for plugins as they are needed or required.

### The `ansible.cfg` for Plugins
---

Ansible will use `ansible.cfg` to know where to find plugins in the repository and enable them. Listed below is the `ansible.cfg` for this repository:

```ini
[defaults]
host_key_checking = False
inventory_plugins = ./

[inventory]
enable_plugins = yaml, controllerx, auto
```

Settings Explained:

| Setting | Description |
| :-- | :-- |
| `inventory_plugins = ./` | where to find the inventory plugins in this repository.
| `enable_plugins = yaml, controllerx, auto` | enable the plugins needed under the `[inventory]` section.

> NOTE and WARNING | Do not filter this `ansible.cfg` with `.gitignore`. It has be included in the repository.


## Plugins and Their Variables
---

Every plugin comes variables or settings that are needed to make it work correctly.

### The `controllerx` Inventory Plugin Variables
---

| Variable Name | Environment Varible | Type | Default | Required | Description |
| :-- | :-- | :-- | :-- | :-- | :-- |
| `plugin:` | `ANSIBLE_INVENTORY_ENABLED`  | string | true | `controllerx` | the name of this plugin, it should always be set to 'controllerx' for this plugin to recognize it as it's own. |
| `host:` | `CONTROLLER_HOST` | string | true | none | The hostname or IP Address of your Ansible Controller host |
| `username:` | `CONTROLLER_USERNAME` | string | true | none | Ansible Controller user account |
| `password:` | `CONTROLLER_PASSWORD` | string | true | none | Ansible Controller user account's password |
| `validate_certs:` | `CONTROLLER_VERIFY_SSL` | boolean | false | `true` | Specify whether Ansible should verify the SSL certificate of Ansible Controller host. |
| `include_metadata:` | `METADATA_ENABLED` | boolean | false | `false` | Make extra requests to provide all group vars with metadata about the source Ansible Controller host. |
| `inventory_name:` | `CONTROLLER_INVENTORY` | raw | true | none | The name of the existing Ansible Controller's Inventory to be filtered |
| `hosts_filter:` | `HOSTS_FILTER` | string | false | none | A Python regex to filter hosts, only matching hosts will be left |
| `hostgroups_filter:` | `HOSTGROUPS_FILTER` | string | false | none | A Python regex to filter hosts, only hosts in matching groups will be left.<br>This regex is expected to be a sub-set of the groups_filter or results will be wrong. |
| `groups_filter:` | `GROUPS_FILTER` | string | false | none | A Python regex to filter groups, only matching groups will be left.<br>If hostgroups_filter isn't defined, it acts as such, i.e. only hosts in those groups will remain.<br>Notice that empty groups won't be filtered out.
 |

The environment variable in the table above can be set using the `export` shell operative for this plugin.

```bash
export ANSIBLE_INVENTORY_ENABLED='controllerx'
export CONTROLLER_HOST='redacted'
export CONTROLLER_USERNAME='redacted'
export CONTROLLER_PASSWORD='redacted'
export CONTROLLER_VERIFY_SSL='false'
export CONTROLLER_INVENTORY='name of the inventory to be filtered'
export METADATA_ENABLED='true'
export GROUP_FILTER='platform_linux
```

#### The `controllerx` Usages
---

Before you execute the following commands, make sure this file is in your plugin path, and enabled this plugin.

* Example for using `controllerx_inventory.yml` file

```ini
plugin: controllerx
host: your_ansible_controller_server_network_address
username: your_ansible_controller_username
password: your_ansible_controller_password
inventory_name: the_ID_of_targeted_ansible_controller_inventory
hosts_filter: a Python regex to filter hosts
hostgroups_filter: a Python regex to filter hosts based on their group(s)
groups_filter: a Python regex to filter groups (and hosts if hostgroups_filter isn't defined)
```

Then run the following command. If some of the arguments are missing, Ansible will attempt to read them from environment variables.

```bash
ansible-inventory -i /path/to/controllerx_inventory.yml --list
```

* For example, the following filters would only keep hosts containing the `important` string in their
hostname and being in the `meta-keep-them` group, whereas all groups starting with `meta-` or ending
with `nova` will be kept:

```yaml
hosts_filter: important
hostgroups_filter: "^meta-keep-them$"
groups_filter: "^meta-.*|nova$"
```

* Example for reading from environment variables

```bash
# export ANSIBLE_INVENTORY_ENABLED='controllerx'
# export CONTROLLER_HOST=YOUR_CONTROLLER_HOST_ADDRESS
# export CONTROLLER_USERNAME=YOUR_CONTROLLER_USERNAME
# export CONTROLLER_PASSWORD=YOUR_CONTROLLER_PASSWORD
# export CONTROLLER_INVENTORY=THE_ID_OF_TARGETED_INVENTORY
# export CONTROLLER_VERIFY_SSL='false'
# export METADATA_ENABLED='true'
# export GROUP_FILTER=THE_ID_OF_CONTROLLERS_INVENTORY
```

  Read the inventory specified in `CONTROLLER_INVENTORY` from Ansible Controller, and list them.  The inventory path must always be @controllerx_inventory if you are reading all settings from environment variables.

```bash
# override the ansible.cfg inventory_plugins variable
export DEFAULT_INVENTORY_PLUGIN_PATH='relative location of inventory_plugins, either ./ or ../' 
ansible-inventory -i @controllerx_inventory --list
```
#### The `controllerx` Inventory Plugin Usage in Ansible Controller
---

The `controllerx` plugin can be used in the Ansible Controller directly to emulate using Smart Inventories. This emulation will pull in group variables that current Smart Inventories do not support. The following is the step-by-step process on how to create inventory filters in Ansible Controller so they are updated when inventories are updated.

* Create a project in Ansible Controller to pull in the `custom_plugins` repository:

```yaml
projects:
  - name: custom_plugins
    description: ""
    local_path: _146__inventory_filter
    scm_type: git
    scm_url: https://<redacted>/custom_plugins.git
    scm_branch: ""
    scm_refspec: ""
    scm_clean: true
    scm_track_submodules: false
    scm_delete_on_update: true
    timeout: 0
    scm_update_on_launch: true
    scm_update_cache_timeout: 0
    allow_override: false
    default_environment: null
    credential:
      organization:
        name: Default
        type: organization
      name: <SCM Credential>
      credential_type:
        name: Source Control
        kind: scm
        type: credential_type
      type: credential
    organization:
      name: Default
      type: organization
    related:
      schedules: []
      notification_templates_started: []
      notification_templates_success: []
      notification_templates_error: []
    natural_key:
      organization:
        name: Default
        type: organization
      name: custom_plugins
      type: project
```

* Create a Custom Credential Type in Ansible Controller with following:

```yaml
credential_types:
  - name: inventory_filter
    description: ""
    kind: cloud
    inputs:
      fields:
        - id: hostname
          type: string
          label: Controller Hostname
          default: <controller hostname or ip address>
        - id: username
          type: string
          label: Controller Username
          default: admin
        - id: password
          type: string
          label: Controller Password
          secret: true
        - id: ssl_verify
          type: boolean
          label: Verify SSL
          default: true
        - id: hosts_filter
          type: string
          label: Hosts Filter
        - id: hostgroups_filter
          type: string
          label: Hosts Groups Filter
        - id: groups_filter
          type: string
          label: Groups Filter
        - id: include_metadata
          type: boolean
          label: Include Metadata
          default: true
        - id: inventory_name
          type: string
          label: Inventory ID
      required:
        - username
        - password
        - hostname
        - ssl_verify
    injectors:
      env:
        HOSTS_FILTER: '{{ hosts_filter }}'
        GROUPS_FILTER: '{{ groups_filter }}'
        CONTROLLER_HOST: '{{ hostname }}'
        METADATA_ENABLE: '{{ include_metadata }}'
        HOSTGROUPS_FILTER: '{{ hostgroups_filter }}'
        CONTROLLER_PASSWORD: '{{ password }}'
        CONTROLLER_USERNAME: '{{ username }}'
        CONTROLLER_INVENTORY: '{{ inventory_name }}'
        CONTROLLER_VERIFY_SSL: '{{ ssl_verify }}'
    natural_key:
      name: inventory_filter
      kind: cloud
      type: credential_type
```

* Create a Credential with the name that describes the filter like `platform_linux_inventory_filter` in Ansible Controller with following:

```yaml
credentials:
  - name: platform_linux_inventory_filter
    description: ""
    inputs:
      hostname: <controller hostname or ip address>
      password: <redacted>
      username: <redacted>
      ssl_verify: false
      hosts_filter: ""
      inventory_name: "<name of existing inventory in Ansible Controller to be filtered"
      groups_filter: platform_linux
      include_metadata: true
      hostgroups_filter: ""
    organization:
      name: Default
      type: organization
    credential_type:
      name: inventory_filter
      kind: cloud
      type: credential_type
    natural_key:
      organization:
        name: Default
        type: organization
      name: platform_linux_inventory_filter
      credential_type:
        name: inventory_filter
        kind: cloud
        type: credential_type
      type: credential
```

* Create a inventory with a name that describes the filter like `AWS Filtered Platform Linux` in Ansible Controller:

```yaml
inventory:
  - name: AWS Filtered Platform Linux
    description: ""
    kind: ""
    host_filter: null
    organization:
      name: Default
      type: organization
```

* Create a inventory source with same name as the project `custom_plugins` in Ansible Controller:

```yaml
inventory_sources:
  - name: custom_plugins
    description: ""
    source: scm
    source_path: inventories/variable_controllerx_inventory.yml
    source_vars: '---'
    enabled_var: ""
    enabled_value: ""
    host_filter: ""
    overwrite: false
    overwrite_vars: false
    timeout: 0
    verbosity: 1
    execution_environment: null
    update_on_launch: false
    update_cache_timeout: 0
    update_on_project_update: true
    credential:
      organization:
        name: Default
        type: organization
      name: platform_linux_inventory_filter
      credential_type:
        name: inventory_filter
        kind: cloud
        type: credential_type
      type: credential
    inventory:
      organization:
        name: Default
        type: organization
      name: AWS Filtered Platform Linux
      type: inventory
    source_project:
      organization:
        name: Default
        type: organization
      name: custom_plugins
      type: project
    related:
      schedules: []
      notification_templates_started: []
      notification_templates_success: []
      notification_templates_error: []
    natural_key:
      name: custom_plugins
      inventory:
        organization:
          name: Default
          type: organization
        name: AWS Filtered Platform Linux
        type: inventory
      type: inventory_source

```

* Sync the inventory source and check the hosts in the inventory `AWS Filtered Platform Linux`, it should be populated with host that in the group called `platform_linux`

* This inventory is now available to be used in Job Templates for running playbooks against it.

### The `custom_plugins` Directory Structure

The following is directory structure for the `custom_plugins` respository:

```yaml
.
├── ansible.cfg
├── inventories
│   └── variable_controllerx_inventory.yml
├── inventory_plugins
│   └── controllerx.py
├── README.md
└── test
    ├── controllerx_inventory
    ├── controllerx_inventory.yml
    └── test.sh
```


## Ansible Documentation Supporting Custom Plugins
* https://docs.ansible.com/ansible/latest/plugins/inventory.html
* https://docs.ansible.com/ansible/latest/dev_guide/developing_inventory.html#developing-inventory
* https://docs.ansible.com/ansible/latest/plugins/inventory.html#inventory-plugins
* https://docs.ansible.com/ansible/latest/dev_guide/developing_plugins.html#developing-plugins
## License
---

GNU General Public License v3.0 or later.

## Author Information
---

- Scott Parker (sparker@redhat.com) -- Created README.md and modified original `towerx` plugin to work with controller, now called `controllerx`.