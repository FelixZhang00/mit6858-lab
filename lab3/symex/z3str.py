## Figure out where the z3str library lives
import os
z3strdir = os.path.dirname(os.path.abspath(__file__))

## Change the python path to load our Z3 python bindings, just in case
import sys
sys.path = [z3strdir + '/z3py'] + sys.path

## Force Z3's python bindings to load the libz3str.so library
import z3
def find_lib_stub():
  return z3strdir + '/libz3str.so'
z3.z3core._find_lib = find_lib_stub

## Enable ctypes for the z3str_*() functions in libz3str.so
import ctypes
z3strlib = z3.z3core.lib()
z3strlib.z3str_context.restype = z3.ContextObj
z3strlib.z3str_context.argtypes = []
z3strlib.z3str_mk_string_sort.restype = z3.Sort
z3strlib.z3str_mk_string_sort.argtypes = []
z3strlib.z3str_concat_decl.restype = z3.FuncDecl
z3strlib.z3str_concat_decl.argtypes = []
z3strlib.z3str_length_decl.restype = z3.FuncDecl
z3strlib.z3str_length_decl.argtypes = []
z3strlib.z3str_substring_decl.restype = z3.FuncDecl
z3strlib.z3str_substring_decl.argtypes = []
z3strlib.z3str_indexof_decl.restype = z3.FuncDecl
z3strlib.z3str_indexof_decl.argtypes = []
z3strlib.z3str_contains_decl.restype = z3.FuncDecl
z3strlib.z3str_contains_decl.argtypes = []
z3strlib.z3str_startswith_decl.restype = z3.FuncDecl
z3strlib.z3str_startswith_decl.argtypes = []
z3strlib.z3str_endswith_decl.restype = z3.FuncDecl
z3strlib.z3str_endswith_decl.argtypes = []
z3strlib.z3str_replace_decl.restype = z3.FuncDecl
z3strlib.z3str_replace_decl.argtypes = []
z3strlib.z3str_register_vars.restype = None
z3strlib.z3str_register_vars.argtypes = [z3.Ast]
z3strlib.setAlphabet.restype = None
z3strlib.setAlphabet.argtypes = []
z3strlib.setAlphabet7bit.restype = None
z3strlib.setAlphabet7bit.argtypes = []

## Set the default Z3py context to use z3str
ctx = z3.main_ctx()
ctx.ctx = z3strlib.z3str_context()
z3strlib.setAlphabet7bit()

## Wrappers around the various z3str_*() functions in libz3str.so
def StringSort():
  ctx = z3.main_ctx()
  sort = z3strlib.z3str_mk_string_sort()
  return z3.SortRef(sort, ctx)

def string_concat():
  ctx = z3.main_ctx()
  decl = z3strlib.z3str_concat_decl()
  return z3.FuncDeclRef(decl, ctx)

def string_length():
  ctx = z3.main_ctx()
  decl = z3strlib.z3str_length_decl()
  return z3.FuncDeclRef(decl, ctx)

def string_substring():
  ctx = z3.main_ctx()
  decl = z3strlib.z3str_substring_decl()
  return z3.FuncDeclRef(decl, ctx)

def string_indexof():
  ctx = z3.main_ctx()
  decl = z3strlib.z3str_indexof_decl()
  return z3.FuncDeclRef(decl, ctx)

def string_contains():
  ctx = z3.main_ctx()
  decl = z3strlib.z3str_contains_decl()
  return z3.FuncDeclRef(decl, ctx)

def string_startswith():
  ctx = z3.main_ctx()
  decl = z3strlib.z3str_startswith_decl()
  return z3.FuncDeclRef(decl, ctx)

def string_endswith():
  ctx = z3.main_ctx()
  decl = z3strlib.z3str_endswith_decl()
  return z3.FuncDeclRef(decl, ctx)

def string_replace():
  ctx = z3.main_ctx()
  decl = z3strlib.z3str_replace_decl()
  return z3.FuncDeclRef(decl, ctx)

def z3str_register(expr):
  z3strlib.z3str_register_vars(expr.as_ast())

## Wrapper around Z3's old solver API; unfortunately, z3str seems
## to work only with the old solver API, and not with the new one.
##
## WARNING: z3str does not seem to clean up in-memory state after
## solving, so it's probably best to fork off a separate process
## to invoke z3str_check_and_model(), and then send the results
## to the parent process using a non-Z3 representation like JSON.
def check_and_model(expr):
  z3str_register(expr)
  z3.z3core.Z3_assert_cnstr(ctx.ctx, expr.as_ast())

  _m = z3.Model(None)
  _ok = z3.z3core.Z3_check_and_get_model(ctx.ctx, ctypes.byref(_m))
  ok = z3.CheckSatResult(_ok)
  if ok == z3.sat:
    m = z3.ModelRef(_m, ctx)
    return (ok, m)
  else:
    return (ok, None)

Concat = string_concat()
Length = string_length()
SubString = string_substring()
Indexof = string_indexof()
Contains = string_contains()
StartsWith = string_startswith()
EndsWith = string_endswith()
Replace = string_replace()

