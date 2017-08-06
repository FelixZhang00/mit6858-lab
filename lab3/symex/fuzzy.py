import z3str
import z3
import multiprocessing
import sys
import collections
import Queue
import signal
import operator
import inspect
import __builtin__

## Our AST structure

class sym_ast(object):
  def __str__(self):
    return str(self._z3expr(True))

class sym_func_apply(sym_ast):
  def __init__(self, *args):
    for a in args:
      if not isinstance(a, sym_ast):
        raise Exception("Passing a non-AST node %s %s as argument to %s" % \
                        (a, type(a), type(self)))
    self.args = args

  def __eq__(self, o):
    if type(self) != type(o):
      return False
    if len(self.args) != len(o.args):
      return False
    return all(sa == oa for (sa, oa) in zip(self.args, o.args))

  def __hash__(self):
    return reduce(operator.xor, [hash(a) for a in self.args], 0)

class sym_unop(sym_func_apply):
  def __init__(self, a):
    super(sym_unop, self).__init__(a)

  @property
  def a(self):
    return self.args[0]

class sym_binop(sym_func_apply):
  def __init__(self, a, b):
    super(sym_binop, self).__init__(a, b)

  @property
  def a(self):
    return self.args[0]

  @property
  def b(self):
    return self.args[1]

class sym_triop(sym_func_apply):
  def __init__(self, a, b, c):
    super(sym_triop, self).__init__(a, b, c)

  @property
  def a(self):
    return self.args[0]

  @property
  def b(self):
    return self.args[1]

  @property
  def c(self):
    return self.args[2]

def z3expr(o, printable = False):
  assert isinstance(o, sym_ast)
  return o._z3expr(printable)

class const_str(sym_ast):
  def __init__(self, v):
    self.v = v

  def __eq__(self, o):
    if not isinstance(o, const_str):
      return False
    return self.v == o.v

  def __hash__(self):
    return hash(self.v)

  def _z3expr(self, printable):
    ## z3str has a weird way of encoding string constants.
    ## for printing, we make strings look like nice constants,
    ## but otherwise we use z3str's encoding plan.
    if printable:
      return z3.Const('"%s"' % self.v, z3str.StringSort())

    enc = "__cOnStStR_" + "".join(["_x%02x" % ord(c) for c in self.v])
    return z3.Const(enc, z3str.StringSort())

class const_int(sym_ast):
  def __init__(self, i):
    self.i = i

  def __eq__(self, o):
    if not isinstance(o, const_int):
      return False
    return self.i == o.i

  def __hash__(self):
    return hash(self.i)

  def _z3expr(self, printable):
    return self.i

class const_bool(sym_ast):
  def __init__(self, b):
    self.b = b

  def __eq__(self, o):
    if not isinstance(o, const_bool):
      return False
    return self.b == o.b

  def __hash__(self):
    return hash(self.b)

  def _z3expr(self, printable):
    return self.b

def ast(o):
  if hasattr(o, '_sym_ast'):
    return o._sym_ast()
  if isinstance(o, bool):
    return const_bool(o)
  if isinstance(o, int):
    return const_int(o)
  if isinstance(o, str) or isinstance(o, unicode):
    return const_str(o)
  raise Exception("Trying to make an AST out of %s %s" % (o, type(o)))

## Logic expressions

class sym_eq(sym_binop):
  def _z3expr(self, printable):
    return z3expr(self.a, printable) == z3expr(self.b, printable)

class sym_and(sym_func_apply):
  def _z3expr(self, printable):
    return z3.And(*[z3expr(a, printable) for a in self.args])

class sym_or(sym_func_apply):
  def _z3expr(self, printable):
    return z3.Or(*[z3expr(a, printable) for a in self.args])

class sym_not(sym_unop):
  def _z3expr(self, printable):
    return z3.Not(z3expr(self.a, printable))

## Arithmetic

class sym_int(sym_ast):
  def __init__(self, id):
    self.id = id

  def __eq__(self, o):
    if not isinstance(o, sym_int):
      return False
    return self.id == o.id

  def __hash__(self):
    return hash(self.id)

  def _z3expr(self, printable):
    return z3.Int(self.id)

class sym_lt(sym_binop):
  def _z3expr(self, printable):
    return z3expr(self.a, printable) < z3expr(self.b, printable)

class sym_gt(sym_binop):
  def _z3expr(self, printable):
    return z3expr(self.a, printable) > z3expr(self.b, printable)

class sym_plus(sym_binop):
  def _z3expr(self, printable):
    return z3expr(self.a, printable) + z3expr(self.b, printable)

class sym_minus(sym_binop):
  def _z3expr(self, printable):
    return z3expr(self.a, printable) - z3expr(self.b, printable)

## Exercise 2: your code here.
## Implement AST nodes for division and multiplication.
class sym_mul(sym_binop):
  def _z3expr(self,printable):
    return z3expr(self.a,printable) * z3expr(self.b,printable)

class sym_div(sym_binop):
  def _z3expr(self,printable):
    return z3expr(self.a,printable) / z3expr(self.b,printable)


## String operations

class sym_str(sym_ast):
  def __init__(self, id):
    self.id = id

  def __eq__(self, o):
    if not isinstance(o, sym_str):
      return False
    return self.id == o.id

  def __hash__(self):
    return hash(self.id)

  def _z3expr(self, printable):
    return z3.Const(self.id, z3str.StringSort())

class sym_concat(sym_binop):
  def _z3expr(self, printable):
    return z3str.Concat(z3expr(self.a, printable),
                        z3expr(self.b, printable))

class sym_length(sym_unop):
  def _z3expr(self, printable):
    return z3str.Length(z3expr(self.a, printable))

class sym_substring(sym_triop):
  def _z3expr(self, printable):
    return z3str.SubString(z3expr(self.a, printable),
                           z3expr(self.b, printable),
                           z3expr(self.c, printable))

class sym_indexof(sym_binop):
  def _z3expr(self, printable):
    return z3str.Indexof(z3expr(self.a, printable),
                         z3expr(self.b, printable))

class sym_contains(sym_binop):
  def _z3expr(self, printable):
    return z3str.Contains(z3expr(self.a, printable),
                          z3expr(self.b, printable))

class sym_startswith(sym_binop):
  def _z3expr(self, printable):
    return z3str.StartsWith(z3expr(self.a, printable),
                            z3expr(self.b, printable))

class sym_endswith(sym_binop):
  def _z3expr(self, printable):
    return z3str.EndsWith(z3expr(self.a, printable),
                          z3expr(self.b, printable))

class sym_replace(sym_triop):
  def _z3expr(self, printable):
    return z3str.Replace(z3expr(self.a, printable),
                         z3expr(self.b, printable),
                         z3expr(self.c, printable))

## Symbolic simplifications

class patname(sym_ast):
  def __init__(self, name, pattern = None):
    self.name = name
    self.pattern = pattern

simplify_patterns = [
  (sym_substring(patname("a",
                         sym_substring(patname("b"),
                                       patname("c"),
                                       sym_minus(sym_length(patname("b")),
                                                 patname("c")))),
                 patname("d"),
                 sym_minus(sym_length(patname("a")),
                           patname("d"))),
   sym_substring(patname("b"),
                 sym_plus(patname("c"), patname("d")),
                 sym_minus(sym_length(patname("b")),
                           sym_plus(patname("c"), patname("d"))))
  ),
  (sym_concat(patname("a"), const_str("")),
   patname("a")
  ),
]

def pattern_match(expr, pat, vars):
  if isinstance(pat, patname):
    if pat.name in vars:
      return expr == vars[pat.name]
    else:
      vars[pat.name] = expr
      if pat.pattern is None:
        return True
      return pattern_match(expr, pat.pattern, vars)

  if type(expr) != type(pat):
    return False

  if not isinstance(expr, sym_func_apply):
    return expr == pat

  if len(expr.args) != len(pat.args):
    return False

  return all(pattern_match(ea, pa, vars)
             for (ea, pa) in zip(expr.args, pat.args))

def pattern_build(pat, vars):
  if isinstance(pat, patname):
    return vars[pat.name]
  if isinstance(pat, sym_func_apply):
    args = [pattern_build(pa, vars) for pa in pat.args]
    return type(pat)(*args)
  return pat

def simplify(e):
  matched = True
  while matched:
    matched = False
    for (src, dst) in simplify_patterns:
      vars = {}
      if not pattern_match(e, src, vars):
        continue
      e = pattern_build(dst, vars)
      matched = True

  if isinstance(e, sym_func_apply):
    t = type(e)
    args = [simplify(a) for a in e.args]
    return t(*args)

  return e

## Current path constraint

cur_path_constr = None
cur_path_constr_callers = None

def get_caller():
  frame = inspect.currentframe()
  try:
    while True:
      info = inspect.getframeinfo(frame)
      ## Skip stack frames inside the symbolic execution engine,
      ## as well as in the rewritten replacements of dict, %, etc.
      if not info.filename.endswith('fuzzy.py') and\
         not info.filename.endswith('rewriter.py'):
        return (info.filename, info.lineno)
      frame = frame.f_back
  finally:
    del frame

def add_constr(e):
  global cur_path_constr, cur_path_constr_callers
  cur_path_constr.append(simplify(e))
  cur_path_constr_callers.append(get_caller())

## This exception is thrown when a required symbolic condition
## is not met; the symbolic execution engine should retry with
## a different input to go down another path instead.
class RequireMismatch(Exception):
  pass

def require(e):
  if not e:
    raise RequireMismatch()

## Creating new symbolic names

namectr = 0
def uniqname(id):
  global namectr
  namectr += 1
  return "%s_%d" % (id, namectr)

## Helper for printing Z3-indented expressions

def indent(s, spaces = '  '):
  return spaces + str(s).replace('\n', '\n' + spaces)

## Support for forking because z3str uses lots of global variables

## timeout for Z3, in seconds
z3_timeout = 5

def fork_and_check_worker(constr, conn):
  z3e = z3expr(constr)
  (ok, z3m) = z3str.check_and_model(z3e)
  m = {}
  if ok == z3.sat:
    for k in z3m:
      v = z3m[k]
      if v.sort() == z3.IntSort():
        m[str(k)] = v.as_long()
      elif v.sort() == z3str.StringSort():
        # print "Model string %s: %s" % (k, v)
        vs = str(v)
        if not vs.startswith('__cOnStStR_'):
          if not str(k).startswith('_t_'):
            print 'Undecodable string constant (%s): %s' % (k, vs)
          continue
        hexbytes = vs.split('_x')[1:]
        bytes = [int(h, 16) for h in hexbytes]
        m[str(k)] = ''.join(chr(x) for x in bytes)
      else:
        raise Exception("Unknown sort for %s=%s: %s" % (k, v, v.sort()))
  conn.send((ok, m))
  conn.close()

def fork_and_check(constr):
  constr = simplify(constr)

  parent_conn, child_conn = multiprocessing.Pipe()
  p = multiprocessing.Process(target=fork_and_check_worker,
                              args=(constr, child_conn))
  p.start()
  child_conn.close()

  ## timeout after a while..
  def sighandler(signo, stack):
    print "Timed out.."
    # print z3expr(constr, True).sexpr()
    p.terminate()

  signal.signal(signal.SIGALRM, sighandler)
  signal.alarm(z3_timeout)

  try:
    res = parent_conn.recv()
  except EOFError:
    res = (z3.unknown, None)
  finally:
    signal.alarm(0)

  p.join()
  return res

## Symbolic type replacements

def concolic_bool(sym, v):
  ## Python claims that 'bool' is not an acceptable base type,
  ## so it seems difficult to subclass bool.  Luckily, bool has
  ## only two possible values, so whenever we get a concolic
  ## bool, add its value to the constraint.
  add_constr(sym_eq(sym, ast(v)))
  return v

class concolic_int(int):
  def __new__(cls, sym, v):
    self = super(concolic_int, cls).__new__(cls, v)
    self.__v = v
    self.__sym = sym
    return self

  def __eq__(self, o):
    if not isinstance(o, int):
      return False

    if isinstance(o, concolic_int):
      res = (self.__v == o.__v)
    else:
      res = (self.__v == o)

    return concolic_bool(sym_eq(ast(self), ast(o)), res)

  def __ne__(self, o):
    return not self.__eq__(o)

  def __cmp__(self, o):
    res = long(self.__v).__cmp__(long(o))
    if concolic_bool(sym_lt(ast(self), ast(o)), res < 0):
      return -1
    if concolic_bool(sym_gt(ast(self), ast(o)), res > 0):
      return 1
    return 0

  def __add__(self, o):
    if isinstance(o, concolic_int):
      res = self.__v + o.__v
    else:
      res = self.__v + o
    return concolic_int(sym_plus(ast(self), ast(o)), res)

  def __radd__(self, o):
    res = o + self.__v
    return concolic_int(sym_plus(ast(o), ast(self)), res)

  def __sub__(self, o):
    res = self.__v - o
    return concolic_int(sym_minus(ast(self), ast(o)), res)

  ## Exercise 2: your code here.
  ## Implement symbolic division and multiplication.
		
  def __mul__(self,o):
    res = self.__v * o
    return concolic_int(sym_mul(ast(self),ast(o)),res)		

  def __div__(self,o):
    res = self.__v / o
    return concolic_int(sym_div(ast(self),ast(o)),res)		

  def _sym_ast(self):
    return self.__sym

class concolic_str(str):
  def __new__(cls, sym, v):
    assert type(v) == str or type(v) == unicode
    self = super(concolic_str, cls).__new__(cls, v)
    self.__v = v
    self.__sym = sym
    return self

  def __eq__(self, o):
    if not isinstance(o, str) and not isinstance(o, unicode):
      return False

    if isinstance(o, concolic_str):
      res = (self.__v == o.__v)
    else:
      res = (self.__v == o)

    return concolic_bool(sym_eq(ast(self), ast(o)), res)

  def __ne__(self, o):
    return not self.__eq__(o)

  def __add__(self, o):
    if isinstance(o, concolic_str):
      res = self.__v + o.__v
    else:
      res = self.__v + o
    return concolic_str(sym_concat(ast(self), ast(o)), res)

  def __radd__(self, o):
    res = o + self.__v
    return concolic_str(sym_concat(ast(o), ast(self)), res)

  ## Exercise 4: your code here.
  ## Implement symbolic versions of string length (override __len__)
  ## and contains (override __contains__).
  def __len__(self):
    res = len(self.__v)
    return concolic_int(sym_length(ast(self)),res)

  def __contains__(self,o):
    if isinstance(o, concolic_str):
      res = self.__v.__contains__(o.__v)
    else:
      res =  self.__v.__contains__(o) 
    return concolic_bool(sym_contains(ast(self),ast(o)),res) 

  def startswith(self, o):
    res = self.__v.startswith(o)
    return concolic_bool(sym_startswith(ast(self), ast(o)), res)

  def endswith(self, o):
    res = self.__v.endswith(o)
    return concolic_bool(sym_endswith(ast(self), ast(o)), res)

  def __getitem__(self, i):
    res = self.__v[i]
    return concolic_str(sym_substring(ast(self), ast(i), ast(1)), res)

  def __getslice__(self, i, j):
    if j == 9223372036854775807 or j == 2147483647:
      ## Python passes in INT_MAX when there's no upper bound.
      ## Unfortunately, this differs depending on whether you're
      ## running in a 32-bit or a 64-bit system.
      j = self.__len__()
    res = self.__v[i:j]
    return concolic_str(sym_substring(ast(self), ast(i), ast(j-i)), res)

  def find(self, ch):
    res = self.__v.find(ch)
    return concolic_int(sym_indexof(ast(self), ast(ch)), res)

  def decode(self, encoding = sys.getdefaultencoding(), errors = 'strict'):
    ## XXX hack: we restrict z3str to just 7-bit ASCII (see call to
    ## setAlphabet7bit) and then pretend that str and unicode objects
    ## are the same.
    return self

  def encode(self, encoding = sys.getdefaultencoding(), errors = 'strict'):
    ## XXX same hack as for decode().
    return self

  def __unicode__(self):
    ## XXX same hack as for decode().
    return self

  def lstrip(self, chars = ' \t\n\r'):
    for ch in chars:
      if self.startswith(chars):
        return self[1:].lstrip(chars)
    return self

  def rsplit(self, sep = None, maxsplit = -1):
    if maxsplit != 1 or type(sep) != str:
      return self.__v.rsplit(sep, maxsplit)

    name = 'rsplit_%s_%s' % (self.__sym, sep)
    l = mk_str(name + '_l')
    r = mk_str(name + '_r')
    if l + sep + r != self:
      require(sep not in self)
      return self

    require(sep not in l)
    require(sep not in r)
    return (l, r)

  def upper(self):
    ## XXX an incorrect overloading that gets us past werkzeug's use
    ## of .upper() on the HTTP method name..
    return self

  def _sym_ast(self):
    return self.__sym

## Override some builtins..

old_len = __builtin__.len
def xlen(o):
  if isinstance(o, concolic_str):
    return o.__len__()
  return old_len(o)
__builtin__.len = xlen

## Track inputs that should be tried later

class InputQueue(object):
  def __init__(self):
    ## "inputs" is a priority queue storing inputs we should try.
    ## The inputs are stored as a dictionary, from symbolic variable
    ## name to the value we should try.  If a value is not present,
    ## mk_int() and mk_str() below will pick a default value.  Each
    ## input also has a priority (lower is "more important"), which
    ## is useful when there's too many inputs to process.
    self.inputs = Queue.PriorityQueue()
    self.inputs.put((0, {}))

    ## "branchcount" is a map from call site (filename and line number)
    ## to the number of branches we have already explored at that site.
    ## This is used to choose priorities for inputs.
    self.branchcount = collections.defaultdict(int)

  def empty(self):
    return self.inputs.empty()

  def get(self):
    (prio, values) = self.inputs.get()
    return values

  def add(self, new_values, caller):
    prio = self.branchcount[caller]
    self.branchcount[caller] += 1
    self.inputs.put((prio, new_values))

## Actual concolic execution API

concrete_values = {}

def mk_int(id):
  global concrete_values
  if id not in concrete_values:
    concrete_values[id] = 0
  return concolic_int(sym_int(id), concrete_values[id])

def mk_str(id):
  global concrete_values
  if id not in concrete_values:
    concrete_values[id] = ''
  return concolic_str(sym_str(id), concrete_values[id])

def concolic_test(testfunc, maxiter = 100, verbose = 0):
  ## "checked" is the set of constraints we already sent to Z3 for
  ## checking.  use this to eliminate duplicate paths.
  checked = set()

  ## list of inputs we should try to explore.
  inputs = InputQueue()

  iter = 0
  while iter < maxiter and not inputs.empty():
    iter += 1

    global concrete_values
    concrete_values = inputs.get()

    global cur_path_constr, cur_path_constr_callers
    cur_path_constr = []
    cur_path_constr_callers = []

    if verbose > 0:
      print 'Trying concrete values:', concrete_values
      #print inputs

    try:
      testfunc()
    except RequireMismatch:
      pass

    if verbose > 1:
      print 'Test generated', len(cur_path_constr), 'branches:'
      for (c, caller) in zip(cur_path_constr, cur_path_constr_callers):
        print indent(z3expr(c, True)), '@', '%s:%d' % (caller[0], caller[1])

    ## for each branch, invoke Z3 to find an input that would go
    ## the other way, and add it to the list of inputs to explore.

    ## Exercise 3: your code here.
    ##
    ## Here's a possible plan of attack:
    ##
    ## - Iterate over the set of branches in cur_path_constr.
    ##
    ## - Compute an AST expression for the constraints necessary
    ##   to go the other way on that branch.  You can use existing
    ##   logical AST combinators like sym_not(), sym_and(), etc.
    ##
    ##   Note that some of the AST combinators take separate positional
    ##   arguments. In Python, to unpack a list into separate positional
    ##   arguments, use the '*' operator documented at
    ##   https://docs.python.org/2/tutorial/controlflow.html#unpacking-argument-lists
    ##
    ## - If this constraint is already in the "checked" set, skip
    ##   it (otherwise, add it to prevent further duplicates).
    ##
    ## - Invoke Z3, along the lines of:
    ##
    ##     (ok, model) = fork_and_check(constr)
    ##
    ## - If Z3 was able to find example inputs that go the other
    ##   way on this branch, make a new input set containing the
    ##   values from Z3's model, and add it to the set of inputs
    ##   to consider:
    ##
    ##     inputs.add(new_values, caller)
    ##
    ##   where caller is the corresponding value from the list
    ##   of call sites (cur_path_constr_callers).
    ##
    ##   Note that Z3 might not assign values to every variable,
    ##   such as if that variable turns out to be irrelevant to
    ##   the overall constraint, so be sure to preserve values
    ##   from the initial input (concrete_values).
    # my code start..
    for i in range(len(cur_path_constr)):
      branch,caller = zip(cur_path_constr,cur_path_constr_callers)[i]   
      #branch is a symbolic constraint
      if verbose > 0:
        print branch,type(branch)
      args = [sym_not(branch)]+cur_path_constr[:i]
      branchn = sym_and(*args)
      
      # is this AST constraint is in the set checked,skip it,otherwise add it    
      if branchn in checked:
        if verbose > 0:
          print "already in checked"
        continue
      checked.add(branchn)
      
      #check for AST constraint via Z3
      (ok,model) = fork_and_check(branchn)
      if verbose > 0:
        print ok,model,type(model)

      #if sat,then create a new branch and add it to the set of input  
      if ok == z3.sat:
        inputs.add(model,caller)
        

  if verbose > 0:
    print 'Stopping after', iter, 'iterations'
