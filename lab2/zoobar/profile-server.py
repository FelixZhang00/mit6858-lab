#!/usr/bin/python

import rpclib
import sys
import os
import stat
import sandboxlib
import urllib
import hashlib
import socket
import bank_client
import zoodb

from debug import *

## Cache packages that the sandboxed code might want to import
import time
import errno

class ProfileAPIServer(rpclib.RpcServer):
    def __init__(self, user, visitor):
        uid = 61012
        self.user = user
        self.visitor = visitor
        os.setresuid(uid,uid,uid)

    def rpc_get_self(self):
        return self.user

    def rpc_get_visitor(self):
        return self.visitor

    def rpc_get_xfers(self, username):
        xfers = []
        for xfer in bank_client.get_log(username):
            xfers.append({ 'sender': xfer['sender'],
                           'recipient': xfer['recipient'],
                           'amount': xfer['amount'],
                           'time': xfer['time'],
                         })
        return xfers

    def rpc_get_user_info(self, username):
        person_db = zoodb.person_setup()
        p = person_db.query(zoodb.Person).get(username)
        if not p:
            return None
        return { 'username': p.username,
                 'profile': p.profile,
                 'zoobars': bank_client.balance(username),
               }

    def rpc_xfer(self, target, zoobars):
        bank_client.transfer(self.user, target, zoobars)

def run_profile(pcode, profile_api_client):
    globals = {'api': profile_api_client}
    exec pcode in globals

class ProfileServer(rpclib.RpcServer):
    def rpc_run(self, pcode, user, visitor):
        uid = 61008 # according zook.conf
        
        #consider the possibillity of usernames with special characters
        #so I use hash function try to get a unique nnumber
        userdir = '/tmp/%s' % str(hashlib.sha512(user).hexdigest())[0:10] 
        print 'userdir=%s' % userdir
        if not os.path.exists(userdir):
            os.makedirs(userdir)
            os.chmod(userdir,0755)        
            os.chown(userdir,uid,uid)

        (sa, sb) = socket.socketpair(socket.AF_UNIX, socket.SOCK_STREAM, 0)
        pid = os.fork()
        if pid == 0:
            if os.fork() <= 0:
                sa.close()
                ProfileAPIServer(user, visitor).run_sock(sb)
                sys.exit(0)
            else:
                sys.exit(0)
        sb.close()
        os.waitpid(pid, 0)

        sandbox = sandboxlib.Sandbox(userdir, uid, '/profilesvc/lockfile')
        with rpclib.RpcClient(sa) as profile_api_client:
            return sandbox.run(lambda: run_profile(pcode, profile_api_client))

(_, dummy_zookld_fd, sockpath) = sys.argv

s = ProfileServer()
s.run_sockpath_fork(sockpath)
