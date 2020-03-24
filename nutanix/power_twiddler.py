#!/usr/bin/python3

import json
import requests
import sys
import time


import urllib3
urllib3.disable_warnings()


BASE_URL = 'https://%s:9440/api/nutanix/v3'


class RestApi(object):
    def __init__(self, hostname, username, password):
        self.url = BASE_URL % hostname
        self.session = self._get_session(username, password)

    def _get_session(self, username, password):
        s = requests.Session()
        s.auth = (username, password)
        s.verify = False
        s.headers.update({'Content-Type': 'application/json; charset=utf-8'})
        return s

    def get_clusters(self):
        url = self.url + '/clusters/list'
        r = self.session.post(url, json={'kind': 'cluster'})
        if r.status_code != 200:
            return r.status_code, r.text
        return r.status_code, r.json()

    def get_vm(self, vm_uuid):
        url = self.url + '/vms/' + vm_uuid
        r = self.session.get(url)
        if r.status_code != 200:
            return r.status_code, r.text
        return r.status_code, r.json()

    def put_vm(self, vm_info):
        url = self.url + '/vms/' + vm_uuid
        r = self.session.put(url, json=vm_info)
        if r.status_code != 200:
            return r.status_code, r.text
        return r.status_code, r.json()

    def get_vms(self):
        url = self.url + '/vms/list'
        r = self.session.post(url, json={'kind': 'vm'})
        if r.status_code != 200:
            return r.status_code, r.text
        return r.status_code, r.json()


if __name__ == '__main__':
    r = RestApi('192.168.10.30', sys.argv[1], sys.argv[2])

    # Discover basic cluster information
    status, cluster_info = r.get_clusters()
    if status != 200:
        print('Failed to fetch cluster info: %s' % status)
        sys.exit(1)

    for cluster in cluster_info['entities']:
        print('Available cluster:')
        print('    Name: %s' % cluster['spec']['name'])
        print('    Version: %s' %
              cluster['spec']['resources']['config']['software_map']['NOS']['version'])

    # Discover all VMs
    status, vms = r.get_vms()
    if status != 200:
        print('Failed to fetch VMs: %s (%s)' % (status, vms))
        sys.exit(1)

    for vm in vms['entities']:
        print()
        print('VM %s (%s) owned by %s' % (
            vm['metadata']['uuid'],
            vm['spec']['name'],
            vm['metadata']['owner_reference']['name']))
        print('    vCPUs %dx%d, Memory %.02f MiB, powered %s'
              % (vm['spec']['resources']['num_sockets'],
                 vm['spec']['resources']['num_vcpus_per_socket'],
                 vm['spec']['resources']['memory_size_mib'],
                 vm['spec']['resources']['power_state']))
        for nic in vm['spec']['resources']['nic_list']:
            print('    NIC: %s with MAC %s' %
                  (nic['uuid'], nic['mac_address']))
        for disk in vm['spec']['resources']['disk_list']:
            print('    Disk: %s is %s MiB' %
                  (disk['uuid'], disk.get('disk_size_mib', 0)))

    # Power cycle a single VM
    print()
    print('---------------------------------------------')
    print()
    vm_uuid = '27a7dd0a-fec4-4918-98d7-634955ba81c6'

    status, vm_info = r.get_vm(vm_uuid)
    if status != 200:
        print('Failed to get VM info: %s (%s)' % (status, vm_info))
        sys.exit(1)
    print('%s is %s' % (vm_uuid, vm_info['spec']['resources']['power_state']))

    if vm_info['spec']['resources']['power_state'] == 'OFF':
        print('VM is already powered off, aborting...')
        sys.exit(1)

    print('...powering off VM')
    del vm_info['status']
    vm_info['spec']['resources']['power_state'] = 'OFF'
    status, vm_info = r.put_vm(vm_info)
    if status != 202:
        print('Failed to put VM info: %s (%s)' % (status, vm_info))
        sys.exit(1)

    print('...waiting for VM to be powered off')
    done = False
    while not done:
        time.sleep(1)
        status, vm_info = r.get_vm(vm_uuid)
        if status != 200:
            print('Failed to get VM info after state change: %s' % status)
            sys.exit(1)
        print('%s is %s' %
              (vm_uuid, vm_info['spec']['resources']['power_state']))

        done = vm_info['spec']['resources']['power_state'] == 'OFF'
