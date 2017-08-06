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

pwfiles = ['passwd', 'shadow', 'group']
def clean_env():
    # remove /jail and reset password/group files
    if os.path.exists("/jail"):
        sh("mv /jail /jail.bak")
    if os.path.exists("zoobar/db"):
        sh("rm -rf zoobar/db.bak")
        sh("mv zoobar/db zoobar/db.bak")

    for f in pwfiles:
        if not os.path.exists(os.path.join(thisdir, "env", f)):
            log_exit("missing '%s' file in test dir" % f)

    for f in pwfiles:
        sh("mv /etc/%s /etc/%s.bak" % (f, f))
        sh("cp %s/env/%s /etc/%s" % (thisdir, f, f))

    atexit.register(restore_env)

def restore_env():
    for f in pwfiles:
        sh("mv /etc/%s.bak /etc/%s" % (f, f))

    log("+ restoring /jail; test /jail saved to /jail.check..")
    if os.path.exists("/jail.check"):
        sh("rm -rf /jail.check")
    sh("mv /jail /jail.check")
    if os.path.exists("/jail.bak"):
        sh("mv /jail.bak /jail")
    if os.path.exists("zoobar/db.bak"):
        sh("rm -rf zoobar/db")
        sh("mv zoobar/db.bak zoobar/db")

def check_root():
    if os.geteuid() != 0:
        log_exit("must run %s as root" % sys.argv[0])

def killall():
    sh("killall zookld zookd zookfs echo-server.py auth-server.py bank-server.py profile-server.py >/dev/null 2>&1", exit_onerr=False)

def setup():
    log("+ setting up environment in fresh /jail..")
    check_root()
    killall()
    clean_env()

    log("+ running make.. output in /tmp/make.out")
    sh("make clean >/dev/null")
    sh("make all setup >/tmp/make.out 2>&1")

    log("+ running zookld in the background.. output in /tmp/zookld.out")
    zookld_out = open("/tmp/zookld.out", "w")
    subprocess.Popen(["./zookld"], stdout=zookld_out, stderr=zookld_out)

    atexit.register(killall)

    time.sleep(5)

def is_chrooted(process_name):
    sh("for p in $(pgrep %s); do readlink /proc/$p/root; done | sort | uniq > /tmp/chroot.log" % process_name)
    roots = file_read("/tmp/chroot.log").strip().split("\n")
    return roots == ["/jail"]

def check_ex2():
    if not is_chrooted("zookd"):
        log(red("FAIL"), "Exercise 2:", "zookd not chroot'ed to jail")
        return
    if not is_chrooted("zookfs"):
        log(red("FAIL"), "Exercise 2:", "zookfs not chroot'ed to jail")
        return
    log(green("PASS"), "Exercise 2")

def check_ex3():
    sh("pgrep -l zookld > /tmp/ex3.log")
    if 'zookld' not in file_read('/tmp/ex3.log'):
        log(red("FAIL"), "Exercise 3:", "zookld not found")
        return
    sh("for p in $(pgrep zookd); do stat -c %u /proc/$p; done | sort | uniq > /tmp/ex3.log")
    zookduids = file_read('/tmp/ex3.log').split('\n')
    if zookduids[0] == '0':
        log(red("FAIL"), "Exercise 3:", "zookd running as root")
        return
    sh("for p in $(pgrep zookfs); do stat -c %u /proc/$p; done | sort | uniq > /tmp/ex3.log")
    zookfsuids = file_read('/tmp/ex3.log').split('\n')
    if '0' in zookfsuids:
        log(red("FAIL"), "Exercise 3:", "zookfs running as root")
        return
    if zookduids[0] in zookfsuids:
        log(red("FAIL"), "Exercise 3:", "zookfs and zookd running with the same uid")
        return
    log(green("PASS"), "Exercise 3")


def check_ex4_1():
    sh("curl http://localhost:8080/zoobar/db/person/person.db >/tmp/ex4.log 2>/dev/null", exit_onerr=False)
    x = file_read('/tmp/ex4.log')
    if 'CREATE TABLE' in x:
        log(red("FAIL"), "Exercise 4:", "person.db is directly accessible")
        return False
    sh("curl http://localhost:8080/zoobar/db/transfer/transfer.db >/tmp/ex4.log 2>/dev/null", exit_onerr=False)
    x = file_read('/tmp/ex4.log')
    if 'CREATE TABLE' in x:
        log(red("FAIL"), "Exercise 4:", "transfer.db is directly accessible")
        return False
    return True

def file_uid(pn):
    return os.stat(pn).st_uid

def access(pn, perm):
    s = os.stat(pn)
    return (s.st_mode & perm) != 0

def zook_uids(url):
    sh("rm -f /jail/tmp/http_request_line /jail/tmp/http_request_headers")
    sh("touch /jail/tmp/grading")
    sh("curl %s >/dev/null 2>&1" % url)
    return { 'zookd'  : file_uid("/jail/tmp/http_request_line"),
             'zookfs' : file_uid("/jail/tmp/http_request_headers") }

def check_ex4_2():
    u1 = zook_uids("http://localhost:8080/zoobar/index.cgi")
    u2 = zook_uids("http://localhost:8080/zoobar/media/zoobar.css")
    if u1['zookfs'] == u2['zookfs']:
        log(red("FAIL"), "Exercise 4:", "static and dynamic content served by same uid", str(u1['zookfs']))
        return False
    return True

def check_exec(svc, allowed):
    import ConfigParser, StringIO
    config = ConfigParser.RawConfigParser()
    data = StringIO.StringIO('\n'.join(line.strip() for line in open("zook.conf")))
    config.readfp(data)

    if not config.has_section(svc):
        log(red("FAIL"), "Exercise 4:", "%s missing from zook.conf" % svc)
        return False
    if not config.has_option(svc, "args"):
        log(red("FAIL"), "Exercise 4:", "%s has no args in zook.conf" % svc)
        return False
    try:
        uid, gid = map(int, config.get(svc, "args").split())
    except:
        log(red("FAIL"), "Exercise 4:", "%s has ill-formatted args in zook.conf" % svc)
        return False
    if uid < 0 or gid < 0:
        log(red("FAIL"), "Exercise 4:", "args should have non-negative uid and gid")
        return False

    sh("find /jail -uid %d -gid %d > /tmp/executable.log" % (uid, gid))
    x = file_read("/tmp/executable.log").strip().split()
    bad = list(sorted(set(x) - set(allowed)))
    if bad != []:
        log(red("FAIL"), "Exercise 4:", "%s allows execution of %s" % (svc, bad[0]))
        return False
    return True

def check_ex4_3():
    if not check_exec("static_svc", []):
        return False
    return check_exec("dynamic_svc", ["/jail/zoobar/index.cgi"])

def check_ex4():
    if check_ex4_1() and check_ex4_2() and check_ex4_3():
        log(green("PASS"), "Exercise 4")

def dbquery(dbfile, q):
    conn = sqlite3.connect(dbfile)
    cur  = conn.cursor()
    cur.execute(q)
    ret  = cur.fetchall()
    cur.close()
    conn.close()
    return ret

def db_tables(dbfile):
    rows = dbquery(dbfile, "SELECT name FROM sqlite_master WHERE type='table'")
    return [ r[0].lower() for r in rows ]

def column_in_table(dbfile, table, column):
    rows = dbquery(dbfile, "SELECT sql FROM sqlite_master WHERE type='table' AND name='%s'" % table)
    return column.lower() in rows[0][0].lower()

def check_db(ex, service, dbfile, table, columns):
    if not os.path.exists(dbfile):
        log(red("FAIL"), ex, "no db %s" % dbfile)
        return False

    dbname = os.path.basename(dbfile)
    uid = file_uid(dbfile)
    sh("pgrep -l -u %s > /tmp/ex-db.log" % uid, exit_onerr=False)
    x = file_read("/tmp/ex-db.log")
    if service not in x:
        log(red("FAIL"), ex, "no %s running with access to %s" % (service, dbname))
    elif len(x.strip().split("\n")) > 1:
        log(red("FAIL"), ex, "more than one running process has access to %s" % dbname)
    elif access(dbfile, S_IWGRP) or access(dbfile, S_IWOTH):
        log(red("FAIL"), ex, "non-owners can write to %s" % dbname)
    elif table.lower() not in db_tables(dbfile):
        log(red("FAIL"), ex, "%s table not present in %s" % (table, dbfile))
    elif not all([ column_in_table(dbfile, table, c) for c in columns ]):
        log(red("FAIL"), ex, "missing some column in %s table of %s" % (table, dbfile))
    else:
        return True

    return False

def check_ex5_1():
    db = "/jail/zoobar/db/cred/"
    if access(db, S_IRWXG) or access(db, S_IRWXO):
        log(red("FAIL"), "Exercise 5:", "cred table directory has group or world permissions")
        return False
    return True

def check_ex5_2():
    persondb = "/jail/zoobar/db/person/person.db"
    if any([ column_in_table(persondb, "person", c) \
               for c in ['password', 'token'] ]):
        log(red("FAIL"), "Exercise 5:", "person table still has some cred table column")
        return False
    return True

def check_ex5():
    check_0 = check_db("Exercise 5:", "auth-server.py",
                       "/jail/zoobar/db/cred/cred.db",
                       "cred", ['password', 'token'])

    if check_0 and check_ex5_1() and check_ex5_2():
        log(green("PASS"), "Exercise 5")

def check_ex6():
    dbfile = "/jail/zoobar/db/cred/cred.db"
    if not os.path.exists(dbfile):
        log(red("FAIL"), "Exercise 6:", "no db %s" % dbfile)
        return

    db = file_read(dbfile)
    if "supersecretpassword" in db:
        log(red("FAIL"), "Exercise 6:", "plain-text password in database")
    else:
        log(green("PASS"), "Exercise 6")

def check_ex7_1():
    if column_in_table("/jail/zoobar/db/person/person.db", "person", "zoobars"):
        log(red("FAIL"), "Exercise 7:", "person table still has the zoobars column")
        return False
    return True

def check_ex7():
    check_0 = check_db("Exercise 7:", "bank-server.py",
                       "/jail/zoobar/db/bank/bank.db",
                       "bank", ['zoobars'])

    if check_0 and check_ex7_1():
        log(green("PASS"), "Exercise 9")

import z_client
def check_ex0():
    x = z_client.check()
    if not x[0]:
        log(red("FAIL"), "App functionality", x[1])
        exit(1)
    else:
        log(green("PASS"), "App functionality")

def main():
    if '-v' in sys.argv:
        global verbose
        verbose = True

    try:
        setup()
        check_ex0()

        check_ex2()
        check_ex3()
        check_ex4()
        check_ex5()
        check_ex6()
        check_ex7()
    except Exception:
        log_exit(traceback.format_exc())

if __name__ == "__main__":
    main()
