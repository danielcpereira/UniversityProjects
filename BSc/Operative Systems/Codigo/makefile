CC = gcc

CFLAGS = -Wall -Wextra -pthread

LDFLAGS = -lcrypto

PROGRAM = controller txgen

all: $(PROGRAM)

controller: controller.c pow.c utils.c controller.h pow.h utils.h
	$(CC) $(CFLAGS) -o controller controller.c pow.c utils.c $(LDFLAGS)

txgen: txgen.c utils.c controller.h utils.h
	$(CC) $(CFLAGS) -o txgen txgen.c utils.c

clean:
	rm -f *.o $(PROGRAM)