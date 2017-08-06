#!/usr/bin/env python

import sys
import htmlfilter
from debug import *

print htmlfilter.filter_html(sys.stdin.read())

