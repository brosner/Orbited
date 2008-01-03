
# logger = getLogger("HTTPBuffer")

class Buffer(object):
    ''' A Buffer object buffers text, and has two modes, 'index' and 'consume'
        
        In index mode, which is the default initial mode of a Buffer object,
        the buffer object keeps track of a position 'pos', which can be
        altered by calling b.move, or by b.exhaust, which moves 'pos' to the
        end of the file.  ... TODO: finish this
        
        In consume mode, a buffer essentially just a proxy for its contained
        string b.data.
    '''
    def __init__(self, initial_data='', mode='index'):
        self.mode = None
        self.pos = None
        self.data = initial_data        
        self.set_mode(mode)
    
    def set_mode(self, mode):
        # No change
        if self.mode == mode:
            return
        # Switch from consume to index or initial mode is index
        elif mode == 'index':
            self.mode = 'index'
            self.pos = 0
        # Switch from index to consume
        elif mode == 'consume' and self.pos is not None:
            self.data = self.data[self.pos:]
            self.pos = None
            self.mode = 'consume'
        # initial mode is consume
        else: 
            self.mode = 'consume'
            self.pos = None
    
    def find(self, marker, i=0):
        if self.mode == 'consume':
            return self.data.find(marker, i)
        elif self.mode == 'index':
            pos =  self.data.find(marker, i + self.pos)
            if pos == -1:
                return -1
            return pos - self.pos
    
    def __str__(self):
        return self.get_value()
    
    def get_value(self):
        ''' Return the data in consume mode, or the remainder of the data in
            index mode.
        '''
        if self.mode == 'consume':
            return self.data
        elif self.mode == 'index':
            return self.data[self.pos:]
    
    def get_full_value(self):
        ''' Returns the full value of the string, even in index mode. '''
        return self.data
    
    def exhaust(self):
        ''' In index mode, sets position to the end of the buffered data.  In
            consume mode, sets data to empty.
        '''
        if self.mode == 'consume':
            self.data = ''
        elif self.mode == 'index':
            self.pos = len(self.data)
    
    def reset_position(self):
        ''' Resets position to 0. '''
        if self.mode == 'index':
            self.pos = 0
    
    def reset(self, content = ''):
        ''' Resets data to empty, or an opional 'content' string, and position
            to 0.
        '''
        self.data = content
        if self.mode == 'index':
            self.pos = 0
    
    def empty(self):
        ''' Boolean; is true if the the buffer is empty '''
        if self.mode == 'consume':
            return len(self.data) == 0
        elif self.mode == 'index':
            return (len(self.data) - self.pos) == 0
    
    def move(self, i):
        if self.mode == 'consume':
            self.data = self.data[i:]
        elif self.mode == 'index':
            self.pos += i
    
    def part(self, start, end):
        if self.mode == 'consume':
            return self.data[start:end]
        elif self.mode == 'index':
            return self.data[self.pos + start: self.pos + end]
    
    def __contains__(self, data):
        if self.mode == 'consume':
            return data in self.data
        elif self.mode == 'index':
            return self.data.find(data, self.pos) != -1
    
    def __eq__(self, data):
        if self.mode == 'consume':
            return self.data == data
        elif self.mode == 'index':
            return self.data[self.pos:] == data
    
    def __len__(self):
        if self.mode == 'consume':
            return len(self.data)
        elif self.mode == 'index':
            return len(self.data) - self.pos
    
    def __get_slice__(self, start, end):
        return self.part(self, start, end)
    
    def __add__(self, add_data):
        ''' Add the passed-in string to the buffer '''
        if not isinstance(add_data, str):
            raise TypeError
        self.data += add_data
        return self        
    
