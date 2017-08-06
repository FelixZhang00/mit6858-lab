from debug import *
from zoodb import *
import rpclib

def transfer(sender,recipient,zoobars):
    with rpclib.client_connect('/banksvc/sock') as c:
        kwargs = {'sender':sender,'recipient':recipient,'zoobars':zoobars}
        ret = c.call('transfer',**kwargs)
        return ret

def balance(username):
    with rpclib.client_connect('/banksvc/sock') as c:
        kwargs = {'username':username}
        ret = c.call('balance',**kwargs)
        return ret

def get_log(username):
    with rpclib.client_connect('/banksvc/sock') as c:
        kwargs = {'username':username}
        print "bank_client get_log kwargs=%s" % kwargs
        ret = c.call('get_log',**kwargs)
        return ret

def check_in(username):
    with rpclib.client_connect('/banksvc/sock') as c:
        kwargs = {'username':username}
        print "bank_client check_in  kwargs=%s" % kwargs
        ret = c.call('check_in',**kwargs)
        return ret
