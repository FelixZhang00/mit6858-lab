#!/usr/bin/python

import datetime
import os
import stat
import sys
import atexit
import time
import subprocess
import traceback
import re
import urllib
import base64
import sqlite3

import z_client as z

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

def file_read(pn, size=-1):
    with open(pn) as fp:
        return fp.read(size)

def log_to_file(*m):
    with open('/tmp/html.out', 'a') as fp:
        print >> fp, " ".join(m)

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
    sh("rm -f /tmp/html.out")

    log("+ running zookld in the background.. output in /tmp/zookld.out")
    zookld_out = open("/tmp/zookld.out", "w")
    subprocess.Popen(["./zookld"], stdout=zookld_out, stderr=zookld_out)

    log("+ profile output logged in /tmp/html.out")

    atexit.register(killall)

    time.sleep(5)

def check_ex0():
    x = z.check()
    if not x[0]:
        log(red("FAIL"), "App functionality", x[1])
        exit(1)
    else:
        log(green("PASS"), "App functionality")

def update_profile(cookie, code):
    result = z.post("http://localhost:8080/zoobar/index.cgi/", cookie,
           "profile_update=%s&profile_submit=Save" % urllib.quote_plus(code))

def check_profile_internal(logmsg, code, prof_pat,
                           user1="test1", pass1="supersecretpassword",
                           user2="test2", pass2="pass"):
    ## login as user test1
    html1, cookies1 = z.login(user1, pass1)
    ## update test1 profile
    update_profile(cookies1, code)

    ## login as user test2
    html2, cookies2 = z.login(user2, pass2)

    ## fetch test1 profile
    vhtml = z.view_user(cookies2, user1)

    ## log profile output
    log_to_file("=" * 60)
    log_to_file(logmsg)
    log_to_file("")
    log_to_file(vhtml)
    log_to_file("")

    ## check for profile pattern
    ans = "Traceback" not in vhtml and re.search(prof_pat, vhtml, re.DOTALL) is not None
    #if not ans:
        #print "OOPS! $#$#$#$#$#"
        #print "pat",prof_pat
        #print vhtml
    return ans

## profile generation patterns
wrapper_pat = '''
try:
    if check():
        print "SUCCESS"
    else:
        print "ERROR : check failed"
except BaseException, e:
    import traceback
    print "ERROR : caught exception"
    print traceback.format_exc()
'''

file_read_pat = '''#!python
def check():
    import os, base64
    print "Opening file %(path)s"
    fd = os.open("%(path)s", os.O_RDONLY)
    print "Opened file %(path)s"
    d  = os.read(fd, %(length)d)
    os.close(fd)
    print "Read '" + d + "' from file"
    return base64.b64encode(d) == "%(data)s"
'''

file_write_pat = '''#!python
def check():
    import os
    print "Opening file %(path)s"
    fd = os.open("%(path)s", os.O_CREAT | os.O_RDWR)
    print "Opened file %(path)s"
    d  = "%(data)s"
    l  = os.write(fd, d)
    os.close(fd)
    print "Wrote " + str(l) + " bytes"
    return l == len(d)
'''

def file_read_check(logmsg, sbpath, realpath=None, data=None,
                    user1="test1", pass1="supersecretpassword",
                    user2="test2", pass2="pass"):
    if not data:
        data = file_read(realpath, 10)

    code = file_read_pat % {'path': sbpath, 'data': base64.b64encode(data), 'length': len(data)}
    code += wrapper_pat
    return check_profile_internal(logmsg, code, "SUCCESS", user1, pass1, user2, pass2)

def file_write_check(logmsg, sbpath, data=None,
                    user1="test1", pass1="supersecretpassword",
                    user2="test2", pass2="pass"):
    if not data:
        data = "file_write_check test string"

    code = file_write_pat % {'path': sbpath, 'data': data}
    code += wrapper_pat
    if not check_profile_internal(logmsg, code, "SUCCESS", user1, pass1, user2, pass2):
        return False

    return file_read_check(logmsg + "read and compare:", sbpath, None, data, user1, pass1, user2, pass2)

def check_profile(prof_py, prof_pat, msg):
    code = file_read(os.path.join(thisdir, "profiles", prof_py))
    ret = check_profile_internal("%s:" % msg, code, prof_pat)
    if not ret:
        log(red("FAIL"), "Profile", prof_py, ":", msg)
    return ret

def check_sandbox():
    if file_read_check("Exercise 10: Sandbox:", "/zoobar/media/zoobar.css",
                       "/jail/zoobar/media/zoobar.css"):
        log(red("FAIL"), "Exercise 10: Sandbox check")
        return False
    else:
        log(green("PASS"), "Exercise 10: Sandbox check")
        return True

def check_hello():
    pat = "profile.*Hello,.*test2.*Current time: \d+\.\d+"
    if check_profile("hello-user.py", pat, "Hello user check"):
        log(green("PASS"), "Profile hello-user.py")

#there has got to be a better way...
def check_myprofile():
    code = file_read(os.path.join(thisdir, "profiles", "my-profile.py"))
    code += "\nprint 'SUCCESS'"
    ret = check_profile_internal("Challenge 2: my-profile functional", code, "SUCCESS")
    if not ret:
        log(red("FAIL"), "Challenge 2: Profile my-profile doesn't seem to parse correctly")
    else:
        log(green("PASS"), "Challenge 2: basic sanity check")


def check_visit_tracker_1():
    pat = "profile.*Hello,.*test2.*Your visit count: 0.*Your last visit: never"
    return check_profile("visit-tracker.py", pat, "First visit check")

def check_visit_tracker_2():
    pat = "profile.*Hello,.*test2.*Your visit count: 1.*Your last visit: \d+\.\d+"
    return check_profile("visit-tracker.py", pat, "Second visit check")

def check_visit_tracker():
    if check_visit_tracker_1() and check_visit_tracker_2():
        log(green("PASS"), "Profile visit-tracker.py")

def check_last_visits_1():
    pat = "profile.*Last 3 visitors:.*test2 at \d+"
    return check_profile("last-visits.py", pat, "Last visits check (1/3)")

def check_last_visits_2():
    pat = "profile.*Last 3 visitors:.*test2 at \d+.*test2 at \d+"
    return check_profile("last-visits.py", pat, "Last visits check (2/3)")

def check_last_visits_3():
    pat = "profile.*Last 3 visitors:.*test2 at \d+.*test2 at \d+.*test2 at \d+"
    return check_profile("last-visits.py", pat, "Last visits check (3/3)")

def check_last_visits():
    if check_last_visits_1() and check_last_visits_2() and check_last_visits_3():
        log(green("PASS"), "Profile last-visits.py")

def check_xfer_tracker_1():
    now = datetime.datetime.now()
    pat = "profile.*I gave you 3 zoobars \@ .* %d" % now.year
    return check_profile("xfer-tracker.py", pat, "Transfer tracker check")

# def check_xfer_tracker_2():
#     html2, cookies2 = z.login("test2", "pass")
#     thtml = z.transfer(cookies2, "test1", 3)
#     pat = "profile.*You gave me 3 zoobars \@"
#     return check_profile("xfer-tracker.py", pat)

def check_xfer_tracker():
    if check_xfer_tracker_1():
        log(green("PASS"), "Profile xfer-tracker.py")

def check_granter_1():
    pat = "profile.*Thanks for visiting.  I gave you one zoobar."
    if not check_profile("granter.py", pat, "Zoobar grant check"):
        return False

    # check that profile owner token was used and not visitor's, by checking
    # that profile owner has one less zoobar
    html, cookies = z.login("test1", "supersecretpassword")
    if not z.check_zoobars(html, "test1", 6, "")[0]:
        log(red("FAIL"), "Exercises 9-11:", "Not using profile owner's token")

    return True

def check_granter_2():
    pat = "profile.*I gave you a zoobar .* seconds ago"
    return check_profile("granter.py", pat, "'Greedy visitor check1")

def check_granter_3():
    html3, cookies3 = z.register("test3", "pass")
    z.transfer(cookies3, "test2", 10)
    pat = "profile.*You have \d+ already; no need for more"
    return check_profile("granter.py", pat, "Greedy visitor check2")

def check_granter_4():
    html1, cookies1 = z.login("test1", "supersecretpassword")
    z.transfer(cookies1, "test2", 6)
    pat = "profile.*Sorry, I have no more zoobars"
    return check_profile("granter.py", pat, "'I am broke' check")

def check_granter():
    if check_granter_1() and check_granter_2() and \
        check_granter_3() and check_granter_4():
        log(green("PASS"), "Profile granter.py")

# check that the file system is separate for different users
def check_fs():
    tmpfile = "/testfile"
    data    = "testfile check test string"

    # write to / as user test1
    if not file_write_check("Exercise 10: /testfile write:", tmpfile, data,
                            "test1", "supersecretpassword", "test2", "pass"):
        log(red("FAIL"), "Exercise 10: /testfile check (could not write to /testfile)")
        return

    # try to read the same file
    if file_read_check("Exercise 10: shared /testfile:", tmpfile, None, data,
                       "test2", "pass", "test1", "supersecretpassword"):
        log(red("FAIL"), "Exercise 10: /testfile check (/testfile shared by more than one user)")
        return

    # try to read the same file, sneaky edition
    z.register("test1/.", "pass")
    if file_read_check("Exercise 10: shared /testfile:", tmpfile, None, data,
                       "test1/.", "pass", "test1", "supersecretpassword"):
        log(red("FAIL"), "Exercise 10: /testfile check (special characters in usernames)")
        return

    # check world permissions on file
    #st = os.stat('/jail'+tmpfile)
    #if bool(st.st_mode & stat.S_IRWXO):
    #    log(red("FAIL"), "Exercise 2: profile files have world permissions")
    #    return


    log(green("PASS"), "Exercise 10: /testfile check")


sleeping_pat = '''#!python
import time
time.sleep(4)
print "DONE"
'''


def check_profileapi_uid():
    pid = os.fork()
    if pid == 0:
        atexit._exithandlers = []
        check_profile_internal("Check number of root processes",sleeping_pat,"DONE")
        sys.exit(0)

    #yeah, it's a bit of a race. Give it 30s. Better ideas?
    for i in range(60):
        sh("for p in $(pgrep profile-s); do stat -c %u /proc/$p; done | sort > /tmp/ex3.uids")
        profile_uids = file_read('/tmp/ex3.uids').split('\n')
        #assuming that service forks three times, empty line at end
        if len(profile_uids) >= 5:
            break;
        time.sleep(0.5)

    os.waitpid(pid,0)
    l = len([1 for x in profile_uids if x == '0'])
    if l > 2:
        log(red("FAIL"), "Exercise 11: Profile API service seems to be running as root")
        return
    if l < 2:
        log(red("FAIL?"), "Exercise 11: profile-service does not seem to fork")
        return

    log(green("PASS"), "Exercise 11: ProfileAPIServer uid")

def column_in_table(dbfile, table, column):
    rows = dbquery(dbfile, "SELECT sql FROM sqlite_master WHERE type='table' AND name='%s'" % table)
    return column.lower() in rows[0][0].lower()


def dbquery(dbfile, q):
    conn = sqlite3.connect(dbfile)
    cur  = conn.cursor()
    cur.execute(q)
    ret  = cur.fetchall()
    cur.close()
    conn.close()
    return ret

def check_profile_service():
    persondb = "/jail/zoobar/db/person/person.db"
    if column_in_table(persondb, "person", "profile"):
        log(red("FAIL"), "Challenge 3:", "person table still has column profile")
        return False
    return True



def main():
    if '-v' in sys.argv:
        global verbose
        verbose = True

    try:
        setup()
        check_ex0()

        check_hello()
        check_visit_tracker()
        check_last_visits()
        check_xfer_tracker()
        check_granter()

        #Exercise 10
        #if check_sandbox():
        check_fs()
        #Exercise 11
        check_profileapi_uid()
        #Challenge 2
        check_myprofile()
        #Challenge 3
        if check_profile_service():
            log(green("PASS"), "Challenge: profile column not in person db")




    except Exception:
        log_exit(traceback.format_exc())

if __name__ == "__main__":
    main()
