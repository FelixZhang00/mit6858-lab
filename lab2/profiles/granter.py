#!python
import sys, time, errno

global api
selfuser = api.call('get_self')
visitor = api.call('get_visitor')

me = api.call('get_user_info', username=selfuser)
if me['zoobars'] <= 0:
  print 'Sorry, I have no more zoobars'
  sys.exit(0)

you = api.call('get_user_info', username=visitor)
if you['zoobars'] > 20:
  print 'You have', you['zoobars'], 'already; no need for more'
  sys.exit(0)

last_fn = 'last_freebie_%s_%s.dat' % (selfuser, visitor)
last_xfer = 0
try:
  with open(last_fn) as f:
    last_xfer = float(f.read())
except IOError, e:
  if e.errno == errno.ENOENT:
    pass

now = time.time()
if now - last_xfer < 60:
  print 'I gave you a zoobar %.1f seconds ago' % (now-last_xfer)
  sys.exit(0)

api.call('xfer', target=visitor, zoobars=1)
print 'Thanks for visiting.  I gave you one zoobar.'

with open(last_fn, 'w') as f:
  f.write(str(now))

