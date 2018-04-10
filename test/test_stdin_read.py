#!/bin/env python

import sys

def shell():
    while True:
        cmd = ''
        c = sys.stdin.read(1)
        if c == '\x1b':
            sys.stdout.write(">> hep")
            sys.stdin.write('nidaye')
            sys.stdout.flush()
        else:
            l = sys.stdin.readline()
            print(l)


shell()
