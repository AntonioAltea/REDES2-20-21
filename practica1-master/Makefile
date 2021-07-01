all: server client concurrent_clients

CC=gcc
CFLAGS=-I/$(IDIR) -g

IDIR=includes/
LSDIR=libsrc/
ODIR=obj/
LDIR=lib/
SDIR=src/

LIBS=-lm -pthread -L. $(LDIR)picohttpparser.a $(LDIR)serverlib.a
DEPS= $(LDIR)picohttpparser.a $(LDIR)serverlib.a

_OBJ = server.o client.o serverlib.o picohttpparser.o concurrent_clients.o
OBJ = $(patsubst %,$(ODIR)%,$(_OBJ))

$(ODIR)%.o: $(SDIR)%.c
	$(CC) -c -o $@ $< $(CFLAGS)

$(ODIR)picohttpparser.o: $(LSDIR)picohttpparser.c
	$(CC) -c -o $@ $< $(CFLAGS)

$(ODIR)serverlib.o: $(LSDIR)serverlib.c $(LDIR)picohttpparser.a
	$(CC) -c -o $@ $< $(CFLAGS)

$(LDIR)picohttpparser.a: $(ODIR)picohttpparser.o
	ar -rv $@ $^

$(LDIR)serverlib.a: $(ODIR)serverlib.o
	ar -rv $@ $^

server: $(ODIR)server.o $(ODIR)serverlib.o $(DEPS)
	$(CC) -o $@ $^ $(CFLAGS) $(LIBS)

client: $(ODIR)client.o $(ODIR)serverlib.o
	$(CC) -o $@ $^ $(CFLAGS) $(LIBS)

concurrent_clients: $(ODIR)concurrent_clients.o $(ODIR)serverlib.o
	$(CC) -o $@ $^ $(CFLAGS) $(LIBS)

.PHONY: clean

clean:
	rm -f $(ODIR)*.o $(LDIR)*.a *~ core $(IDIR)*~ server client concurrent_clients

runs: server
	./server

runc: client
	./client
