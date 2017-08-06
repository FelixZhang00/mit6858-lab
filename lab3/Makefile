ASFLAGS := -m32
CFLAGS  := -m32 -g -std=c99 -Wall -Werror -D_GNU_SOURCE
LDFLAGS := -m32
LDLIBS  := -lcrypto
PROGS   := zookld zookfs zookd

all: $(PROGS)
.PHONY: all

zookld zookd zookfs: %: %.o http.o


.PHONY: check
check:
	./check_lab3.py



.PHONY: fix-flask
fix-flask: fix-flask.sh
	./fix-flask.sh

.PHONY: clean
clean:
	rm -f *.o *.pyc *.bin $(PROGS)


lab%-handin.tar.gz: clean
	tar cf - `find . -type f | grep -v '^\.*$$' | grep -v '/CVS/' | grep -v '/\.svn/' | grep -v '/\.git/' | grep -v 'lab[0-9].*\.tar\.gz' | grep -v '/submit.token$$' | grep -v libz3str.so` | gzip > $@

.PHONY: prepare-submit
prepare-submit: lab3-handin.tar.gz

.PHONY: prepare-submit-a
prepare-submit-a: lab3a-handin.tar.gz

.PHONY: prepare-submit-b
prepare-submit-b: lab3b-handin.tar.gz

.PHONY: submit-a
submit-a: lab3a-handin.tar.gz
	./submit.py $<

.PHONY: submit-b
submit-b: lab3b-handin.tar.gz
	./submit.py $<

.PHONY: submit
submit: lab3-handin.tar.gz
	./submit.py $<

.PRECIOUS: lab3-handin.tar.gz
