#!/bin/bash

DIFF="
1239c1239
<         self.path_info = to_unicode(path_info)
---
>         self.path_info = to_unicode(path_info or u'')
"

echo "$DIFF" | sudo patch /usr/lib/python2.7/dist-packages/werkzeug/routing.py && \
echo "Done"
