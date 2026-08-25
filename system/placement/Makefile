# ObjPlace — object-level CXL placement runtime.
CC      ?= gcc
CFLAGS  ?= -O2 -g -Wall -Wextra
LDLIBS  ?= -lnuma -lm

.PHONY: all clean test
all: test_objplace libobjplace.so bwbench gnnbench sensbench mixbench obench

objplace.o: objplace.c objplace.h
	$(CC) $(CFLAGS) -fPIC -c objplace.c -o $@

# Shared library so Python (ctypes) and other tools can call the runtime.
libobjplace.so: objplace.o
	$(CC) -shared -o $@ objplace.o $(LDLIBS)

test_objplace: test_objplace.c objplace.o objplace.h
	$(CC) $(CFLAGS) test_objplace.c objplace.o -o $@ $(LDLIBS)

# Bandwidth-sensitive synthetic benchmark.
bwbench: bwbench.c objplace.o objplace.h
	$(CC) $(CFLAGS) -pthread bwbench.c objplace.o -o $@ $(LDLIBS)

# GNN-style feature-gather benchmark.
gnnbench: gnnbench.c objplace.o objplace.h
	$(CC) $(CFLAGS) -pthread gnnbench.c objplace.o -o $@ $(LDLIBS)

# Sensitivity-vs-hotness demonstration.
sensbench: sensbench.c objplace.o objplace.h
	$(CC) $(CFLAGS) -pthread sensbench.c objplace.o -o $@ $(LDLIBS)

# Multi-object DRAM-budget sweep.
mixbench: mixbench.c objplace.o objplace.h
	$(CC) $(CFLAGS) -pthread mixbench.c objplace.o -o $@ $(LDLIBS)

# Overhead microbenchmark.
obench: obench.c objplace.o objplace.h
	$(CC) $(CFLAGS) obench.c objplace.o -o $@ $(LDLIBS)

test: test_objplace
	./test_objplace

clean:
	rm -f test_objplace bwbench gnnbench sensbench mixbench obench objplace.o libobjplace.so \
	      test_placement obj_placement.o libobj_placement.so
