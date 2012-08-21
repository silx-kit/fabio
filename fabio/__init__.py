version = "0.1.1"
import logging
logging.basicConfig()
import fabioimage
import openimage
from fabioutils import filename_object, COMPRESSORS, jump_filename, \
        previous_filename, next_filename, deconstruct_filename, \
        extract_filenumber, getnum, construct_filename
from openimage import openimage as open
from openimage import openheader as openheader
