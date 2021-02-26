#!/usr/bin/env python3
import os
import sys

buf = ''
_next = 0
limit = 0
max_bytes = 1000
eof = ''
jobs = []

def getchar():
    global eof                                  # Access globals
    i
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

def job_status():                               # Background Task
    global jobs

    for proc_id in jobs:                        # get proc_id for list of jobs
        try:
            os.waitpid(proc_id, os.WNOHANG)     # reaps zombies/WNOHANG: don't wait
            os.kill(proc_id, 0)                 # chck if process still alive
        except OSError:
            jobs.remove(proc_id)
            os.write(1, f'{proc_id} has terminated\n'.encode())

def shell_loop(prompt='$ '.encode()):               # function for shell loop
    global eof                                      # get global eof

    os.write(1, prompt)                             # Prompt
    sys.stdout.flush()                              # flush since no '/n'
    line = readline()                               # Get first line
    while line != eof and line != 'exit\n':         # While line is valid
        job_status()
        if line != '\n':                            # if line is empty
            line = line[:-1]                        # Cut off the newline char
            super_tokens = super_tokenize(line)
            commands = preconfigure(super_tokens)
            run(commands)                           # executes with the list returned from tokenize()
        os.write(1, prompt)                         # Prompt
        sys.stdout.flush()                          # flush to guarantee write
        line = readline()                           # get next line

def tokenize(line):                                 # tokenize function
    tokens = line.split(' ')                        # tokenized string
    while '' in tokens:
        tokens.remove('')                           # removes empty string
    return tokens


"""
super_tokenize:
Takes whole line if there are multiple commands in one & split them.
"""
def super_tokenize(line, super_tokens=None):
    if not super_tokens:
        super_tokens = []
    special_chars = ['|', '<', '>', '&']
    for char in line:
        if char in special_chars:
            idx = line.index(char)                          # gets index of special char
            before = tokenize(line[:idx])                   # tokenizes command <- special char
            after = line[idx+1:]                            # gets command -> special char
            super_tokens += [before, char]                  # stores b4 command and special char
            return super_tokenize(after, super_tokens)      # ST rest of line, if more than 1 cmds
    super_tokens += [tokenize(line)]
    while [] in super_tokens:                               # removes any empty list
        super_tokens.remove([])
    return super_tokens

"""
preconfigure:
check if there is a special operator, and preconfigure the command for its
intended purpose

"""

def preconfigure(tokens):
    'grep banana < test.txt | sed ///'
    commands = [[token, [], True] if not token in ('|', '<', '>', '&') else token for token in tokens]
    for token in tokens:
        if token == '|':                                                # piping
            idx = commands.index(token)                                 # gets index of |
            before = commands[idx - 1]                                  # gets command <- |
            after = commands[idx + 1]                                   # gets remainder of commands
            r, w = os.pipe()                                            # returns pair of FDs
            os.set_inheritable(r, True)                                 # child proc can inherit descr
            os.set_inheritable(w, True)
            before[1] += [(w,1)]                                        # if b4 = write, preconfig for dup()
            after[1] += [(r,0)]                                         # if after = read, preconfig dup()

        elif token == '>':                                              # redirection
            idx = commands.index(token)                                 # gets index of >
            command = commands[idx - 1]                                 # gets command to the <- of idx
            filename = commands[idx + 1][0][0]                          # [0] pulls [file.txt], [0] pulls file.txt
            fd = os.open(filename, os.O_WRONLY | os.O_CREAT, 0o644)     # open file w/ chmod
            command[1] += [(fd,1)]                                      # 0 - stdout, write to file
            commands.pop(idx)                                           # remove < from copy of supertoken
            commands.pop(idx)                                           # remove file.txt from supertoken

        elif token == '<':                                              # redirection
            idx = commands.index(token)                                 # gets idx of <
            command = commands[idx - 1]                                 # cmd b4 <
            filename = commands[idx + 1][0][0]                          # filename after <
            try:
                fd = os.open(filename, os.O_RDONLY)                     # reads from file
            except FileNotFoundError as error:
                os.write(2, f'File not found error: {error}\n')
            command[1] += [(fd,0)]                                      # 0 - stdin, read from file
            commands.pop(idx)                                           # grep b < file.tx | sed
            commands.pop(idx)                                           # remove < file.txt (for preconfig)

        elif token == '&':                                              # background
            idx = commands.index(token)
            command = commands[idx - 1]
            command[2] = False

    commands = [token for token in commands if not token in ('|', '<', '>', '&')] # sets command
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
    global jobs
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

    if command[2]: # if foreground mode
        _proc_id, status = os.waitpid(proc_id, 0)                               # wait for child to terminate
        if status:
            os.write(1, f'{command[0]} failed with exit status {status}\n'.encode())
        return

    os.waitpid(proc_id, os.WNOHANG)
    jobs += [proc_id]

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
