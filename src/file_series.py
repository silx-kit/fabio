


#!/usr/bin/env python
"""

Authors: Henning O. Sorensen & Erik Knudsen
         Center for Fundamental Research: Metal Structures in Four Dimensions
         Risoe National Laboratory
         Frederiksborgvej 399
         DK-4000 Roskilde
         email:erik.knudsen@risoe.dk

        + Jon Wright, ESRF
"""
from fabio import filename_object
from fabio.openimage import openimage
        

        


class file_series(list):
    """
    represents a series of files to iterate
    has an idea of a current position to do next and prev

    You also get from the list python superclass:
       append
       count
       extend
       insert
       pop
       remove
       reverse
       sort
    """
    def __init__(self, list_of_strings):
        """
        arg should be a list of strings which are filenames
        """
        super(file_series, self).__init__( list_of_strings )
        # track current position in list
        self._current = 0
        

    # methods which return a filename
    
    def first(self):
        """ first image in series """
        return self[0]
    
    def last(self):
        """ last in series """
        return self[-1]

    def previous(self):
        """ prev in a sequence"""
        self._current -= 1
        return self[self._current]

    def current(self):
        """ current position in a sequence """
        return self[self._current]

    def next(self):
        """ next in a sequence """
        self._current += 1
        return self[self._current]

    def jump(self, num):
        """ goto a position in sequence """
        assert num < len(self) and num > 0, "num out of range"
        self._current = num
        return self[self._current]

    def len(self):
        """ number of files"""
        return len(self)


    # Methods which return a fabioimage

    def first_image(self):
        """ first image in a sequence """
        return openimage(self.first())

    def last_image(self):
        """ last image in a sequence """
        return openimage(self.last())

    def next_image(self):
        """ Return the next image """        
        return openimage(self.next())

    def previous_image(self):
        """ Return the previous image """        
        return openimage(self.previous())

    def jump_image(self, num):
        """ jump to and read image """
        return openimage(self.jump(num))

    def current_image(self):
        """ current image in sequence """
        return openimage(self.current())

    # methods which return a file_object

    def first_object(self):
        """ first image in a sequence """
        return filename_object(self.first())

    def last_object(self):
        """ last image in a sequence """
        return filename_object(self.last())

    def next_object(self):
        """ Return the next image """        
        return filename_object(self.next())

    def previous_object(self):
        """ Return the previous image """        
        return filename_object(self.previous())

    def jump_object(self, num):
        """ jump to and read image """
        return filename_object(self.jump(num))

    def current_object(self):
        """ current image in sequence """
        return filename_object(self.current())




class numbered_file_series(file_series):        
    """
    mydata0001.edf = "mydata" + 0001 + ".edf"
    mydata0002.edf = "mydata" + 0002 + ".edf"
    mydata0003.edf = "mydata" + 0003 + ".edf"
    """
    def __init__(self, stem, first, last, extension, digits = 4, padding='Y', step = 1):
        """
        stem - first part of the name
        step - in case of every nth file
        padding - possibility for specifying that numbers are not padded
                  with zeroes up to digits
        """
        if padding == 'Y':
            fmt = "%s%0"+str(digits)+"d%s"
        else:
            fmt = "%s%i%s"
            
        super(numbered_file_series, self).__init__(
            [ fmt % ( stem, i, extension ) for i in range(first,
                                                          last + 1,
                                                          step) ] )


class filename_series:
    """ Much like the others, but created from a string filename """
    def __init__(self, filename):
        """ create from a filename (String)"""
        self.obj = filename_object(filename)

    def next(self):
        """ increment number """
        self.obj.num += 1
        return self.obj.tostring()

    def previous(self):
        """ decrement number """
        self.obj.num -=1
        return self.obj.tostring()

    def current(self):
        """ return current filename string"""
        return self.obj.tostring()

    def jump(self, num):
        """ jump to a specific number """
        self.obj.num = num       
        return self.obj.tostring()

    # image methods
    def next_image(self):
        return openimage(self.next())
    def prev_image(self):
        return openimage(self.previous())
    def current_image(self):
        return openimage(self.current())
    def jump_image(self):
        return openimage(self.jump())
    # object methods
    def next_object(self):
        self.obj.num += 1
        return self.obj
    def previous_object(self):
        self.obj.num -= 1
        return self.obj
    def current_object(self):
        return self.obj
    def jump_object(self, num):
        self.obj.num = num
        return self.obj




