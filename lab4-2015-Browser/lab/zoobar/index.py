from flask import g, render_template, request
from login import requirelogin
from debug import *
from zoodb import *

@catch_err
@requirelogin
def index():
    if 'profile_update' in request.form:
        persondb = person_setup()
        person = persondb.query(Person).get(g.user.person.username)
        person.profile = request.form['profile_update']
        persondb.commit()

        ## also update the cached version (see login.py)
        g.user.person.profile = person.profile
    return render_template('index.html')
