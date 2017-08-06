import importwrapper
import types
import byteplay
import __builtin__

def mkstr(s):
  if isinstance(s, str):
    return s
  if isinstance(s, unicode):
    return s
  return str(s)

def __rewriter_pct(a, b):
  orig = a % b
  origa = a
  origb = b
  if isinstance(a, str) or isinstance(a, unicode):
    res = ''
    while True:
      pos = a.find('%')
      if pos < 0:
        # if res+a != orig: print '__rewriter_pct mismatch:', res+a, orig
        return res + a
      res += a[0:pos]
      a = a[pos:]
      if a[1] == 's':
        if isinstance(b, tuple):
          v = b[0]
          b = b[1:]
        else:
          v = b
        res = res + mkstr(v)
        a = a[2:]
      elif a[1] == '(':
        pos = a.find(')')
        if pos < 0:
          break
        name = a[2:pos]
        if a[pos+1] != 's':
          break
        res += mkstr(b[name])
        a = a[pos+2:]
      else:
        break

    ## couldn't figure out this pattern..
    # print "__rewriter_pct: bailing out on pattern", origa
    return orig
  else:
    return orig

def __rewriter_in(a, b):
  if not isinstance(b, dict) and \
     not isinstance(b, set) and \
     not isinstance(b, list) and \
     not isinstance(b, tuple):
    return a in b
  for k in b:
    if a == k:
      return True
  return False

def __rewriter_not_in(a, b):
  return not __rewriter_in(a, b)

def __rewriter_load_attr_get(a):
  if not isinstance(a, dict):
    return getattr(a, 'get')

  def newget(b, default = None):
    for (k, v) in a.items():
      if b == k:
        return v
    return default

  return newget

def __rewriter_eq(a, b):
  if isinstance(a, unicode):
    ## unicode.__eq__ would coerce the RHS into a unicode object,
    ## even if it was a concolic_str, so reverse the equality check
    ## to give concolic_str.__eq__ a chance to run.
    return b == a
  return a == b

## Stick our replacement functions into the __builtin__ module
## so they are in the namespace of any function we're rewriting.
__builtin__.__rewriter_pct = __rewriter_pct
__builtin__.__rewriter_in = __rewriter_in
__builtin__.__rewriter_not_in = __rewriter_not_in
__builtin__.__rewriter_load_attr_get = __rewriter_load_attr_get
__builtin__.__rewriter_eq = __rewriter_eq

def rewrite_function(f):
  if not hasattr(f, 'func_code'):
    return

  c = byteplay.Code.from_code(f.func_code)
  newcode = byteplay.CodeList()
  for i in c.code:
    if i[0] == byteplay.BINARY_MODULO:
      newcode.append((byteplay.LOAD_GLOBAL, '__rewriter_pct'))
      newcode.append((byteplay.ROT_THREE, None))
      newcode.append((byteplay.CALL_FUNCTION, 2))
    elif i == (byteplay.COMPARE_OP, 'in'):
      newcode.append((byteplay.LOAD_GLOBAL, '__rewriter_in'))
      newcode.append((byteplay.ROT_THREE, None))
      newcode.append((byteplay.CALL_FUNCTION, 2))
    elif i == (byteplay.COMPARE_OP, 'not in'):
      newcode.append((byteplay.LOAD_GLOBAL, '__rewriter_not_in'))
      newcode.append((byteplay.ROT_THREE, None))
      newcode.append((byteplay.CALL_FUNCTION, 2))
    elif i == (byteplay.COMPARE_OP, '=='):
      newcode.append((byteplay.LOAD_GLOBAL, '__rewriter_eq'))
      newcode.append((byteplay.ROT_THREE, None))
      newcode.append((byteplay.CALL_FUNCTION, 2))
    elif i == (byteplay.LOAD_ATTR, 'get'):
      newcode.append((byteplay.LOAD_GLOBAL, '__rewriter_load_attr_get'))
      newcode.append((byteplay.ROT_TWO, None))
      newcode.append((byteplay.CALL_FUNCTION, 1))
    else:
      newcode.append(i)
  c.code = newcode
  try:
    f.func_code = c.to_code()
  except:
    print "Cannot assemble bytecode for", f
    print c.code
    raise

def rewriter(m):
  # print 'rewriting', m
  for k in dir(m):
    if k.startswith('__') and k.endswith('__'):
      continue
    try:
      v = getattr(m, k)
    except AttributeError:
      ## SQLalchemy has some attributes backed by a getter that
      ## can throw an exception..
      continue
    if type(v) == types.FunctionType:
      rewrite_function(v)
    elif type(v) == types.MethodType:
      rewrite_function(v.im_func)
    elif type(v) == types.TypeType:
      rewriter(v)
    elif type(v) == types.ClassType:
      rewriter(v)
    elif 'werkzeug.utils.cached_property' in str(type(v)):
      ## XXX what a hack!  we should really do the rewriting earlier,
      ## perhaps when the code is first loaded by Python.  but it's
      ## not clear how to do that..
      rewriter(v)
    else:
      # print "Not rewriting", k, "type", type(v)
      pass
