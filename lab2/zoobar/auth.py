from zoodb import *
from debug import *

import hashlib
import random
import os
import pbkdf2

def newtoken(db, cred):
    hashinput = "%s%.10f" % (cred.password, random.random())
    cred.token = hashlib.md5(hashinput).hexdigest()
    db.commit()
    return cred.token

def login(username, password):
    db_person = person_setup()
    person = db_person.query(Person).get(username)
    if not person:
        return None
    db_cred = cred_setup()
    cred = db_cred.query(Cred).get(username)
    password = pbkdf2.PBKDF2(password,cred.salt).hexread(32)
    if cred.password == password:
        return newtoken(db_cred, cred)
    else:
        return None

def register(username, password):
    print "auth register (%s,%s)" % (username,password)
    db_person = person_setup()
    person = db_person.query(Person).get(username)
    if person:
        return None
    newperson = Person()
    newperson.username = username
    db_person.add(newperson)
    db_person.commit()
    
    # salt to secure password
    salt = os.urandom(32).encode('hex')
    password = pbkdf2.PBKDF2(password,salt).hexread(32) 
 
    db_cred = cred_setup()
    newcred = Cred()
    newcred.username = username
    newcred.password = password
    newcred.salt = salt
    db_cred.add(newcred)
    db_cred.commit()
    return newtoken(db_cred, newcred)

def check_token(username, token):
    db = cred_setup()
    cred = db.query(Cred).get(username)
    if cred and cred.token == token:
        return True
    else:
        return False

