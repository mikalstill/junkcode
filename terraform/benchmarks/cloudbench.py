#!/usr/bin/python

import argparse
import datetime
import os
import subprocess
import sys
import time


def runcloud(cloud, count=5):
    path = os.path.join(
        '/'.join(os.path.realpath(__file__).split('/')[:-1]), '%s_simple' % cloud)

    # See if there are newer versions
    i = 2
    while os.path.exists('%s_%d' %(path, i)):
        i += 1
    i -= 1

    if i > 1:
        path += '_%d' % i

    print('%s Test terraform is %s' %(datetime.datetime.now(), path))

    run_id = '%s' % time.time()
    run_id = run_id.replace('.', '_')
    print('%s Run id is %s' %(datetime.datetime.now(), run_id))

    env = os.environ.copy()
    env['TF_LOG'] = 'TRACE'

    env['TF_LOG_PATH'] = '../runlogs/%s_%s_init.log' %(cloud, run_id)
    cmd = 'terraform init'
    out, ecode, duration = execute(cmd, path, env)
    print('%s %s "%s" returned %d after %.02f seconds'
          %(datetime.datetime.now(), cloud, cmd, ecode, duration))
    sys.stdout.flush()
    with open('runlogs/%s_%s_init' %(cloud, run_id), 'w') as f:
        f.write(''.join(out))
        f.write('\n\nexit code: %s' % ecode)

    env['TF_LOG_PATH'] = '../runlogs/%s_%s_plan.log' %(cloud, run_id)
    cmd = 'terraform plan -var-file=demo.tfvars'
    out, ecode, duration = execute(cmd, path, env)
    print('%s %s "%s" returned %d after %.02f seconds'
          %(datetime.datetime.now(), cloud, cmd, ecode, duration))
    sys.stdout.flush()
    with open('runlogs/%s_%s_plan' %(cloud, run_id), 'w') as f:
        f.write(''.join(out))
        f.write('\n\nexit code: %s' % ecode)

    for i in range(count):
        env['TF_LOG_PATH'] = '../runlogs/%s_%s_%d_apply.log' %(cloud, run_id, i)
        cmd = 'terraform apply -auto-approve -var-file=demo.tfvars' 
        out, ecode, duration = execute(cmd, path, env)
        print('%s %s "%s" returned %d after %.02f seconds'
              %(datetime.datetime.now(), cloud, cmd, ecode, duration))
        sys.stdout.flush()
        with open('runlogs/%s_%s_%d_apply' %(cloud, run_id, i), 'w') as f:
            f.write(''.join(out))
            f.write('\n\nexit code: %s' % ecode)

        env['TF_LOG_PATH'] = '../runlogs/%s_%s_%d_destroy.log' %(cloud, run_id, i)
        cmd = 'terraform destroy -auto-approve -var-file=demo.tfvars'
        out, ecode, duration = execute(cmd, path, env)
        print('%s %s "%s" returned %d after %.02f seconds'
              %(datetime.datetime.now(), cloud, cmd, ecode, duration))
        sys.stdout.flush()
        with open('runlogs/%s_%s_%d_destroy' %(cloud, run_id, i), 'w') as f:
            f.write(''.join(out))
            f.write('\n\nexit code: %s' % ecode)


def execute(cmd, cwd, env):
    start_time = time.time()
    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, cwd=cwd, env=env)
    p.wait()
    return (p.stdout.readlines(), p.returncode, time.time() - start_time)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--cloud', default='azure',
                        help='One of aws, azure, gcp, vault, vexxhost')
    parser.add_argument('--count', default=5, type=int,
                        help='The number of runs per cycle')
    parser.add_argument('--cycles', default=1, type=int,
                        help='The number of cycles')
    parser.add_argument('--cycle-frequency', default=600, type=int,
                        help='The number seconds to space cycles at')
    args = parser.parse_args()

    previous = time.time() - args.cycle_frequency - 1
    for _ in range(args.cycles):
        if os.path.exists('abort'):
            sys.exit(0)

        t = time.time()
        if t - previous > args.cycle_frequency:
            runcloud(args.cloud, count=args.count)
        else:
            time.sleep(1)
