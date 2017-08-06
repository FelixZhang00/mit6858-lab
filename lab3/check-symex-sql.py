#!/usr/bin/python

import symex.fuzzy as fuzzy
import shutil
import os
from sqlalchemy import *
from sqlalchemy.orm import *
from sqlalchemy.ext.declarative import *

import symex.importwrapper as importwrapper
import symex.rewriter as rewriter
importwrapper.rewrite_imports(rewriter.rewriter)

import symex.symsql

Test1Base = declarative_base()
Test2Base = declarative_base()

class Test1(Test1Base):
    __tablename__ = "test1"
    name = Column(String(128), primary_key=True)
    value = Column(Integer)

class Test2(Test2Base):
    __tablename__ = "test2"
    name = Column(Integer, primary_key=True)
    value = Column(String(128))

dbdir = '/tmp/lab3-check-symex-sql'
if os.path.exists(dbdir):
    shutil.rmtree(dbdir)
os.makedirs(dbdir)

def dbsetup(name, base):
    dbfile = os.path.join(dbdir, "%s.db" % name)
    engine = create_engine('sqlite:///%s' % dbfile,
                           isolation_level='SERIALIZABLE')
    base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)
    return session()

def test1_setup():
    return dbsetup("test1", Test1Base)

def test2_setup():
    return dbsetup("test2", Test2Base)

f_results = set()
def test_f():
    db = test1_setup()
    s = fuzzy.mk_str('s')
    print s
    r = db.query(Test1).get(s)
    print r
    if r is None:
        v = None
    else:
        v = r.value
    print s, '->', v
    f_results.add(v)

g_results = set()
def test_g():
    db = test2_setup()
    x = fuzzy.mk_int('x')
    r = db.query(Test2).get(x)
    if r is None:
        v = None
    else:
        v = r.value
    print x, '->', v
    g_results.add(v)

t1 = test1_setup()
t1a = Test1()
t1a.name = 'foo'
t1a.value = 924
t1.add(t1a)
t1b = Test1()
t1b.name = 'barr'
t1b.value = 22
t1.add(t1b)
t1.commit()

t2 = test2_setup()
t2a = Test2()
t2a.name = 9241
t2a.value = 'firstthing'
t2.add(t2a)
t2b = Test2()
t2b.name = 5
t2b.value = 'another'
t2.add(t2b)
t2c = Test2()
t2c.name = -23
t2c.value = 'yy'
t2.add(t2c)
t2.commit()

print 'Testing f..'
fuzzy.concolic_test(test_f, verbose=10)
f_expected = (924, 22)
if all(x in f_results for x in f_expected):
    print "Found all cases for f"
else:
    print "Missing some cases for f:", set(f_expected) - set(f_results)

print 'Testing g..'
fuzzy.concolic_test(test_g, verbose=10)
g_expected = ('firstthing', 'another', 'yy')
if all(x in g_results for x in g_expected):
    print "Found all cases for g"
else:
    print "Missing some cases for g:", set(g_expected) - set(g_results)
