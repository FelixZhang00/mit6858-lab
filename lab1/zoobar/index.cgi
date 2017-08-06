#!/usr/bin/env python

from wsgiref.handlers import CGIHandler

from __init__ import *

if __name__ == "__main__":
    CGIHandler().run(app)
