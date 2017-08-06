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
    fuzzy.concrete_values = {'x': 10}
    x = fuzzy.mk_int('x')
    y = x * 2
    if not isinstance(y, fuzzy.concolic_int):
        raise MyException("ERROR: lost concolic object after multiply")
    if y != 20:
        raise MyException("ERROR: wrong concrete value for concolic object")
    if len(fuzzy.cur_path_constr) == 0:
        raise MyException("ERROR: no path constraint from equality check")
    if len(fuzzy.cur_path_constr) > 1:
        raise MyException("ERROR: too many path constraints from equality check")
    fuzzy.cur_path_constr = []
    if y == 70:
        raise MyException("ERROR: wrong concrete value for concolic object, take 2")
    (ok, model) = fuzzy.fork_and_check(fuzzy.sym_not(fuzzy.cur_path_constr[0]))
    if ok != z3.sat:
        raise MyException("ERROR: unsolvable constraint")
    if model['x'] != 35:
        raise MyException("ERROR: wrong value in solved constraint")
    print "Multiply works"
except MyException:
    traceback.print_exc(None, sys.stdout)

try:
    fuzzy.cur_path_constr = []
    fuzzy.concrete_values = {'x': 10}
    x = fuzzy.mk_int('x')
    y = x / 2
    if not isinstance(y, fuzzy.concolic_int):
        raise MyException("ERROR: lost concolic object after divide")
    if y != 5:
        raise MyException("ERROR: wrong concrete value for concolic object")
    if len(fuzzy.cur_path_constr) == 0:
        raise MyException("ERROR: no path constraint from equality check")
    if len(fuzzy.cur_path_constr) > 1:
        raise MyException("ERROR: too many path constraints from equality check")
    fuzzy.cur_path_constr = []
    if y == 70:
        raise MyException("ERROR: wrong concrete value for concolic object, take 2")
    (ok, model) = fuzzy.fork_and_check(fuzzy.sym_not(fuzzy.cur_path_constr[0]))
    if ok != z3.sat:
        raise MyException("ERROR: unsolvable constraint")
    if model['x'] != 140:
        raise MyException("ERROR: wrong value in solved constraint")
    print "Divide works"
except MyException:
    traceback.print_exc(None, sys.stdout)

try:
    fuzzy.cur_path_constr = []
    concrete_values = {'x': 10}
    x = fuzzy.mk_int('x')
    y = (x / 2) * 4 + 3
    if not isinstance(y, fuzzy.concolic_int):
        raise MyException("ERROR: lost concolic object after divide+multiply+add")
    if y != 23:
        raise MyException("ERROR: wrong concrete value for concolic object")
    if len(fuzzy.cur_path_constr) == 0:
        raise MyException("ERROR: no path constraint from equality check")
    if len(fuzzy.cur_path_constr) > 1:
        raise MyException("ERROR: too many path constraints from equality check")
    fuzzy.cur_path_constr = []
    if y == 143:
        raise MyException("ERROR: wrong concrete value for concolic object, take 2")
    (ok, model) = fuzzy.fork_and_check(fuzzy.sym_not(fuzzy.cur_path_constr[0]))
    if ok != z3.sat:
        raise MyException("ERROR: unsolvable constraint")
    if model['x'] != 70:
        raise MyException("ERROR: wrong value in solved constraint")
    print "Divide+multiply+add works"
except MyException:
    traceback.print_exc(None, sys.stdout)

