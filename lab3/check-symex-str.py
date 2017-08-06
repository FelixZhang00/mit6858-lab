#!/usr/bin/python

import symex.fuzzy as fuzzy

def g(s):
    if 'abc' in s:
        return "Found abc in s"
    if '' == s:
        return "Empty s"
    if len(s) > 30:
        return "Too long"
    if 'xyxy' == s + s:
        return "Found the xyxy double"
    if s.startswith('start'):
        return "Starts with start"
    if s.endswith('end'):
        return "Ends with end"
    if len(s) >= 4 and s[3] == 'q':
        return "4th character is q"
    return "Other stuff"

g_results = set()
def test_g():
    s = fuzzy.mk_str('s')
    v = g(s)
    print s, '->', v
    g_results.add(v)

print 'Testing g..'
fuzzy.concolic_test(test_g, verbose=10)
g_expected = ('Empty s', '4th character is q', 'Other stuff',
              'Found abc in s', 'Too long', 'Found the xyxy double',
              'Starts with start', 'Ends with end')
if all(x in g_results for x in g_expected):
    print "Found all cases for g"
else:
    print "Missing some cases for g:", set(g_expected) - set(g_results)
