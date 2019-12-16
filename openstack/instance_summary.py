#!/usr/bin/python

# Summarize openstack instances so I can get a feel for the cost of
# transitioning workloads.

import argparse
import csv
from io import StringIO
import json
import os
from prettytable import PrettyTable
import sys
import urllib.error
import urllib.request


args = None


def _make_req(method, url, data, headers):
    if data:
        posted = json.dumps(data, indent=4, sort_keys=True).encode()
    else:
        posted = None

    if args.verbose:
        print('%s %s' % (method, url))
        for header in headers:
            print('    header: %s=%s' %(header, headers[header]))

        if data:
            for line in posted.decode().split('\n'):
                print('    posted: %s' % line)

        print()

    req = urllib.request.Request(url=url, method=method, data=posted,
                                 headers=headers)

    try:
        with urllib.request.urlopen(req) as res:
            out = json.loads(res.read())

            if args.verbose:
                print('    result: code = %d' % res.code)
                for header in headers:
                    print('    header: %s=%s' %(header, headers[header]))
                for line in json.dumps(out, indent=4, sort_keys=True).split('\n'):
                    print('  returned: %s' % line)

                print()

            return res.headers, out
    except urllib.error.HTTPError as e:
        if args.verbose:
            print('    result: code = %d' % e.code)
            print('     error: reason = %s' % e.reason)
            print()
        raise e


def getKeystoneVersion():
    headers = {'Content-Type': 'application/json'}

    rhead, data = _make_req('GET', os.environ.get('OS_AUTH_URL'), None, headers)
    return data.get('version').get('id')


def getKeystoneV2Token(tenant=None):
    headers = {'Content-Type': 'application/json'}
    url = '%s/tokens' % os.environ.get('OS_AUTH_URL')

    if not tenant:
        tenant = os.environ.get('OS_TENANT_NAME')

    data = {
        'auth': {
            'tenantName': tenant,
            'passwordCredentials': {
                'username': os.environ.get('OS_USERNAME'),
                'password': os.environ.get('OS_PASSWORD'),
            },
        }
    }

    rhead, data = _make_req('POST', url, data, headers)
    return data.get('access').get('token'), data.get('access').get('serviceCatalog')


def getKeystoneV3Token(scope=None):
    headers = {'Content-Type': 'application/json'}
    url = '%s/auth/tokens' % os.environ.get('OS_AUTH_URL')
    data = {
        'auth': {
            'identity': {
                'methods': [
                    'password'
                ],
                'password': {
                    'user': {
                        'name': os.environ.get('OS_USERNAME'),
                        'domain': {
                            'name': 'Default'
                        },
                        'password': os.environ.get('OS_PASSWORD')
                    }
                }
            },
        }
    }

    if not scope:
        data['auth']['scope'] = {
            'system': {
                'all': True
            }
        }
    else:
        data['auth']['scope'] = {
            'project': {
                'id': scope
            }
        }

    rhead, data = _make_req('POST', url, data, headers)
    return rhead.get('X-Subject-Token'), data.get('token')


def getKeystoneV3Projects(token, user):
    headers = {
        'Content-Type': 'application/json',
        'X-Auth-Token': token
    }
    url = '%s/users/%s/projects' % (os.environ.get('OS_AUTH_URL'), user)

    rhead, data = _make_req('GET', url, None, headers)
    return data.get('projects')


def getKeystoneV3Catalog(token):
    headers = {
        'Content-Type': 'application/json',
        'X-Auth-Token': token
    }

    # Keystone v3 requires us to lookup services and then their
    # endpoints
    url = '%s/services' % os.environ.get('OS_AUTH_URL')

    rhead, data = _make_req('GET', url, None, headers)
    services = data.get('services')

    # And now endpoints
    url = '%s/endpoints' % os.environ.get('OS_AUTH_URL')

    rhead, data = _make_req('GET', url, None, headers)
    service_to_endpoints = {}
    for endpoint in data.get('endpoints'):
        service_to_endpoints[endpoint.get('service_id')] = endpoint.get('url')
    
    # And now we can construct a catalog
    catalog = {}
    for service in services:
        name = service.get('name')
        service_id = service.get('id')
        catalog[name] = service_to_endpoints.get(service_id)

    return catalog


def getFlavors(token, service_url, tenant=None):
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'X-Auth-Token': token,
        'X-OpenStack-Nova-API-Version': '2.42',
    }
    url = '%s/flavors/detail' % service_url
    url = url % {'tenant_id': tenant}

    rhead, data = _make_req('GET', url, None, headers)
    return data.get('flavors')


def getServers(token, service_url, tenant=None):
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'X-Auth-Token': token,
        'X-OpenStack-Nova-API-Version': '2.42',
    }
    url = '%s/servers/detail' % service_url
    url = url % {'tenant_id': tenant}

    rhead, data = _make_req('GET', url, None, headers)
    return data.get('servers')


def summarizeServer(server_keys, server, flavors):
    summary = []

    for key in server_keys:
        data = server.get(key)
        if type(data) == dict and 'id' in data:
            data = data['id']

        if key == 'addresses':
            count = 0
            for network in data:
                count += len(data[network])
            data = count
        elif key == 'flavor':
            data = flavors[data]

        summary.append(data)

    return summary


class PrettyOut(object):
    def __init__(self, style, headers):
        self.style = style
        self.headers = headers
        self.rows = []

    def add(self, values):
        self.rows.append(values)

    def emit(self):
        if self.style == 'table':
            pt = PrettyTable()
            pt.field_names = self.headers

            for row in self.rows:
                pt.add_row(row)

            return str(pt)

        elif self.style == 'csv':
            f = StringIO()
            csv_file = csv.writer(f, delimiter=',')
            csv_file.writerow(self.headers)

            for row in self.rows:
                csv_file.writerow(row)

            return f.getvalue()

        else:
            raise Exception('Unknown output style %s' % self.style)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--style', default='table',
                        help='Output style. One of csv or table.')
    parser.add_argument('--tenants',
                        help=('List of tenants to process, separated by commas. '
                              'This is used only for Keystone v2 authenticated users. '
                              'For example: foo=1234,bar=5687'))
    parser.add_argument('--verbose',
                        help='increase output verbosity',
                        action='store_true')

    args = parser.parse_args()

    server_keys = ['id', 'name', 'flavor', 'image', 'status', 'addresses', 'tenant']
    po = PrettyOut(args.style, server_keys)
    server_keys = server_keys[:-1]

    auth_version = getKeystoneVersion()
    if auth_version.startswith('v2'):
        # Keystone v2 doesn't let us see all the user's projects without
        # doing some manual work. Allow users to specify tenants on the
        # command line and then iterate them.
        if not args.tenants:
            projects = [
                {
                    'name': os.environ.get('OS_TENANT_NAME'),
                    'id': os.environ.get('OS_TENANT_ID')
                }
            ]
        else:
            projects = []
            for spec in args.tenants.split(','):
                name, id = spec.split('=')
                projects.append({
                    'name': name,
                    'id': id
                })

        for tenant in projects:
            token_data, endpoints = getKeystoneV2Token(tenant=tenant.get('name'))
            token = token_data.get('id')

            services = {}
            for endpoint in endpoints:
                name = endpoint.get('name')
                services[name] = endpoint.get('endpoints')[0].get('publicURL')

            flavors = {}
            for flavor in getFlavors(token, services['nova'], tenant.get('id')):
                flavors[flavor.get('id')] = '%(name)s: %(vcpus)s cpu, %(ram)s MiB RAM, %(disk)s GiB disk' % flavor

            for server in getServers(token, services['nova'], tenant.get('id')):
                summary = summarizeServer(server_keys, server, flavors)
                summary.append(tenant.get('name'))
                po.add(summary)

    elif auth_version.startswith('v3'):
        token, token_data = getKeystoneV3Token()
        user_id = token_data.get('user').get('id')
        projects = getKeystoneV3Projects(token, user_id)
        services = getKeystoneV3Catalog(token)

        for tenant in projects:
            ptoken, ptoken_data = getKeystoneV3Token(scope=tenant.get('id'))

            flavors = {}
            for flavor in getFlavors(ptoken, services['nova'], tenant.get('id')):
                flavors[flavor.get('id')] = '%(name)s: %(vcpus)s cpu, %(ram)s MiB RAM, %(disk)s GiB disk' % flavor

            for server in getServers(ptoken, services['nova'], tenant.get('id')):
                summary = summarizeServer(server_keys, server, flavors)
                summary.append(tenant.get('name'))
                po.add(summary)

    else:
        print('Unknown auth version %s' % auth_version)
        sys.exit(1)

    print(po.emit())