#!/usr/bin/env python2
#-*- coding: utf-8 -*-
import datetime
import errno
import os
import fcntl
import paramiko
import sys
import subprocess
import signal
import time
import json

from paramiko import SSHException

class Exp(Exception):
    def __init__(self, errno, err, out = None):
        self.errno = errno
        self.err = err
        self.out = out

    def __str__(self):
        exp_info = 'errno:%s, err:%s'%(self.errno, self.err)
        if self.out is not None:
            exp_info += ' stdout:' + self.out
        return repr(exp_info)

def DINFO(msg):
    print datetime.datetime.now(), 'INFO', msg

def DWARN(msg):
    print >> sys.stderr, datetime.datetime.now(), 'WARN', msg

def DERROR(msg):
    print >> sys.stderr, datetime.datetime.now(), 'ERROR', msg

def exec_cmd(cmd, retry = 3, p = False, timeout = 0):
    env = {"LANG" : "en_US", "LC_ALL" : "en_US", "PATH" : os.getenv("PATH")}
    #cmd = self.lich_inspect + " --movechunk '%s' %s  --async" % (k, loc)
    _retry = 0
    if (p):
        print(cmd)
    while (1):
        p = None
        try:
            p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, env = env)
        except Exception, e:
            raise Exp(e.errno, cmd + ": command execute failed")

        if timeout != 0:
            signal.signal(signal.SIGALRM, _alarm_handler)
            signal.alarm(timeout)
        try:
            stdout, stderr = p.communicate()
            signal.alarm(0)
            ret = p.returncode
            if (ret == 0):
                return stdout, stderr
            elif (ret == errno.EAGAIN and _retry < retry):
                _retry = _retry + 1
                time.sleep(1)
                continue
            else:
                raise Exp(ret, cmd + ": " + os.strerror(ret))

        except KeyboardInterrupt as err:
            _dwarn("interupted")
            p.kill()
            exit(errno.EINTR)

def ping_ok(ip):
    cmd = 'ping %s -c 3 -W 1' % (ip)
    try:
        exec_cmd(cmd)
    except Exp, err:
        return False
    return True

if __name__ == "__main__":
    print "hello, word!"
