# cxlpath — build + tests.  `make test` uses sparse files in /dev/shm as fake devices;
# `make test-dax` runs the same tests on ranges of /dev/dax0.0 and /dev/dax1.0 that cxlpath OWNS.
CC      = gcc
CFLAGS  = -O2 -g -std=gnu11 -Wall -Wextra -mavx2 -pthread -Iinclude
LDLIBS  = -lm
SRC     = $(wildcard src/*.c)
OBJ     = $(SRC:src/%.c=build/%.o)
TESTS   = $(patsubst tests/%.c,build/%,$(wildcard tests/test_*.c))
FAKE0   = /dev/shm/cxlpath.fakedev0
FAKE1   = /dev/shm/cxlpath.fakedev1

CUDA    = /usr/local/cuda
HAVE_CUDA = $(wildcard $(CUDA)/include/cuda_runtime.h)
GPUTOOLS = cxlp_gpu_test
TOOLS   = $(filter-out $(addprefix build/,$(GPUTOOLS)),$(patsubst tests/tools/%.c,build/%,$(wildcard tests/tools/*.c)))
ifneq ($(HAVE_CUDA),)
TOOLS  += build/libcxlpath_gpu.a $(addprefix build/,$(GPUTOOLS))
endif
all: build/libcxlpath.a build/cxlpathd $(TESTS) $(TOOLS)
build/%.o: src/%.c include/cxlpath.h include/cxlpath_daemon.h src/internal.h | build
	$(CC) $(CFLAGS) -c $< -o $@
build/libcxlpath.a: $(OBJ)
	ar rcs $@ $^
build/test_%: tests/test_%.c build/libcxlpath.a
	$(CC) $(CFLAGS) $< build/libcxlpath.a $(LDLIBS) -o $@
build/cxlpathd: daemon/cxlpathd.c build/libcxlpath.a
	$(CC) $(CFLAGS) $< build/libcxlpath.a $(LDLIBS) -o $@
build/%: tests/tools/%.c build/libcxlpath.a
	$(CC) $(CFLAGS) -march=native $< build/libcxlpath.a -o $@
build/gpu.o: src/gpu/gpu.c include/cxlpath_gpu.h src/internal.h | build
	$(CC) $(CFLAGS) -I$(CUDA)/include -c $< -o $@
build/libcxlpath_gpu.a: build/gpu.o
	ar rcs $@ $^
build/cxlp_gpu_test: tests/tools/cxlp_gpu_test.c build/libcxlpath_gpu.a build/libcxlpath.a
	$(CC) $(CFLAGS) -I$(CUDA)/include $< build/libcxlpath_gpu.a build/libcxlpath.a -L$(CUDA)/lib64 -Wl,-rpath,$(CUDA)/lib64 -lcudart $(LDLIBS) -o $@
build:
	mkdir -p build
test: all
	@truncate -s 2G $(FAKE0) $(FAKE1)
	@for t in $(TESTS); do echo "== $$t (fake devices)"; CXLP_DEV0=$(FAKE0) CXLP_DEV1=$(FAKE1) CXLP_DEV_MIB=2048 $$t || exit 1; done
	@echo "== data path syscall check (strace)"; CXLP_DEV0=$(FAKE0) CXLP_DEV1=$(FAKE1) CXLP_DEV_MIB=2048 tests/check_datapath.sh
	@rm -f $(FAKE0) $(FAKE1)
test-dax: all
	@for t in $(TESTS); do echo "== $$t (dax0.0 + dax1.0, first 8 GiB each)"; CXLP_DEV0=/dev/dax0.0 CXLP_DEV1=/dev/dax1.0 CXLP_DEV_MIB=8192 $$t || exit 1; done
clean:
	rm -rf build
.PHONY: all test test-dax clean
