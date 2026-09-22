CX = ../../system/cxlpath
CFLAGS = -O2 -g -std=gnu11 -Wall -Wextra -mavx2 -pthread -I$(CX)/include
all: ckpt_producer reader_victim
ckpt_producer: ckpt_producer.c $(CX)/build/libcxlpath.a
	gcc $(CFLAGS) $< $(CX)/build/libcxlpath.a -lm -o $@
reader_victim: reader_victim.c
	gcc $(CFLAGS) $< -o $@
clean:
	rm -f ckpt_producer reader_victim
