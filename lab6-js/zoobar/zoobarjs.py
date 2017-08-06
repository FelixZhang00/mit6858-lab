from flask import g, render_template, make_response

import login
from zoodb import *
from debug import catch_err

@catch_err
def zoobarjs():
    if login.logged_in():
        return render_template("zoobars.js")
    else:
        return ""
