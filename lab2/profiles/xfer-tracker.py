#!python
import sys

global api
selfuser = api.call('get_self')
visitor = api.call('get_visitor')

for xfer in api.call('get_xfers', username=selfuser):
  if xfer['sender'] == visitor:
    print 'You gave me', xfer['amount'], 'zoobars @', xfer['time']
    sys.exit(0)
  if xfer['recipient'] == visitor:
    print 'I gave you', xfer['amount'], 'zoobars @', xfer['time']
    sys.exit(0)

print 'We never exchanged zoobars!'
