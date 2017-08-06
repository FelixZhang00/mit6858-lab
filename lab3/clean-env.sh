#!/bin/bash
F="$1"
shift

ulimit -s unlimited

DIR=$(cd -P -- "$(dirname -- "$F")" && pwd -P)
FILE=$(basename -- "$F")
if [ "$DIR" != /home/httpd/lab ]; then
    echo "========================================================"
    echo "WARNING: Lab directory is $DIR"
    echo "Make sure your lab is checked out at /home/httpd/lab or"
    echo "your solutions may not work when grading."
    echo "========================================================"
fi
exec env - PWD="$DIR" SHLVL=0 "$DIR/$FILE" "$@"
