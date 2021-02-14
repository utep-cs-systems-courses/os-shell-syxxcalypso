#!/usr/bin/env python3

from os import read, write, execvpe, execve
from sys import stdin, stdout

buf = ''
_next = 0
limit = 0
max_bytes = 4
eof = ''

def getchar():
    global eof
    global buf
    global _next
    global limit

    if _next == limit:                       # First run, or limit reached
        buf  += read(0, max_bytes).decode()  # Fill / add to buffer
        limit = len(buf)                     # Get size of buffer

        if limit == 0: # If read no chars
            return eof

    c = buf[_next] # Get char
    _next += 1     # Setup for next char
    return c       # Return the char

def readline():

    # Access globals
    global buf
    global _next
    global limit
    global eof

    c = getchar()                   # Get first char
    while c != '\n' and c != eof:   # While char is valid
        c = getchar()               # get next char

    tmp = buf[:_next] # get all chars up to newline (including newline)
    buf = buf[_next:] # clear buffer upto newline
    limit = len(buf)  # reset limit
    _next = 0         # reset next
    return tmp        # return the line



def shell_loop(prompt='$ '.encode()):
    global eof # get global eof

    write(1, prompt)          # Prompt
    stdout.flush()
    line = readline()         # Get first line
    while line != eof:        # While line is valid
        if line == '\n':      # if line is empty
            line = readline() # then get another line (reset the prompt)
            continue          # reset the while loop

        line = line[:-1]   # Cut off the newline char
        print(':',line)    # echo
        write(1, prompt)   # Prompt
        stdout.flush()
        line = readline()  # get next line

if __name__ == '__main__':
    shell_loop()
