#!/usr/bin/env python2
#-*- coding: utf-8 -*-

import Queue
import threading
import time
import MySQLdb
import traceback

from vmcheck.utils import exec_cmd, DINFO, DWARN, DERROR, ping_ok, Exp

PING_TIMEOUT = 300
THREAD_NUM = 10

def get_hosts():
    #hosts = [['uuid': uuid, 'managementIp': mip}]
    db = MySQLdb.connect(host="localhost", user="root", db="zstack")
    sql = '''select uuid, managementIp from HostVO '''
    #sql = '''select uuid, name, hostUuid, lastHostUuid from VmInstanceVO where state="running" '''
    cur = db.cursor()
    cur.execute(sql)
    r = cur.fetchall()
    hosts = []
    for x in r:
        hosts.append({"uuid": x[0], "host": x[1]})

    cur.close()
    db.close()
    return hosts

def get_vms_running():
    '''
    从数据库里面查询到当前所有正在运行的虚拟机
    vms.append({'uuid': x[0], 'name': x[1], 'hostUuid': hostuuid, 'lastHostUuid': x[3], 'host': host})
    '''
    db = MySQLdb.connect(host="localhost", user="root", db="zstack")
    sql = '''select uuid, name, hostUuid, lastHostUuid from VmInstanceVO where state="Running" '''
    #sql = '''select uuid, name, hostUuid, lastHostUuid from VmInstanceVO where state="running" '''
    cur = db.cursor()
    cur.execute(sql)
    r = cur.fetchall()

    hosts = get_hosts()
    vms = []
    for x in r:
        hostuuid = x[2]

        host = ''
        for h in hosts:
            if h['uuid'] == hostuuid:
                host = h['host']
                break

        if not host:
            raise Exp(1, 'can not find host uuid: %s, hosts: %s' % (hostuuid, hosts))

        vms.append({'uuid': x[0], 'name': x[1], 'hostUuid': hostuuid, 'lastHostUuid': x[3], 'host': host})

    cur.close()
    db.close()
    return vms

def update_vm(vm_uuid, status):
    db = MySQLdb.connect(host="localhost", user="root", db="zstack")
    sql = '''update VmInstanceVO set state="%s" where uuid="%s" ''' % (status, vm_uuid)
    cur = db.cursor()
    cur.execute(sql)
    db.commit()

    cur.close()
    db.close()

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
    vms = get_vms_running()
    hosts = list(set([vm['host'] for vm in vms]))
    if not hosts:
        DINFO("no hosts, return")
        return

    q = Queue.Queue()
    for h in list(set(vm['host'] for vm in vms)):
        q.put(h)

    def _do_fetch(host):
        if host_online(host):
            DINFO("host %s online, ok" % host)
        else:
            _vms = []
            for v in vms:
                if v['host'] == host:
                    _vms.append(x)

            DWARN("host %s offline, update vms %s to Stopped" % (host, _vms))
            for x in _vms:
                status = 'Stopped'
                DINFO("vm_update vm: %s, vmuuid: %s, status: %s" % (vm["name"], vm["uuid"], status))
                update_vm(vm, status)

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
            traceback.print_exc()
            DERROR('worker was error, %s' % (e)) 

        time.sleep(7)
    pass

if __name__ == "__main__":
    print "hello, word!"
    worker()
