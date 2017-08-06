#!/usr/bin/python

import sys
import re
import pprint
import collections

Head = collections.namedtuple("Head", "file line")

def parse(pn):
    ans = collections.defaultdict(str)

    head = None
    for l in open(pn):
        # ignore comments
        if l.startswith("#"):
            continue

        # found a header
        m = re.match("^\[(\S+):(\d+)\]+.*", l)
        if m:
            head = Head._make(m.groups())
            continue

        # collect descriptions
        if head:
            ans[head] += l

    # chomp
    return dict((h, d.strip()) for (h, d) in ans.items())

def say_pass(reason):
    print "\033[1;32mPASS\033[m", reason

def say_fail(reason):
    print "\033[1;31mFAIL\033[m", reason
    
def stat_summary(ans):
    print("Summary:")
    for (h, d) in ans.items():
        desc = d.split("\n")[0]
        print(" %-8s %+4s | %-30s .." % (h.file, h.line, desc))

    if len(ans) >= 5:
        say_pass("found enough bugs")
    else:
        say_fail("found %s bugs, but need at least 5" % len(ans))

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("usage: %s [bugs.txt]", sys.argv[0])
        exit(1)
    
    ans = parse(sys.argv[1])
    stat_summary(ans)
    
