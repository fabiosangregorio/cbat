def findall(p, s):
    '''Yields all the positions of the pattern p in the string s.'''
    i = s.find(p)
    while i != -1:
        yield i
        i = s.find(p, i+1)


def printl(msg):
    '''Prints msg on the same line as previous printl messages.'''
    print(msg, end="", flush=True)
