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

    i=0
    while ! curl --connect-timeout 1 -s $HOST:$PORT &>/dev/null; do
        ((i=i+1))
        if ((i>5)); then
            echo "failed to connect to $HOST:$PORT"
            exit 1
        fi
        sleep .1
    done
}

# colors from http://stackoverflow.com/questions/4332478/read-the-current-text-color-in-a-xterm/4332530#4332530
NORMAL=$(tput sgr0)
RED=$(tput setaf 1)
FAIL="[ ${RED}FAIL${NORMAL} ]"
OHNO="[ ${RED}OHNO${NORMAL} ]"
GREEN=$(tput setaf 2)
PASS="[ ${GREEN}PASS${NORMAL} ]"
BLUE=$(tput setaf 4)
INFO="[ ${BLUE}INFO${NORMAL} ]"
YELLOW=$(tput setaf 3)
DOTS="[ ${YELLOW}....${NORMAL} ]"

run_test() {
    printf "${INFO}: Testing exploit for $1...\n"
    setup_server
    $HOME/phantomjs $2 .
}

cleanup
trap cleanup EXIT

./get-phantomjs.sh

echo "Generating reference images..."
setup_server
$HOME/phantomjs lab4-tests/make-reference-images.js

### Part 1 ###
run_test "Exercise 1" lab4-tests/grade-ex01.js
run_test "Exercise 2" lab4-tests/grade-ex02.js
run_test "Exercise 3" lab4-tests/grade-ex03.js
run_test "Exercise 4" lab4-tests/grade-ex04.js
run_test "Exercise 5" lab4-tests/grade-ex05.js

### Part 2 ###
run_test "Exercise 6" lab4-tests/grade-ex06.js
run_test "Exercise 7" lab4-tests/grade-ex07.js
run_test "Exercise 8" lab4-tests/grade-ex08.js

### Part 3 ###
run_test "Exercise 9" lab4-tests/grade-ex09.js
run_test "Exercise 10" lab4-tests/grade-ex10.js
run_test "Exercise 11" lab4-tests/grade-ex11.js
run_test "Exercise 12" lab4-tests/grade-ex12.js
run_test "Exercise 13" lab4-tests/grade-ex13.js

### Challenge ###
run_test "Challenge" lab4-tests/grade-chal.js

### Part 4 ###
run_test "Exercise 14" lab4-tests/grade-ex14.js
