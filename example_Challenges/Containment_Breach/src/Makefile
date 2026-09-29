CC ?= gcc
CFLAGS ?= -fno-stack-protector -no-pie -z execstack -Wall -O0
TARGET = container-ctl

all: $(TARGET)

$(TARGET): container-ctl.c
	$(CC) $(CFLAGS) -o $(TARGET) container-ctl.c

clean:
	rm -f $(TARGET)
