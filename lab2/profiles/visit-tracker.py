#!python
import time, errno

global api
selfuser = api.call('get_self')
visitor = api.call('get_visitor')

visit_count = 0
visit_last = 'never'
fn = 'last_visit_%s_%s.dat' % (selfuser, visitor)
try:
  with open(fn) as f:
    visit_count = int(f.readline())
    visit_last = f.readline()
except IOError, e:
  if e.errno == errno.ENOENT:
    pass
except ValueError:
  pass

print 'Hello, <i>', visitor, '</i>'
print '<p>Your visit count:', visit_count
print '<p>Your last visit:', visit_last

visit_count += 1
visit_last = time.time()

with open(fn, 'w') as f:
  f.write(str(visit_count) + '\n')
  f.write(str(visit_last) + '\n')
