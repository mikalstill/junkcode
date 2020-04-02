#!/usr/bin/python3

import json
import requests
import sys
import time


import urllib3
urllib3.disable_warnings()


BASE_URL = 'https://%s:9440'


class RestApiException(Exception):
    def __init__(self, status, body):
        self.status = status
        self.body = body


class RestApi(object):
    def __init__(self, hostname, username, password):
        self.base_url = BASE_URL % hostname
        self.api_url = self.base_url + '/api/nutanix/v3'
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
                                       self.api_url + '/clusters/list',
                                       json={'kind': 'cluster'})

    def get_vm(self, vm_uuid):
        return self._validated_request('get',
                                       self.api_url + '/vms/' + vm_uuid)

    def put_vm(self, vm_uuid, vm_info):
        return self._validated_request('put',
                                       self.api_url + '/vms/' + vm_uuid,
                                       json=vm_info)

    def get_vms(self):
        return self._validated_request('post',
                                       self.api_url + '/vms/list',
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

    # NOTE(mika): VMs don't always change power state when you ask them to.
    # So instead we have some poor man's retry logic to try and get them to
    # the state we want them to be in.
    def batch_set_power_with_retry(self, uuids, state):
        results = {}

        # First attempt
        for uuid in uuids:
            if r.set_power_state(uuid, state):
                results[uuid] = 'soft'
            else:
                results[uuid] = 'skip'

        time.sleep(60)

        # Test compliance
        dirty = False
        for uuid in uuids:
            actual = 'OFF'
            if r.is_powered_on(uuid):
                actual = 'ON'

            if actual != state:
                r.set_power_state(uuid, state)
                results[uuid] = 'hard'
                dirty = True

        # Verify
        if dirty:
            time.sleep(60)

            for uuid in uuids:
                actual = 'OFF'
                if r.is_powered_on(uuid):
                    actual = 'ON'

                if actual != state:
                    results[uuid] = 'fail'

        return results

    def get_vdi_url(self, uuid):
        vm_info = self.get_vm(uuid)
        return ('%(url)s/console/lib/noVNC/vnc_auto.html?'
                'path=vnc/vm/%(uuid)s/proxy&uuid=%(uuid)s&'
                'title=%(uuid)s&attached=false&hypervisorType=kKvm&'
                'controllerVm=false&vmName=%(uuid)s&noV1Access=false&'
                'useV3=true&isXi=false&clusterId=%(cluster)s'
                % {
                    'url': self.base_url,
                    'uuid': uuid,
                    'cluster': vm_info['spec']['cluster_reference']['uuid']
                })


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

    # Fetch a VDI URL
    print()
    print('Ubuntu VDI: %s' % r.get_vdi_url(ubuntu_vm_uuid))
    print()
    print('Centos VDI: %s' % r.get_vdi_url(centos_vm_uuid))

    # Validate power cycling
    print()
    print('---------------------------------------------')
    print()

    for count in range(5):
        # Power on
        results = r.batch_set_power_with_retry(
            [ubuntu_vm_uuid, centos_vm_uuid], 'ON'
        )
        print('Pass %3d  ON: ubuntu = %s, centos = %s'
              % (count, results[ubuntu_vm_uuid], results[centos_vm_uuid]))
        time.sleep(60)

        # Power off
        results = r.batch_set_power_with_retry(
            [ubuntu_vm_uuid, centos_vm_uuid], 'OFF'
        )
        print('Pass %3d OFF: ubuntu = %s, centos = %s'
              % (count, results[ubuntu_vm_uuid], results[centos_vm_uuid]))
        time.sleep(60)

        print('-------------------')
