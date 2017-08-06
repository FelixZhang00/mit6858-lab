#!python
import time
global api
print 'Hello, <i>', api.call('get_visitor'), '</i>'
print '<p>Current time:', time.time()
