#!/bin/bash

HOST=localhost
PORT=8080
STRACELOG=/tmp/strace.log
need_cleanup=1

cleanup() {
  if [ "$need_cleanup" = 1 ]; then
    killall -w zookld zookd zookfs zookd-nxstack zookfs-nxstack zookd-exstack zookfs-exstack &> /dev/null
    need_cleanup=0
  fi
}

PASS="\033[1;32mPASS\033[m"
FAIL="\033[1;31mFAIL\033[m"

cleanup
trap cleanup EXIT

# launch the server. strace so we can see SEGVs.
strace -f -e none -o "$STRACELOG" ./clean-env.sh ./zookld $1 &> /dev/null &
need_cleanup=1

# wait until we can connect
sleep 1
if ! curl --connect-timeout 10 -s $HOST:$PORT &>/dev/null ; then
  echo "failed to connect to $HOST:$PORT"
  exit 1
fi

# run the script with a 5-second timeout.
$2 $HOST $PORT >/dev/null &
pid=$!
(sleep 5; kill -9 $pid &>/dev/null) &
wait $pid

# waiting in case the exploit exits before the SEGFAULT.
sleep 1

# stop the server
cleanup

# check that we got a SIGSEGV.
if grep SIGSEGV "$STRACELOG"; then
  echo -e "$PASS $2"
else
  echo -e "$FAIL $2"
fi

