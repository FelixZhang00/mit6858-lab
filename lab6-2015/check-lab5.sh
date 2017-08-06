#!/bin/bash

HOST=localhost
PORT=8080

need_cleanup=1

cleanup() {
    sudo killall -w zookld zookd zookfs zookd-nxstack zookfs-nxstack zookd-exstack zookfs-exstack auth-server.py echo-server.py bank-server.py profile-server.py &> /dev/null
}

setup_server() {
    cleanup
    make &> /dev/null
    sudo rm -rf zoobar/db &> /dev/null
    ( ./zookld & ) &> /tmp/zookld.out

    sleep 1
    if ! curl --connect-timeout 10 -s $HOST:$PORT &>/dev/null; then
        echo "failed to connect to $HOST:$PORT"
        exit 1
    fi
}

run_test() {
    echo "Cleaning up servers..."
    setup_server
    echo "Testing $1..."
    $HOME/phantomjs $2 .
}

cleanup
trap cleanup EXIT

./get-phantomjs.sh

echo "Generating reference images..."
setup_server
$HOME/phantomjs lab5-tests/make-reference-images.js

run_test "Exercise 1" lab5-tests/grade-ex1.js
run_test "Exercise 2" lab5-tests/grade-ex2.js
run_test "Exercise 3" lab5-tests/grade-ex3.js
run_test "Exercise 4" lab5-tests/grade-ex4.js
run_test "Challenge" lab5-tests/grade-chal.js
