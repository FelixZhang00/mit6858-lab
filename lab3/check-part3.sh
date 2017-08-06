#!/bin/bash

HOST=localhost
PORT=8080
GRAD=/home/httpd/grades.txt

cleanup() {
  killall -w zookld zookd zookfs zookd-nxstack zookfs-nxstack zookd-exstack zookfs-exstack &>/dev/null
}

PASS="\033[1;32mPASS\033[m"
FAIL="\033[1;31mFAIL\033[m"

cleanup
trap cleanup EXIT

# launch the server
script -q -f -c "./clean-env.sh ./zookld $1" /tmp/zookld.out &> /dev/null &

# wait until we can connect
sleep 1
if ! curl --connect-timeout 10 -s $HOST:$PORT &>/dev/null ; then
  echo "failed to connect to $HOST:$PORT"
  exit 1
fi

# create the grades file
touch "$GRAD" || exit 1

# run the script with a 5-second timeout.
$2 $HOST $PORT >/dev/null &
pid=$!
(sleep 5; kill -9 $pid &>/dev/null) &
wait $pid

# check if the grades file exists or not
if [ -f "$GRAD" ]; then
  echo -e "$FAIL $2"
else
  echo -e "$PASS $2"
fi
