import os
import resource
import sys
import fcntl
import signal
import threading

class ProcessTimeout(threading.Thread):
    def __init__(self, pid, timeout):
        threading.Thread.__init__(self)
        self.pid = pid
        self.timeout = timeout
        self.killing = threading.Event()
        self.killed = threading.Event()

    def kill(self):
        if not self.killing.is_set():
            self.killing.set()
            os.kill(self.pid, signal.SIGKILL)
            (_, status) = os.waitpid(self.pid, 0)
            assert(os.WIFEXITED(status) or os.WIFSIGNALED(status))
            self.killed.set()
        self.killed.wait()

    def run(self):
        self.killed.wait(self.timeout)
        self.kill()

class Sandbox(object):
    def __init__(self, dir, uid, lockfile, timeout=5.0):
        self.dir = dir
        self.uid = uid
        self.lockfile = lockfile
        self.timeout = timeout

    def child(self, func):
        os.chroot(self.dir)
        os.chdir('/')
        resource.setrlimit(resource.RLIMIT_NPROC, (0, 0))
        os.setresuid(self.uid, self.uid, self.uid)
        func()

    def run(self, func):
        with open(self.lockfile, 'w+') as lockf:
            ## Only one instance allowed at a time, due to shared uid
            fcntl.flock(lockf.fileno(), fcntl.LOCK_EX)

            (piperd, pipewr) = os.pipe()

            pid = os.fork()
            if pid == 0:
                lockf.close()
                os.close(piperd)
                os.close(0)
                os.dup2(pipewr, 1)
                self.child(func)
                sys.exit(0)

            pt = ProcessTimeout(pid, self.timeout)
            pt.start()

            os.close(pipewr)
            with os.fdopen(piperd, 'r') as piperf:
                resp = piperf.read()

            pt.kill()
            return resp

