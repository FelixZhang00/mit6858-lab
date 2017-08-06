import __builtin__
import inspect
import fuzzy

def str_to_small_int(s):
  sign = 1
  digitpos = 0

  if s.startswith('-'):
    sign = -1
    digitpos = 1

  if s[digitpos:] == '0':
    return 0
  elif s[digitpos:] == '1':
    return sign * 1
  elif s[digitpos:] == '10':
    return sign * 10
  elif s[digitpos:] == '100':
    return sign * 100
  return None

real_eval = __builtin__.eval
def myeval(expr, globals = None, locals = None):
  if ';badstuff();' in expr:
    raise Exception("eval injection")
  if locals is None and globals is not None:
    locals = globals
  if locals is None and globals is None:
    frame = inspect.currentframe()
    try:
      locals = frame.f_back.f_locals
      globals = frame.f_back.f_globals
    finally:
      del frame

  ## Try to evaluate the expression as an integer
  v = str_to_small_int(expr)
  if v is not None:
    return v

  return real_eval(expr, globals, locals)
__builtin__.eval = myeval

def symint(x, base = 10):
  if base == 10 and isinstance(x, fuzzy.concolic_str):
    i = str_to_small_int(x)
    if i is not None:
      return i
  return int(x, base)
__builtin__.symint = symint
