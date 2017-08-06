#!/usr/bin/python
#
# Insert bank server code here.
#
import rpclib
import sys
import bank
from debug import *

class BankRpcServer(rpclib.RpcServer):
    def rpc_balance(self,username):
        return bank.balance(username)        

    def rpc_transfer(self,sender,recipient,zoobars):
        return bank.transfer(sender,recipient,zoobars)

    def rpc_get_log(self,username):
        print "rpc_get_log username=%s" % username
        return bank.get_log(username)

    def rpc_check_in(self,username):
        return bank.check_in(username)


(_,dummy_zookld_fd,sockpath) = sys.argv

s = BankRpcServer()
s.run_sockpath_fork(sockpath)
