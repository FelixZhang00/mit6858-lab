#!/bin/sh
THISYEAR=$(date +%Y)
COUNT=$(tar ztvf bin.tar.gz | awk '{print $4;}' | grep -c ^$THISYEAR)
if [ "$COUNT" != "5" ]; then
    echo "WARNING: bin.tar.gz might not have been built this year ($THISYEAR);"
    echo "WARNING: if $THISYEAR is correct, ask course staff to rebuild bin.tar.gz."
fi
