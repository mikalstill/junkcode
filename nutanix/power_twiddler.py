#!/usr/bin/python3

import json
import requests
import sys
import time


import urllib3
urllib3.disable_warnings()


BASE_URL = 'https://%s:9440/PrismGateway/services/rest/v2.0'


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

    def get_cluster_info(self):
        url = self.url + '/cluster'
        r = self.session.get(url)
        if r.status_code != 200:
            return r.status_code, r.text
        return r.status_code, r.json()

    def get_vm(self, vm_uuid):
        url = self.url + '/vms/' + vm_uuid
        r = self.session.get(url)
        if r.status_code != 200:
            return r.status_code, r.text
        return r.status_code, r.json()

    def get_vms(self):
        url = self.url + '/vms/'
        r = self.session.get(url)
        if r.status_code != 200:
            return r.status_code, r.text
        return r.status_code, r.json()

    def set_power(self, vm_uuid, power_state):
        url = self.url + '/vms/' + vm_uuid + '/set_power_state/'
        body = {
            'transition': power_state
        }
        r = self.session.post(url, json=body)
        if r.status_code != 200:
            return r.status_code, r.text
        return r.status_code, r.json()


if __name__ == '__main__':
    r = RestApi('192.168.10.30', sys.argv[1], sys.argv[2])

    # Discover basic cluster information
    status, cluster_info = r.get_cluster_info()
    if status != 200:
        print('Failed to fetch cluster info: %s' % status)
        sys.exit(1)

    print('Cluster is:')
    print('    UUID: %s' % cluster_info['cluster_uuid'])
    print('    Version: %s' % cluster_info['version'])

    # Discover all VMs
    status, vms = r.get_vms()
    if status != 200:
        print('Failed to fetch VMs: %s (%s)' %(status, vms))
        sys.exit(1)

    for vm in vms['entities']:
        print()
        print('VM %s, %s on %s' %(vm['uuid'], vm['vmName'], vm['hostName']))
        print('    vCPUs %d, Memory %.02f GB, powered %s'
              %(vm['numVCpus'],
                vm['memoryCapacityInBytes'] / 1024 / 1024 / 1024,
                vm['powerState']))
        for ip in vm['ipAddresses']:
            print('    IP: %s' % ip)
        for nic in vm['virtualNicUuids']:
            print('    NIC: %s' % nic)
        if vm.get('nutanixVirtualDiskUuids'):
            for disk in vm.get('nutanixVirtualDiskUuids', []):
                print('    Disk: %s' % disk)

    # Pause a single VM
    print()
    print('---------------------------------------------')
    print()
    vm_uuid = '27a7dd0a-fec4-4918-98d7-634955ba81c6'

    status, vm_info = r.get_vm(vm_uuid)
    if status != 200:
        print('Failed to get VM info: %s (%s)' %(status, vm_info))
        sys.exit(1)
    print('%s is %s' %(vm_uuid, vm_info['powerState']))

    status, output = r.set_power(vm_uuid, 'OFF')
    if status != 200:
        print('Failed to set power state: %s (%s)' %(status, output))
        sys.exit(1)

    done = False
    while not done:
        time.sleep(1)
        status, vm_info = r.get_vm(vm_uuid)
        if status != 200:
            print('Failed to get VM info after state change: %s' % status)
            sys.exit(1)
        print('%s is %s' %(vm_uuid, vm_info['powerState']))

        done = vm_info['powerState'] == 'OFF'
