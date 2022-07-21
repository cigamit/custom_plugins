#!/bin/bash -x
export ANSIBLE_INVENTORY_ENABLED='controllerx'
export CONTROLLER_HOST='redacted'
export CONTROLLER_USERNAME='redacted'
export CONTROLLER_PASSWORD='redacted'
export CONTROLLER_VERIFY_SSL='false'
export CONTROLLER_INVENTORY='6'
export METADATA_ENABLED='true'
export GROUP_FILTER='platform_linux'

# override the ansible.cfg inventory_plugins variable
export DEFAULT_INVENTORY_PLUGIN_PATH='../' 

ansible-inventory -i @controllerx_inventory --graph -y