#!/usr/bin/env python3
import os
import sys

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

    if _next == limit:                          # First run, or limit reached
        buf  += os.read(0, max_bytes).decode()  # Fill / add to buffer
        limit = len(buf)                        # Get size of buffer

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

    os.write(1, prompt)       # Prompt
    sys.stdout.flush()
    line = readline()         # Get first line
    while line != eof and line != 'exit\n':        # While line is valid
        if line != '\n':      # if line is empty
            line = line[:-1]   # Cut off the newline char
            run(tokenize(line))    # executes with the list returned from tokenize()
        os.write(1, prompt)   # Prompt
        sys.stdout.flush()
        line = readline()  # get next line

def tokenize(line):
    return line.split(' ')

def run(tokens):
    proc_id = os.fork()
    if proc_id < 0:
        os.write(2, "Fork has failed".encode())
        sys.exit(1)
    elif proc_id == 0:
        path = get_env(tokens)
        if path:
            os.execve(path, tokens, os.environ)
    else:
        os.wait()
        return

def get_env(tokens):
    path_list = os.environ["PATH"].split(":")
    for path in path_list:
        if tokens[0] in os.listdir(path):
            return path + '/' + tokens[0]
    print("command not found " + tokens[0])
    return False
    

if __name__ == '__main__':
    shell_loop()
