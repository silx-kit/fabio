


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


class numbered_file_series(file_series):        
    """
    mydata0001.edf = "mydata" + 0001 + ".edf"
    mydata0002.edf = "mydata" + 0002 + ".edf"
    mydata0003.edf = "mydata" + 0003 + ".edf"
    """
    def __init__(self, stem, first, last, extension, digits=4):
        """
        stem - first part of the name
        
        """
        fmt = "%s%0"+str(digits)+"d%s"
        super(numbered_file_series, self).__init__(
            [ fmt % ( stem, i, extension ) for i in range(first, last + 1) ] )



