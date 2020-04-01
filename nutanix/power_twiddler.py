#!/usr/bin/python3

import json
import requests
import sys
import time


import urllib3
urllib3.disable_warnings()


BASE_URL = 'https://%s:9440/api/nutanix/v3'


class RestApiException(Exception):
    def __init__(self, status, body):
        self.status = status
        self.body = body


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

    def _validated_request(self, method, url, json=None):
        r = self.session.request(method, url, json=json)
        if not r.status_code in [200, 202]:
            raise RestApiException(r.status_code, r.text)
        return r.json()

    def get_clusters(self):
        return self._validated_request('post',
                                       self.url + '/clusters/list',
                                       json={'kind': 'cluster'})

    def get_vm(self, vm_uuid):
        return self._validated_request('get',
                                       self.url + '/vms/' + vm_uuid)

    def put_vm(self, vm_uuid, vm_info):
        return self._validated_request('put',
                                       self.url + '/vms/' + vm_uuid,
                                       json=vm_info)

    def get_vms(self):
        return self._validated_request('post',
                                       self.url + '/vms/list',
                                       json={'kind': 'vm'})

    # Meta helper thingies
    def set_power_state(self, vm_uuid, state):
        vm_info = self.get_vm(vm_uuid)
        if vm_info['spec']['resources']['power_state'] == state:
            return False

        del vm_info['status']
        vm_info['spec']['resources']['power_state'] = state
        self.put_vm(vm_uuid, vm_info)
        return True

    def is_powered_on(self, vm_uuid):
        return self.get_vm(vm_uuid)['spec']['resources']['power_state'] == 'ON'


if __name__ == '__main__':
    r = RestApi('192.168.10.30', sys.argv[1], sys.argv[2])

    # Discover basic cluster information
    for cluster in r.get_clusters()['entities']:
        print('Available cluster:')
        print('    Name: %s' % cluster['spec']['name'])
        print('    Version: %s' %
              cluster['spec']['resources']['config']['software_map']['NOS']['version'])

    # Discover all VMs
    for vm in r.get_vms()['entities']:
        print()
        print('VM %s (%s) owned by %s' % (
            vm['metadata']['uuid'],
            vm['spec']['name'],
            vm['metadata'].get('owner_reference', {}).get('name')))
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

        if vm['spec']['name'] == 'mikal ubuntu':
            ubuntu_vm_uuid = vm['metadata']['uuid']
        if vm['spec']['name'] == 'mikal centos':
            centos_vm_uuid = vm['metadata']['uuid']

    # Validate power cycling
    print()
    print('---------------------------------------------')
    print()

    count = 1
    while True:
        # Power everything up
        tests = {'centos': 'skip', 'ubuntu': 'skip'}

        if r.set_power_state(ubuntu_vm_uuid, 'ON'):
            tests['ubuntu'] = 'soft'
        if r.set_power_state(centos_vm_uuid, 'ON'):
            tests['centos'] = 'soft'
        time.sleep(60)

        # Test compliance
        dirty = False
        if not r.is_powered_on(ubuntu_vm_uuid):
            r.set_power_state(ubuntu_vm_uuid, 'ON')
            tests['ubuntu'] = 'hard'
            dirty = True
        if not r.is_powered_on(centos_vm_uuid):
            r.set_power_state(centos_vm_uuid, 'ON')
            tests['centos'] = 'hard'
            dirty = True

        if dirty:
            time.sleep(60)
            if not r.is_powered_on(ubuntu_vm_uuid):
                tests['ubuntu'] = 'fail'
            if not r.is_powered_on(centos_vm_uuid):
                tests['centos'] = 'fail'

        print('Pass %3d  ON: ubuntu = %s, centos = %s'
              % (count, tests['ubuntu'], tests['centos']))
        time.sleep(60)

        # Power everything off
        tests = {'centos': 'skip', 'ubuntu': 'skip'}

        if r.set_power_state(ubuntu_vm_uuid, 'OFF'):
            tests['ubuntu'] = 'soft'
        if r.set_power_state(centos_vm_uuid, 'OFF'):
            tests['centos'] = 'soft'
        time.sleep(120)

        # Test compliance
        dirty = False
        if r.is_powered_on(ubuntu_vm_uuid):
            r.set_power_state(ubuntu_vm_uuid, 'OFF')
            tests['ubuntu'] = 'hard'
            dirty = True
        if r.is_powered_on(centos_vm_uuid):
            r.set_power_state(centos_vm_uuid, 'OFF')
            tests['centos'] = 'hard'
            dirty = True

        if dirty:
            time.sleep(60)
            if r.is_powered_on(ubuntu_vm_uuid):
                tests['ubuntu'] = 'fail'
            if r.is_powered_on(centos_vm_uuid):
                tests['centos'] = 'fail'

        print('Pass %3d OFF: ubuntu = %s, centos = %s'
              % (count, tests['ubuntu'], tests['centos']))

        count += 1
        print('-------------------')
        time.sleep(120)
