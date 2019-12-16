#!/usr/bin/python

import os
import subprocess
import time


def runcloud(cloud):
    path = os.path.join(
        '/'.join(os.path.realpath(__file__).split('/')[:-1]), '%s_simple' % cloud)

    cmd = 'terraform init'
    out, ecode, duration = execute(cmd, path)
    print('%s "%s" returned %d after %.02f seconds' %(cloud, cmd, ecode, duration))

    cmd = 'terraform plan'
    out, ecode, duration = execute(cmd, path)
    print('%s "%s" returned %d after %.02f seconds' %(cloud, cmd, ecode, duration))

    for i in range(5):
        cmd = 'terraform apply -auto-approve'
        out, ecode, duration = execute(cmd, path)
        print('%s "%s" returned %d after %.02f seconds' %(cloud, cmd, ecode, duration))

        cmd = 'terraform destroy -auto-approve'
        out, ecode, duration = execute(cmd, path)
        print('%s "%s" returned %d after %.02f seconds' %(cloud, cmd, ecode, duration))


def execute(cmd, cwd):
    start_time = time.time()
    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, cwd=cwd)
    p.wait()
    return (p.stdout.readlines(), p.returncode, time.time() - start_time)


if __name__ == '__main__':
    # aws, azure, gcp, vault, vexxhost
    for cloud in ['gcp']:
        runcloud(cloud)
