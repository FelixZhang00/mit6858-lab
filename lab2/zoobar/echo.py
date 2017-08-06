from flask import g, render_template, request
from debug import *
import rpclib

@catch_err
def echo():
    with rpclib.client_connect('/echosvc/sock') as c:
        ret = c.call('echo', s=request.args.get('s', ''))
        return render_template('echo.html', s=ret)
