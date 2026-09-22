CX = ../../system/cxlpath
CFLAGS = -O2 -g -std=gnu11 -Wall -Wextra -mavx2 -pthread -I$(CX)/include
all: budget_synth dram_writer probe_log
%: %.c writer.h $(CX)/build/libcxlpath.a
	gcc $(CFLAGS) $< $(CX)/build/libcxlpath.a -lm -o $@
clean:
	rm -f budget_synth dram_writer probe_log
