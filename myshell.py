#!/usr/bin/env python3
import os
import sys

buf = ''
_next = 0
limit = 0
max_bytes = 1000
eof = ''

def getchar():
    global eof                                  # Access globals
    global buf
    global _next
    global limit

    if _next == limit:                          # First run, or limit reached
        buf  += os.read(0, max_bytes).decode()  # Fill / add to buffer
        limit = len(buf)                        # Get size of buffer

        if limit == 0:                          # If read no chars
            return eof

    c = buf[_next]                              # Get char
    _next += 1                                  # Setup for next char
    return c                                    # Return the char

def readline():

    global buf                                  # Access globals
    global _next
    global limit
    global eof

    c = getchar()                               # Get first char
    while c != '\n' and c != eof:               # While char is valid
        c = getchar()                           # get next char

    tmp = buf[:_next]                           # get all chars up to newline (including newline)
    buf = buf[_next:]                           # clear buffer upto newline
    limit = len(buf)                            # reset limit
    _next = 0                                   # reset next
    return tmp                                  # return the line


def shell_loop(prompt='$ '.encode()):           # function for shell loop
    global eof                                  # get global eof

    os.write(1, prompt)                         # Prompt
    sys.stdout.flush()                          # flush since no '/n'
    line = readline()                           # Get first line
    while line != eof and line != 'exit\n':     # While line is valid
        if line != '\n':                        # if line is empty
            line = line[:-1]                    # Cut off the newline char
            super_tokens = super_tokenize(line)
            commands = preconfigure(super_tokens)
            run(commands)                 # executes with the list returned from tokenize()
        os.write(1, prompt)                     # Prompt
        sys.stdout.flush()                      # flush to guarantee write
        line = readline()                       # get next line

def tokenize(line):                             # tokenize function
    tokens = line.split(' ')                    # tokenized string
    while '' in tokens:
        tokens.remove('')
    return tokens

def super_tokenize(line, super_tokens=[]):
    special_chars = ['|', '<', '>']
    for char in line:
        if char in special_chars:
            idx = line.index(char)
            before = tokenize(line[:idx])
            after = line[idx+1:]
            super_tokens += [before, char]
            return super_tokenize(after, super_tokens)
    return super_tokens + [tokenize(line)]

def preconfigure(tokens):
    tokens = [[token, []] if not token in ('|', '<', '>') else token for token in tokens]
    for token in tokens:
        if token == '|':
            idx = tokens.index(token)
            r, w = os.pipe()
            os.set_inheritable(r, True)
            os.set_inheritable(w, True)
            before = tokens[idx - 1]
            after = tokens[idx + 1]
            before[1] += [(w,1)]
            after[1] += [(r,0)]
    commands = [token for token in tokens if not token in ('|', '<', '>')]
    return commands

def run(commands):                                # run command
    for command in commands:

        if get_env(command[0]):
            exec(command)
            continue

        if command[0][0] == 'cd':
            if len(command[0]) > 2:
                os.write(1, 'cd: too many arguments\n')
                return
            if len(command[0]) == 1:
                os.chdir(os.environ['HOME'])
                return
            os.chdir(command[0][1])
            continue

        os.write(1, "command not found " + tokens[0] + '\n')     # prints error msg
        return

def exec(command):
    proc_id = os.fork()                         # starts new child shell
    if proc_id < 0:                             # check if valid fork
        os.write(2, "Fork has failed".encode()) # error message to STDERR
        sys.exit(1)
    elif proc_id == 0:
        try:
            path = get_env(command[0])
            for args in command[1]:
                os.dup2(*args)
            os.execve(path, command[0], os.environ) # execute command
        except OSError as error:
            write(2, f'OSError: {error}\n')
        sys.exit(1)

    for config in command[1]:
        os.close(config[0])

    _proc_id, status = os.wait()                               # wait for child to terminate
    if status:
        os.write(1, f'{command[0]} failed with exit status {status}\n')

def get_env(tokens):                            # get envir path
    path_list = os.environ["PATH"].split(":")   # removes returned : to get valid path to return
    for path in path_list:                      # checks for path in the listdir()
        if tokens[0] in os.listdir(path):
            return path + '/' + tokens[0]       # path found, return with valid syntax
    return False
    




if __name__ == '__main__':
    PS1 = '$ '
    if 'PS1' in os.environ:
        PS1 = os.environ['PS1']

    shell_loop(PS1.encode())
