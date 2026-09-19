# cxlpath — build + tests.  `make test` uses sparse files in /dev/shm as fake devices;
# `make test-dax` runs the same tests on ranges of /dev/dax0.0 and /dev/dax1.0 that cxlpath OWNS.
CC      = gcc
CFLAGS  = -O2 -g -std=gnu11 -Wall -Wextra -mavx2 -pthread -Iinclude
SRC     = $(wildcard src/*.c)
OBJ     = $(SRC:src/%.c=build/%.o)
TESTS   = $(patsubst tests/%.c,build/%,$(wildcard tests/test_*.c))
FAKE0   = /dev/shm/cxlpath.fakedev0
FAKE1   = /dev/shm/cxlpath.fakedev1

all: build/libcxlpath.a $(TESTS)
build/%.o: src/%.c include/cxlpath.h src/internal.h | build
	$(CC) $(CFLAGS) -c $< -o $@
build/libcxlpath.a: $(OBJ)
	ar rcs $@ $^
build/test_%: tests/test_%.c build/libcxlpath.a
	$(CC) $(CFLAGS) $< build/libcxlpath.a -o $@
build:
	mkdir -p build
test: all
	@truncate -s 2G $(FAKE0) $(FAKE1)
	@for t in $(TESTS); do echo "== $$t (fake devices)"; CXLP_DEV0=$(FAKE0) CXLP_DEV1=$(FAKE1) CXLP_DEV_MIB=2048 $$t || exit 1; done
	@rm -f $(FAKE0) $(FAKE1)
test-dax: all
	@for t in $(TESTS); do echo "== $$t (dax0.0 + dax1.0, first 8 GiB each)"; CXLP_DEV0=/dev/dax0.0 CXLP_DEV1=/dev/dax1.0 CXLP_DEV_MIB=8192 $$t || exit 1; done
clean:
	rm -rf build
.PHONY: all test test-dax clean
