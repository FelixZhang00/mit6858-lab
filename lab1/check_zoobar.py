#!/usr/bin/python

import os
import sys
import atexit
import time
import subprocess
import traceback
import sqlite3

from stat import *

thisdir = os.path.dirname(os.path.abspath(__file__))
verbose = False

def green(s):
    return '\033[1;32m%s\033[m' % s

def red(s):
    return '\033[1;31m%s\033[m' % s

def log(*m):
    print >> sys.stderr, " ".join(m)

def log_exit(*m):
    log(red("ERROR:"), *m)
    exit(1)

def file_read(pn):
    with open(pn) as fp:
        return fp.read()

def sh(cmd, exit_onerr=True):
    if verbose: log("+", cmd)
    if os.system(cmd) != 0 and exit_onerr:
        log_exit("running shell command:", cmd)

def killall():
    sh("killall zookld zookd zookfs zookd-exstack zookfs-exstack zookd-nxstack zookfs-nxstack echo-server.py auth-server.py bank-server.py profile-server.py >/dev/null 2>&1", exit_onerr=False)

def setup():
    log("+ removing zoobar db")
    sh("rm -rf zoobar/db")

    log("+ running make.. output in /tmp/make.out")
    sh("make clean >/dev/null")
    sh("make all >/tmp/make.out 2>&1")

    log("+ running zookld in the background.. output in /tmp/zookld.out")
    zookld_out = open("/tmp/zookld.out", "w")
    subprocess.Popen(["./zookld"], stdout=zookld_out, stderr=zookld_out)
    
    atexit.register(killall)
    
    time.sleep(5)

import z_client
def check_ex0():
    x = z_client.check()
    if not x[0]:
        log(red("FAIL"), "Zoobar app functionality", x[1])
        exit(1)
    else:
        log(green("PASS"), "Zoobar app functionality")

def main():
    if '-v' in sys.argv:
        global verbose
        verbose = True
        
    try:
        setup()
        check_ex0()
    except Exception:
        log_exit(traceback.format_exc())

if __name__ == "__main__":
    main()
