#!/usr/bin/env python2.7

# LZSS Decompression (4096-byte Sliding Window)

import time
import random

ringbuff = [chr(0)] * 4096
buff_read_index = 0
buff_write_index = 0xFEE

bias = 3  # Length is guaranteed to be + bias even though you start from 0.

file_in = open('compressed.bin', 'rb')
file_out = open('decompressed.bin', 'wb')

rbcounter = 0
buffer_primer = open('rb_repeat.bin', 'rb')  # Prime ringbuffer with these bytes.
for n in xrange(4096):
    readbyte = buffer_primer.read(1)
    ringbuff[rbcounter] = readbyte  # chr(0)
    rbcounter += 1
buffer_primer.close()

inputbyte = [None]
inputbyte[0] = file_in.read(1)
while ord(inputbyte[0]) != 255:
    inputbyte[0] = file_in.read(1)

primed = False
# The latest read byte should be an LZSS chunk at this point.
while inputbyte[0]:  # ChunkByte-Byte-Byte-Byte-Byte-Byte-Byte-Byte-Byte: Repeat until empty.

    # Chunk byte is turned into a list of binary. [10101010] Each bit flags one of the following 8 bytes as encoded or not.
    blist = [int(n) for n in list(format(ord(inputbyte[0]), '08b'))]
    blist.reverse()

    # Deal with each bit for each next read byte.
    while len(blist) > 0:
        if buff_write_index == 0:
            primed = True
        if blist[0] == 1:  # No compression. Raw output.
            onebyte = file_in.read(1)  # Read one byte.
            if primed:
                file_out.write(onebyte)  # Write output byte.
            ringbuff[buff_write_index] = onebyte  # Write byte to buffer.
            print 'raw', buff_write_index, hex(ord(ringbuff[buff_write_index]))
            buff_write_index = (buff_write_index + 1) & 0xFFF  # Rolls over 4096

        else:  # Compression.
            firstbyte = file_in.read(1)  # Read one byte.
            secondbyte = file_in.read(1)  # Read one byte.

            # Two bytes are loaded to get distance and length pointers.
            # Bits 0-11 are distance. Fixed index in buffer, not relative
            # Bits 12-15 are length. If -bias- is 3, 0b0000 would be 3 bytes.

            if len(firstbyte) == 0:
                inputbyte[0] = None
            elif len(secondbyte) == 0:
                inputbyte[0] = None
            else:
                # Fancy way of getting the low four bits for length.
                length = (ord(secondbyte) & 0xF) + bias
                # Fancy way of getting the respective high and low bits for distance.
                distance = ord(firstbyte) | ((ord(secondbyte) & 0xF0) << 4)

                # Write all pointed bytes to buffer and output.
                for l in xrange(length):
                    byte = ringbuff[distance & 0xFFF]  # Get byte from buffer.
                    ringbuff[buff_write_index] = byte  # Write byte to buffer.
                    print 'compressed', buff_write_index, hex(ord(ringbuff[buff_write_index]))
                    buff_write_index = (buff_write_index + 1) & 0xFFF  # ++ (Wraps if over length.)
                    if primed:
                        file_out.write(byte)  # Write byte to output.
                    distance += 1  # ++ for next byte.
        blist.pop(0)
    inputbyte[0] = file_in.read(1)  # Get next byte. Should be another at chunk this point.

file_in.close()
file_out.close()
