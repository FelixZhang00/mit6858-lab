#!/usr/bin/python

import symex.fuzzy as fuzzy
import z3
import traceback
import sys

class MyException(Exception):
    def __init__(self, *args):
        super(MyException, self).__init__(*args)

try:
    fuzzy.cur_path_constr = []
    fuzzy.cur_path_constr_callers = []
    fuzzy.concrete_values = {'s': 'abcdef'}
    s = fuzzy.mk_str('s')
    t = 'foo' + s + 'bar'
    if not isinstance(t, fuzzy.concolic_str):
        raise MyException("ERROR: lost concolic object after concat")
    l = len(t)
    if not isinstance(l, fuzzy.concolic_int):
        raise MyException("ERROR: lost concolic object after len")
    if l != 12:
        raise MyException("ERROR: wrong concrete value for concolic object")
    if len(fuzzy.cur_path_constr) == 0:
        raise MyException("ERROR: no path constraint")
    if len(fuzzy.cur_path_constr) > 1:
        raise MyException("ERROR: too many path constraints")
    fuzzy.cur_path_constr = []
    if l + 2 == 22:
        raise MyException("ERROR: wrong concrete value, take 2")
    (ok, model) = fuzzy.fork_and_check(fuzzy.sym_not(fuzzy.cur_path_constr[0]))
    if ok != z3.sat:
        raise MyException("ERROR: unsolvable constraint")
    if len(model['s']) != 14:
        raise MyException("ERROR: wrong value in solved constraint")
    print "Length works"
except MyException:
    traceback.print_exc(None, sys.stdout)

try:
    fuzzy.cur_path_constr = []
    fuzzy.cur_path_constr_callers = []
    fuzzy.concrete_values = {'s': 'abcdef'}
    s = fuzzy.mk_str('s')
    t = 'foo' + s + 'bar'
    if not isinstance(t, fuzzy.concolic_str):
        raise MyException("ERROR: lost concolic object after concat")
    if 'ooabc' not in t:
        raise MyException("ERROR: wrong boolean for contains")
    if len(fuzzy.cur_path_constr) == 0:
        raise MyException("ERROR: no path constraint")
    if len(fuzzy.cur_path_constr) > 1:
        raise MyException("ERROR: too many path constraints")
    fuzzy.cur_path_constr = []
    if 'ooxx' in t:
        raise MyException("ERROR: wrong boolean for contains, take 2")
    (ok, model) = fuzzy.fork_and_check(fuzzy.sym_not(fuzzy.cur_path_constr[0]))
    if ok != z3.sat:
        raise MyException("ERROR: unsolvable constraint")
    if 'xx' not in model['s']:
        raise MyException("ERROR: wrong value in solved constraint")
    print "Contains works"
except MyException:
    traceback.print_exc(None, sys.stdout)

