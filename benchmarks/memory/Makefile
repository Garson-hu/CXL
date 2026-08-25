# membench — DRAM vs CXL memory benchmark
# Requires libnuma-dev (provides numa.h).

CC      ?= gcc
CFLAGS  ?= -O3 -g -Wall -Wextra -march=native -pthread
LDFLAGS ?=
LDLIBS  ?= -lnuma -lpthread

TARGET  := membench
SRCS    := membench.c

.PHONY: all clean check-libnuma
all: $(TARGET)

$(TARGET): $(SRCS)
	$(CC) $(CFLAGS) $(SRCS) -o $@ $(LDFLAGS) $(LDLIBS)

check-libnuma:
	@echo '#include <numa.h>' | $(CC) -E -x c - >/dev/null 2>&1 \
	  && echo "libnuma headers OK" \
	  || (echo "libnuma headers missing — install libnuma-dev"; exit 1)

clean:
	rm -f $(TARGET)
