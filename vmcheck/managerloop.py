#!/usr/bin/env python2
#-*- coding: utf-8 -*-

import Queue
import threading
import time
import mysql

from vmcheck.utils import exec_cmd, DINFO, DWARN, DERROR, ping_ok

PING_TIMEOUT = 300
THREAD_NUM = 10

def get_vms_started():
    '''
    从数据库里面查询到当前所有正在运行的虚拟机
    '''
    db = mysql.connect(host="localhost", user="root", passwd=None, db="zstack")
    sql = '''select uuid, name, hostUuid, lastHostUuid from VmInstanceVO where state=="Stopped" '''
    db.query(sql)
    r = db.store_result()
    vms = []
    for x in r:
        vms.append({'uuid': x[0], 'name': x[1], 'hostUuid': x[2], 'lastHostUuid': x[3]})
    return vms

def vm_update_status(vm_uuid, status):
    db = mysql.connect(host="localhost", user="root", passwd=None, db="zstack")
    sql = '''update set state="%s" from VmInstanceVO where uuid=="%s" ''' % (status, vm_uuid)
    db.query(sql)
    r = db.store_result()
    vms = []
    for x in r:
        vms.append({'uuid': x[0], 'name': x[1], 'hostUuid': x[2], 'lastHostUuid': x[3]})
    return vms

def host_online(host):
    t1 = time.time()
    while True:
        if ping_ok(host):
            break

        if (time.time() - t1) > PING_TIMEOUT:
            DWARN("host %s ping error" % (host))
            return False

        DWARN("host %s ping lost, retry" % (host))
        time.sleep(1)

    return True


def _worker():
    vms = get_vms_started()
    hosts = list(set(vm['host'] for vm in vms))
    if not hosts:
        DINFO("no hosts, return")
        return

    q = Queue()
    for h in list(set(vm['host'] for vm in vms)):
        q.put(h)

    def _do_fetch(host):
        if host_online(host):
            DINFO("host %s online, ok")
        else:
            _vms = [x if x['host'] == host for x in vms]
            DWARN("host %s offline, update vms %s to Stopped" % (host, _vms))
            for x in vms:
                status = 'Stopped'
                DINFO("vm_update vm: %s, vmuuid: %s, status: %s" % (vm["name"], vm["uuid"], status))
                vm_update_status(vm, status)

    def _fetch():
        while True:
            item = None
            try:
                item = q.get(block=False)
            except Queue.Empty, e:
                break

            _do_fetch(item)
            q.task_done()

    for i in range(THREAD_NUM):
        t = threading.Thread(target=_fetch)
        t.daemon = True
        t.start()

    q.join()

def worker():
    while True:
        try:
            _worker()
        except Exception, e:
            DERROR('worker was error, %s' % (e)) 

        time.sleep(7)
    pass

if __name__ == "__main__":
    print "hello, word!"
    worker()
