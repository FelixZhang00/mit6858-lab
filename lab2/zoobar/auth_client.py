from debug import *
from zoodb import *
import rpclib

def login(username, password):
    with rpclib.client_connect('/authsvc/sock') as c:
        kwargs = {'username':username,'password':password}
        ret = c.call('login',**kwargs)
        return ret

def register(username, password):
    with rpclib.client_connect('/authsvc/sock') as c:
        kwargs = {'username':username,'password':password}
        print "register kwargs=%s" % kwargs
        ret = c.call('register',**kwargs)
        return ret

def check_token(username, token):
    with rpclib.client_connect('/authsvc/sock') as c:
        kwargs = {'username':username,'token':token}
        ret = c.call('check_token',**kwargs)
        return ret
