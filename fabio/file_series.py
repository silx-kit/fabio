# coding: utf-8
#
#    Project: X-ray image reader
#             https://github.com/silx-kit/fabio
#
#
#    Copyright (C) European Synchrotron Radiation Facility, Grenoble, France
#
#    Principal author:       Jérôme Kieffer (Jerome.Kieffer@ESRF.eu)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

"""

Authors:
........

* Henning O. Sorensen & Erik Knudsen
  Center for Fundamental Research: Metal Structures in Four Dimensions
  Risoe National Laboratory
  Frederiksborgvej 399
  DK-4000 Roskilde
  email:erik.knudsen@risoe.dk
* Jon Wright, ESRF

"""
# Get ready for python3:
from __future__ import absolute_import, print_function, with_statement, division
import logging, sys
logger = logging.getLogger("fileseries")
import traceback as pytraceback

from .fabioutils import FilenameObject, next_filename

from .openimage import openimage


def new_file_series0(first_object, first=None, last=None, step=1):
    """
    Created from a fabio image
    first and last are file numbers

    """
    im = first_object
    nimages = 0
    # for counting images
    if None in (first, last):
        step = 0
        total = 1
    else:
        total = last - first

    yield im
    while nimages < total:
        nimages += step
        try:
            newim = im.next()
            im = newim
        except Exception as error:
            pytraceback.print_exc()

            # Skip bad images
            logger.warning("Got a problem here: %s", error)
            try:
                im.filename = next_filename(im.filename)
            except Exception as error:
                # KE: This will not work and will throw an exception
                # fabio.next_filename doesn't understand %nnnn on the end
                logger.warning("Got another problem here: %s", error)
                im.filename = next_filename(im.sequencefilename)
            yield None
        yield im



def new_file_series(first_object, nimages=0, step=1, traceback=False):
    """
    A generator function that creates a file series starting from a a fabioimage.
    Iterates through all images in a file (if more than 1), then proceeds to
    the next file as determined by fabio.next_filename.

    @param first_object: the starting fabioimage, which will be the first one yielded
        in the sequence
    @param nimages:  the maximum number of images to consider
        step: step size, will yield the first and every step'th image until nimages
        is reached.  (e.g. nimages = 5, step = 2 will yield 3 images (0, 2, 4)
    @param traceback: if True causes it to print a traceback in the event of an
        exception (missing image, etc.).  Otherwise the calling routine can handle
        the exception as it chooses
    @param yields: the next fabioimage in the series.
        In the event there is an exception, it yields the sys.exec_info for the
        exception instead.  sys.exec_info is a tuple:
        ( exceptionType, exceptionValue, exceptionTraceback )
        from which all the exception information can be obtained.

    Suggested usage:

    ::

        for obj in new_file_series( ... ):
          if not isinstance(obj, fabio.fabioimage.fabioimage ):
            # deal with errors like missing images, non readable files, etc
            # e.g.
            traceback.print_exception(obj[0], obj[1], obj[2])

    """
    im = first_object
    nprocessed = 0
    abort = False
    if nimages > 0:
        yield im
        nprocessed += 1
    while nprocessed < nimages:
        try:
            newim = im.next()
            im = newim
            retVal = im
        except Exception as ex:
            retVal = sys.exc_info()
            if(traceback):
                pytraceback.print_exc()
                # Skip bad images
                logger.warning("Got a problem here: next() failed %s", ex)
            # Skip bad images
            try:
                im.filename = next_filename(im.filename)
            except Exception as ex:
                logger.warning("Got another problem here: next_filename(im.filename) %s", ex)
        if nprocessed % step == 0:
            yield retVal
            # Avoid cyclic references with exc_info ?
            retVal = None
            if abort: break
        nprocessed += 1



class file_series(list):
    """
    Represents a series of files to iterate
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
        Constructor:

        @param list_of_strings: arg should be a list of strings which are filenames

        """
        super(file_series, self).__init__(list_of_strings)
        # track current position in list
        self._current = 0


    # methods which return a filename

    def first(self):
        """
        First image in series

        """
        return self[0]

    def last(self):
        """
        Last in series

        """
        return self[-1]

    def previous(self):
        """
        Prev in a sequence

        """
        self._current -= 1
        return self[self._current]

    def current(self):
        """Current position in a sequence

        """
        return self[self._current]

    def next(self):
        """
        Next in a sequence

        """
        self._current += 1
        return self[self._current]

    def jump(self, num):
        """
        Goto a position in sequence

        """
        assert num < len(self) and num > 0, "num out of range"
        self._current = num
        return self[self._current]

    def len(self):
        """
        Number of files

        """
        return len(self)


    # Methods which return a fabioimage

    def first_image(self):
        """
        First image in a sequence

        @return: fabioimage

        """
        return openimage(self.first())

    def last_image(self):
        """
        Last image in a sequence

        @return: fabioimage

        """
        return openimage(self.last())

    def next_image(self):
        """
        Return the next image

        @return: fabioimage

        """
        return openimage(self.next())

    def previous_image(self):
        """
        Return the previous image

        @return: fabioimage

        """
        return openimage(self.previous())

    def jump_image(self, num):
        """
        Jump to and read image

        @return: fabioimage

        """
        return openimage(self.jump(num))

    def current_image(self):
        """
        Current image in sequence

        @return: fabioimage

        """
        return openimage(self.current())

    # methods which return a file_object

    def first_object(self):
        """
        First image in a sequence

        @return: file_object
        """
        return FilenameObject(self.first())

    def last_object(self):
        """
        Last image in a sequence

        @return: file_object

        """
        return FilenameObject(self.last())

    def next_object(self):
        """
        Return the next image

        @return: file_object

        """
        return FilenameObject(self.next())

    def previous_object(self):
        """
        Return the previous image

        @return: file_object

        """
        return FilenameObject(self.previous())

    def jump_object(self, num):
        """
        Jump to and read image

        @return: file_object

        """
        return FilenameObject(self.jump(num))

    def current_object(self):
        """
        Current image in sequence

        @return: file_object

        """
        return FilenameObject(self.current())




class numbered_file_series(file_series):
    """
    mydata0001.edf = "mydata" + 0001 + ".edf"
    mydata0002.edf = "mydata" + 0002 + ".edf"
    mydata0003.edf = "mydata" + 0003 + ".edf"
    """
    def __init__(self, stem, first, last, extension,
                 digits=4, padding='Y', step=1):
        """
        Constructor

        @param stem: first part of the name
        @param step: in case of every nth file
        @param padding: possibility for specifying that numbers are not padded with zeroes up to digits

        """
        if padding == 'Y':
            fmt = "%s%0" + str(digits) + "d%s"
        else:
            fmt = "%s%i%s"

        super(numbered_file_series, self).__init__(
            [ fmt % (stem, i, extension) for i in range(first,
                                                          last + 1,
                                                          step) ])


class filename_series:
    """ Much like the others, but created from a string filename """
    def __init__(self, filename):
        """ create from a filename (String)"""
        self.obj = FilenameObject(filename)

    def next(self):
        """ increment number """
        self.obj.num += 1
        return self.obj.tostring()

    def previous(self):
        """ decrement number """
        self.obj.num -= 1
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
        """ returns the next image as a fabioimage """
        return openimage(self.next())
    def prev_image(self):
        """ returns the previos image as a fabioimage """
        return openimage(self.previous())
    def current_image(self):
        """ returns the current image as a fabioimage"""
        return openimage(self.current())
    def jump_image(self, num):
        """ returns the image number as a fabioimage"""
        return openimage(self.jump(num))
    # object methods
    def next_object(self):
        """ returns the next filename as a fabio.FilenameObject"""
        self.obj.num += 1
        return self.obj
    def previous_object(self):
        """ returns the previous filename as a fabio.FilenameObject"""
        self.obj.num -= 1
        return self.obj
    def current_object(self):
        """ returns the current filename as a fabio.FilenameObject"""
        return self.obj
    def jump_object(self, num):
        """ returns the filename num as a fabio.FilenameObject"""
        self.obj.num = num
        return self.obj




