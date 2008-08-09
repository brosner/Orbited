def format_block(s):
    ''' Formatter for block strings to be sent as HTTP.
        (so they can be written cleanly in python classes)
    
        Dedent every line of a string by the indent of the first line,
        replace newlines with '\r\n', and remove any trailing whitespace.
    '''
    s = s.lstrip('\r\n').rstrip() # leading empty lines, trailing whitespace
    lines = s.expandtabs(4).splitlines()
    
    # find w, the smallest indent of a line with content
    w = min([len(line) - len(line.lstrip()) for line in lines])
    
    return '\r\n'.join([line[w:] for line in lines])
