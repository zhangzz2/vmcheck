#!/usr/bin/env python2
#-*- coding: utf-8 -*-

import Queue
import threading
import time
import traceback

from vmcheck.utils import exec_cmd, DINFO, DWARN, DERROR, Exp, ping_ok

FENCE_TIMEOUT = 300
THREAD_NUM = 10

def get_local_vms():
    vms = []

    cmd = "set -o pipefail;ps aux|grep kvm|grep lichbd|grep m|grep smp|grep file|grep -v grep"
    stdout = ''
    stderr = ''
    try:
        stdout, stderr = exec_cmd(cmd)
    except Exp, e:
        DWARN("no vm, %s" % (e))
        return vms

    if stdout.strip():
        for l in stdout.strip().split("\n"):
            l = l.split()
            vm_name = l[12]
            vm_pid = l[1]
            vms.append({"name": vm_name, "pid": vm_pid})

    return vms

def kill_vms(vms):
    for v in vms:
        cmd = "kill -9 %s" % (v['pid'])
        exec_cmd(cmd)
        DINFO("kill -9 %s" % (v))

def get_hosts():
    cluster = '/opt/mds/etc/cluster.conf'
    hosts = []
    with open(cluster, 'r') as f:
        lines = [x.strip() for x in f.readlines()]
        hosts = [x for x in lines if not x.startswith("#")]

    return hosts

def fence_ok(hosts):
    ok = []
    error = []

    q = Queue.Queue()
    [q.put(h) for h in hosts]

    def _ping():
        while True:
            item = None
            try:
                item = q.get(block=False)
            except Queue.Empty, e:
                break

            if ping_ok(item):
                ok.append(item)
            else:
                error.append(item)

            q.task_done()

    for i in range(THREAD_NUM):
        t = threading.Thread(target=_ping)
        t.daemon = True
        t.start()

    q.join()

    limit = (len(hosts) / 2) + 1
    if len(ok) >= limit or limit == 1:
        return True
    else:
        return False

def sure_fence_ok(hosts):
    t1 = time.time()
    while True:
        if fence_ok(hosts):
            break

        if (time.time() - t1) > FENCE_TIMEOUT:
            DWARN("fence %s error" % (hosts))
            return False

        DWARN("fence %s error, retry" % (hosts))
        time.sleep(1)

    return True

def _worker():
    hosts = get_hosts()
    if not fence_ok(hosts):
        if not sure_fence_ok(hosts):
            vms = get_local_vms()
            kill_vms(vms)

def worker():
    while True:
        try:
            _worker()
        except Exception, e:
            traceback.print_exc()
            DERROR('worker was error, %s' % (e)) 

        DINFO('worker fence ok')
        time.sleep(7)
    pass

if __name__ == "__main__":
    print "hello, word!"
    worker()
