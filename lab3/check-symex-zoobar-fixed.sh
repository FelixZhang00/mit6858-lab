#!/bin/sh

THISDIR=$(dirname $0)
THISDIR=$(cd $THISDIR && pwd)

rm -rf /tmp/lab3-fixed
mkdir /tmp/lab3-fixed
cp -r $THISDIR/* /tmp/lab3-fixed
cp -r $THISDIR/zoobar-fixed/* /tmp/lab3-fixed/zoobar
find /tmp/lab3-fixed -name '*.pyc' -print0 | xargs -0 rm -f

cd /tmp/lab3-fixed
exec ./check-symex-zoobar.py
