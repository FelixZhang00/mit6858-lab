import importlib
import sys

## This uses PEP-302: http://legacy.python.org/dev/peps/pep-0302/

class RewriteLoader(object):
  def __init__(self, module):
    self.module = module

  def load_module(self, module_name):
    return self.module

class RewriteFinder(object):
  def __init__(self, rewriter):
    self.active = set()
    self.rewriter = rewriter

  def find_module(self, module_name, path_entry = None):
    if module_name in self.active:
      return None

    # print "find_module", module_name, path_entry
    try:
      self.active.add(module_name)
      m = importlib.import_module(module_name)
    except ImportError:
      return None
    finally:
      self.active.remove(module_name)

    self.rewriter(m)
    return RewriteLoader(m)

def rewrite_imports(rewriter):
  sys.meta_path.append(RewriteFinder(rewriter))

