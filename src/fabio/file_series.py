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
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
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

import logging
import sys
import os.path
import collections

logger = logging.getLogger(__name__)

import fabio
from .fabioutils import FilenameObject, next_filename
from .openimage import openimage
from .fabioimage import FabioImage
from .utils import deprecation


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
            # Skip bad images
            logger.warning("Got a problem here: %s", error)
            logger.debug("Backtrace", exc_info=True)
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
    A generator function that creates a file series starting from a fabioimage.
    Iterates through all images in a file (if more than 1), then proceeds to
    the next file as determined by fabio.next_filename.

    :param first_object: the starting fabioimage, which will be the first one yielded
        in the sequence
    :param nimages:  the maximum number of images to consider
        step: step size, will yield the first and every step'th image until nimages
        is reached.  (e.g. nimages = 5, step = 2 will yield 3 images (0, 2, 4)
    :param traceback: if True causes it to print a traceback in the event as a
        logging error. Otherwise the exception is logged as a debug message.
        the exception as it chooses
    :param yields: the next fabioimage in the series.
        In the event there is an exception, it yields the sys.exec_info for the
        exception instead.  sys.exec_info is a tuple:
        ( exceptionType, exceptionValue, exceptionTraceback )
        from which all the exception information can be obtained.

    Suggested usage:

    .. code-block:: python

        for obj in new_file_series( ... ):
            if not isinstance(obj, fabio.fabioimage.FabioImage):
                # In case of problem (missing images, non readable files, etc)
                # obj contains the result of exc_info
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
            # Skip bad images
            logger.warning("Got a problem here: next() failed %s", ex)
            if(traceback):
                logger.error("Backtrace", exc_info=True)
            else:
                logger.debug("Backtrace", exc_info=True)
            # Skip bad images
            try:
                im.filename = next_filename(im.filename)
            except Exception as ex:
                logger.warning("Got another problem here: next_filename(im.filename) %s", ex)
        if nprocessed % step == 0:
            yield retVal
            # Avoid cyclic references with exc_info ?
            retVal = None
            if abort:
                break
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

        :param list_of_strings: arg should be a list of strings which are filenames

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
        assert num < len(self) and num >= 0, "num out of range"
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

        :return: fabioimage

        """
        return openimage(self.first())

    def last_image(self):
        """
        Last image in a sequence

        :return: fabioimage

        """
        return openimage(self.last())

    def next_image(self):
        """
        Return the next image

        :return: fabioimage

        """
        return openimage(self.next())

    def previous_image(self):
        """
        Return the previous image

        :return: fabioimage

        """
        return openimage(self.previous())

    def jump_image(self, num):
        """
        Jump to and read image

        :return: fabioimage

        """
        return openimage(self.jump(num))

    def current_image(self):
        """
        Current image in sequence

        :return: fabioimage

        """
        return openimage(self.current())

    # methods which return a file_object

    def first_object(self):
        """
        First image in a sequence

        :return: file_object
        """
        return FilenameObject(self.first())

    def last_object(self):
        """
        Last image in a sequence

        :return: file_object

        """
        return FilenameObject(self.last())

    def next_object(self):
        """
        Return the next image

        :return: file_object

        """
        return FilenameObject(self.next())

    def previous_object(self):
        """
        Return the previous image

        :return: file_object

        """
        return FilenameObject(self.previous())

    def jump_object(self, num):
        """
        Jump to and read image

        :return: file_object

        """
        return FilenameObject(self.jump(num))

    def current_object(self):
        """
        Current image in sequence

        :return: file_object

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

        :param stem: first part of the name
        :param step: in case of every nth file
        :param padding: possibility for specifying that numbers are not padded with zeroes up to digits

        """
        if padding == 'Y':
            fmt = "%s%0" + str(digits) + "d%s"
        else:
            fmt = "%s%i%s"

        strings = [fmt % (stem, i, extension) for i in range(first, last + 1, step)]
        super(numbered_file_series, self).__init__(strings)


class filename_series(object):
    """Iterator through a list of files indexed by a number.

    Supports `next`, `prevous` and jump accessors.

    :param Union[str,FilenameObject] filename: The first filename of the
        iteration.
    """
    """ Much like the others, but created from a string filename """

    def __init__(self, filename):
        """ create from a filename (String)"""
        if isinstance(filename, FilenameObject):
            self.obj = filename
        else:
            self.obj = FilenameObject(filename=filename)

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


_FileDescription = collections.namedtuple('_FileDescription',
                                          ['filename', 'file_number', 'first_frame_number', 'nframes'])
"""Object storing description of a file from a file serie"""


def _filename_series_adapter(series):
    """Adapter to list all available files from a `filename_series` class.

    Without the adaptater `filename_series` will not list the first element,
    and will loop to the infinite.
    """
    assert(isinstance(series, filename_series))
    filename = series.current()
    if not os.path.exists(filename):
        return
    yield filename

    if series.obj.num is None:
        # It's a single filename
        return

    while True:
        filename = series.next()
        if not os.path.exists(filename):
            return
        yield filename


class FileSeries(FabioImage):
    """Provide a `FabioImage` abstracting a file series.

    This abstraction provide the set of the filenames as the container of
    frames.

    .. code-block:: python

        # Sequencial access through all the frames
        with FileSeries(filenames) as serie:
            for frame in serie.frames():
                frame.data
                frame.header
                frame.index                    # index inside the file series
                frame.file_index               # index inside the file (edf, tif)
                frame.file_container.filename  # name of the source file

        # Random access to frames
        with FileSeries(filenames) as serie:
            frame = serie.get_frame(200)
            frame = serie.get_frame(201)
            frame = serie.get_frame(10)
            frame = serie.get_frame(2)

    Files of the series can be set using a list of filenames, an iterator or a
    generator. It also supports a file series described using
    :class:`filename_series` or :class:`file_series` objects.

    .. code-block:: python

        # Iterate known files
        filenames = ["foo.edf", "bar.tif"]
        serie = FileSeries(filenames=filenames)

        # Iterate all images from foobar_0001.edf to 0003
        filenames = numbered_file_series("foobar_", 1, 3, ".edf", digits=4)
        serie = FileSeries(filenames=filenames)

        # Iterate all images from foobar_0000.edf to the last consecutive number found
        filenames = filename_series("foobar_0000.edf")
        serie = FileSeries(filenames=filenames)

    Options are provided to optimize a non-sequencial access by providing the
    amount of frames stored per files. This options (`single_frame`, `fixed_frames` and
    `fixed_frame_number`) can be used if we know an a priori on the way frames
    are stored in the files (the exact same amount of frames par file).

    .. code-block:: python

        # Each files contains a single frame
        serie = FileSeries(filenames=filenames, single_frame=True)

        # Each files contains a fixed amout of frames.  This value is
        # automatically found
        serie = FileSeries(filenames=filenames, fixed_frames=True)

        # Each files contains 100 frames (the last one could contain less)
        serie = FileSeries(filenames=filenames, fixed_frame_number=100)
    """
    DEFAULT_EXTENSIONS = []

    def __init__(self, filenames, single_frame=None, fixed_frames=None, fixed_frame_number=None):
        """
        Constructor

        :param Union[Generator,Iterator,List] filenames: Ordered list of filenames
            to process as a file series. It also can be a generator, and
            iterator, or `filename_series` or `file_series` objects.
        :param Union[Bool,None] single_frame: If True, all files are supposed to
            contain only one frame.
        :param Union[Bool,None] fixed_frames: If True, all files are supposed to
            contain the same amount of frames (this fixed amount will be reached
            from the first file of the serie).
        :param Union[Integer,None] fixed_frame_number: If set, all files are
            supposed to contain the same amount of frames (sepecified by this
            argument)
        """
        if isinstance(filenames, filename_series):
            filenames = _filename_series_adapter(filenames)

        if isinstance(filenames, list):
            self.__filenames = filenames
            self.__filename_generator = None
        else:
            self.__filenames = []
            self.__filename_generator = filenames

        self.__current_fabio_file_index = -1
        self.__current_fabio_file = None
        self.__file_descriptions = None
        self.__current_file_description = None

        if single_frame is not None:
            self.__fixed_frames = True
            self.__fixed_frame_number = 1
        elif fixed_frame_number is not None:
            self.__fixed_frames = True
            self.__fixed_frame_number = int(fixed_frame_number)
        elif fixed_frames is not None and fixed_frames:
            self.__fixed_frames = bool(fixed_frames)
            # We do not yet know the amount of frames per files
            self.__fixed_frame_number = None
        else:
            self.__fixed_frames = False
            self.__fixed_frame_number = None
            self.__file_descriptions = []

        self.__nframes = None
        self.use_edf_shortcut = True
        """If true a custom file sequencial file reader is used for EDF formats"""

    def close(self):
        """Close any IO handler openned."""
        if self.__current_fabio_file is not None:
            self.__current_fabio_file.close()
        self.__current_fabio_file_index = -1
        self.__current_fabio_file = None

    def __iter_filenames(self):
        """Returns an iterator throug all filenames of the file series."""
        for filename in self.__filenames:
            yield filename
        if self.__filename_generator is not None:
            for filename in self.__filename_generator:
                # Store it in case there is backward requests
                self.__filenames.append(filename)
                yield filename
            self.__filename_generator = None

    def frames(self):
        """Returns an iterator throug all frames of all filenames of this
        file series."""
        import fabio.edfimage
        nframe = 0
        for filename in self.__iter_filenames():

            if self.use_edf_shortcut:
                info = FilenameObject(filename=filename)
                # It is the supported formats
                if fabio.edfimage.EdfImage in info.codec_classes:
                    # Custom iterator implementation
                    frames = fabio.edfimage.EdfImage.lazy_iterator(filename)
                    for frame in frames:
                        frame._set_container(self, nframe)
                        yield frame
                        nframe += 1
                    continue

            # Default implementation
            with fabio.open(filename) as image:
                if image.nframes == 0:
                    # The container is empty
                    pass
                else:
                    for frame_num in range(image.nframes):
                        frame = image.get_frame(frame_num)
                        frame._set_container(self, nframe)
                        yield frame
                        nframe += 1
        self.__nframes = nframe

    def __load_all_filenames(self):
        """Load all filenames using the generator.

        It is needed to know the number of frames.

        .. note:: If the generator do not have endding, it will result an
            infinite loop.
        """
        if self.__filename_generator is not None:
            for next_filename in self.__filename_generator:
                self.__filenames.append(next_filename)
            self.__filename_generator = None

    def __get_filename(self, file_number):
        """Returns the filename from it's file position.

        :param int file_number: Position of the file in the file series
        :rtype: str
        :raise IndexError: It the requested position is out of the available
            number of files
        """
        if file_number < len(self.__filenames):
            filename = self.__filenames[file_number]
        elif self.__filename_generator is not None:
            # feed the filenames using the generator
            amount = file_number - len(self.__filenames) + 1
            try:
                for _ in range(amount):
                    next_filename = next(self.__filename_generator)
                    self.__filenames.append(next_filename)
            except StopIteration:
                # No more filenames
                self.__filename_generator = None
            if file_number < len(self.__filenames):
                filename = self.__filenames[file_number]
            else:
                raise IndexError("File number '%s' is not reachable" % file_number)
        else:
            raise IndexError("File number %s is not reachable" % file_number)
        return filename

    def __get_file(self, file_number):
        """Returns the opennned FabioImage from it's file position.

        :param int file_number: Position of the file in the file series
        :rtype: FabioImage
        :raise IndexError: It the requested position is out of the available
            number of files
        """
        if self.__current_fabio_file_index == file_number:
            return self.__current_fabio_file
        filename = self.__get_filename(file_number)
        if self.__current_fabio_file is not None:
            self.__current_fabio_file.close()
        self.__current_fabio_file_index = file_number
        self.__current_fabio_file = fabio.open(filename)
        return self.__current_fabio_file

    def __iter_file_descriptions(self):
        """Iter all file descriptions.

        Use a cached structure which grows according to the requestes.
        """
        assert(self.__file_descriptions is not None)
        for description in self.__file_descriptions:
            yield description

        # Construct the following descriptions
        if len(self.__file_descriptions) > 0:
            description = self.__file_descriptions[-1]
            last_frame_number = description.first_frame_number + description.nframes
        else:
            last_frame_number = 0

        while True:
            # Get the next file
            file_number = len(self.__file_descriptions)
            try:
                filename = self.__get_filename(file_number)
            except IndexError:
                # No more filenames
                break
            fabiofile = self.__get_file(file_number)
            first_frame = last_frame_number
            nframes = fabiofile.nframes
            description = _FileDescription(filename, file_number, first_frame, nframes)
            self.__file_descriptions.append(description)
            yield description
            last_frame_number = first_frame + nframes

    def __find_file_description(self, frame_number):
        """Returns a file description from a cached list of stored descriptions.

        :param int frame_number: A frame number
        :rtype: _FileDescription
        """
        assert(self.__file_descriptions is not None)

        # Check it on the last cached description
        if self.__current_file_description is not None:
            description = self.__current_file_description
            last_frame_number = description.first_frame_number + description.nframes
            if description.first_frame_number <= frame_number < last_frame_number:
                return description

        # Check it on the cached list
        for description in self.__iter_file_descriptions():
            last_frame_number = description.first_frame_number + description.nframes
            if description.first_frame_number <= frame_number < last_frame_number:
                self.__current_file_description = description
                return description

        raise IndexError("Frame %s is out of range" % frame_number)

    def __get_file_description(self, frame_number):
        """Returns file description at the frame number.

        :rtype: _FileDescription
        """
        if not self.__fixed_frames:
            description = self.__find_file_description(frame_number)
            return description

        if self.__fixed_frame_number is None:
            # The number of frames per files have to be reached
            fabiofile = self.__get_file(0)
            self.__fixed_frame_number = fabiofile.nframes

        file_number = frame_number // self.__fixed_frame_number
        try:
            filename = self.__get_filename(file_number)
        except IndexError:
            raise IndexError("Frame %s is out of range" % frame_number)
        first_frame = frame_number - (frame_number % self.__fixed_frame_number)
        nframes = self.__fixed_frame_number
        return _FileDescription(filename, file_number, first_frame, nframes)

    def _get_frame(self, num):
        """Returns the frame numbered `num` in the series as a fabioimage.

        :param int num: The number of the requested frame
        :rtype: FabioFrame
        """
        if num < 0:
            raise IndexError("Frame %s is out of range" % num)
        description = self.__get_file_description(num)
        fileimage = self.__get_file(description.file_number)
        local_frame = num - description.first_frame_number
        if not (0 <= local_frame < description.nframes):
            msg = "Index '%d' (local index '%d' from '%s') is out of range"
            raise IndexError(msg % (num, local_frame, description.filename))
        try:
            frame = fileimage._get_frame(local_frame)
        except IndexError:
            logger.debug("Backtrace", exc_info=True)
            msg = "Index '%d' (local index '%d' from '%s') is out of range"
            raise IndexError(msg % (num, local_frame, description.filename))
        frame._set_container(self, num)
        return frame

    @deprecation.deprecated(reason="Replaced by get_frame.", deprecated_since="0.10.0beta")
    def getframe(self, num):
        return self.get_frame(num)

    @property
    def nframes(self):
        """Returns the number of available frames in the full file series.

        :rtype: int
        """
        if self.__nframes is not None:
            return self.__nframes

        if not self.__fixed_frames:
            # General case. All the information is needed
            # Load all available descriptions
            for _ in self.__iter_file_descriptions():
                pass
            if len(self.__file_descriptions) == 0:
                self.__nframes = 0
                return self.__nframes
            description = self.__file_descriptions[-1]
            self.__nframes = description.first_frame_number + description.nframes
            return self.__nframes

        if self.__fixed_frame_number is None:
            # The number of frames per files have to be reached
            try:
                fabiofile = self.__get_file(0)
            except IndexError:
                self.__nframes = 0
                return self.__nframes
            self.__fixed_frame_number = fabiofile.nframes

        # The last file can contains less frames
        self.__load_all_filenames()
        if len(self.__filenames) == 0:
            self.__nframes = 0
            return self.__nframes
        file_number = len(self.__filenames) - 1
        fabiofile = self.__get_file(file_number)
        nframes = self.__fixed_frame_number * (len(self.__filenames) - 1) + fabiofile.nframes
        self.__nframes = nframes
        return nframes

    @property
    def data(self):
        # This could provide access to the first or the current frame
        raise NotImplementedError("Not implemented. Use serie.frames() or serie.get_frame(int)")

    @property
    def header(self):
        # This could provide access to the first or the current frame
        raise NotImplementedError("Not implemented. Use serie.frames() or serie.get_frame(int)")

    @property
    def shape(self):
        # This could provide access to the first or the current frame
        raise NotImplementedError("Not implemented. Use serie.frames() or serie.get_frame(int)")

    @property
    def dtype(self):
        # This could provide access to the first or the current frame
        raise NotImplementedError("Not implemented. Use serie.frames() or serie.get_frame(int)")
