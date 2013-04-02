version = "0.1.2"
import logging
logging.basicConfig()
import fabioimage
import openimage
from fabioutils import COMPRESSORS, jump_filename, FilenameObject, \
        previous_filename, next_filename, deconstruct_filename, \
        extract_filenumber, getnum, construct_filename
from openimage import openimage as open
from openimage import openheader as openheader
