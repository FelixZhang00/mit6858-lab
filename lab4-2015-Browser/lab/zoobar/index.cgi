#!/usr/bin/env python2

from wsgiref.handlers import CGIHandler

from __init__ import *

if __name__ == "__main__":
    CGIHandler().run(app)
