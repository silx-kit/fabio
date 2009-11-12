
"""
This is the mar header interpreter from Fabian by HOS and EK. 
JPW replaced it with a parser based approach because:
   this might be hard to maintain, in the even of a single incorrect number somewhere
   theoretically all header items are picked up by the parser, automatically
   the pylint score for this was rather low
"""


class obselete:
    def _readheader_fabian(self, infile):
        """
        Read in the header from an already opened file
        """
        self.header = {}
        clip = '\x00'
        l = infile.seek(1024)
        l = infile.read(3072)
        # Header information in MarCCD and MarMosaic images are obtained 
        # from http://www.mar-usa.com/support/data.htm
        #/* File/header format parameters (256 bytes) */
        self.header['header_type'] = \
            N.fromstring(l[0:4], N.uint32)[0]  
        # UINT32 ; /* flag for header type (can be used as magic number) */
        self.header['header_name'] = l[4:4+l[4:20].find(clip)] # char[16] ; /* header name (MMX) */
        self.header['header_major_version'] = N.fromstring(l[20:24],N.uint32)[0]  # UINT32 ; /* header_major_version (n.) */
        self.header['header_minor_version'] = N.fromstring(l[24:28],N.uint32)[0]  # UINT32 ; /* header_minor_version (.n) */
        self.header['header_byte_orde'] = N.fromstring(l[28:32],N.uint32)[0]  # UINT32 r;/* BIG_ENDIAN (Motorola,MIPS); LITTLE_ENDIAN (DEC, Intel) */
        self.header['data_byte_order'] = N.fromstring(l[32:36],N.uint32)[0]  # UINT32 ; /* BIG_ENDIAN (Motorola,MIPS); LITTLE_ENDIAN (DEC, Intel) */
        self.header['header_size'] = N.fromstring(l[36:40],N.uint32)[0]  # UINT32 ; /* in bytes */
        self.header['frame_type'] = N.fromstring(l[40:44],N.uint32)[0]  # UINT32 ; /* flag for frame type */
        #self.header['magic_number'] = N.fromstring(l[44:48],N.uint32)[0]  # UINT32 ; /* to be used as a flag - usually to indicate new file */
        #self.header['compression_type'] = N.fromstring(l[48:52],N.uint32)[0]  # UINT32 ; /* type of image compression */
        #self.header['compression1'] = N.fromstring(l[52:56],N.uint32)[0]  # UINT32 ; /* compression parameter 1 */
        #self.header['compression2'] = N.fromstring(l[56:60],N.uint32)[0]  # UINT32 ; /* compression parameter 2 */
        #self.header['compression3'] = N.fromstring(l[60:64],N.uint32)[0]  # UINT32 ; /* compression parameter 3 */
        #self.header['compression4'] = N.fromstring(l[64:68],N.uint32)[0]  # UINT32 ; /* compression parameter 4 */
        #self.header['compression5'] = N.fromstring(l[68:72],N.uint32)[0]  # UINT32 ; /* compression parameter 4 */
        #self.header['compression6'] = N.fromstring(l[72:76],N.uint32)[0]  # UINT32 ; /* compression parameter 4 */
        #self.header['nheaders'] = N.fromstring(l[76:80],N.uint32)[0]  # UINT32 ; /* total number of headers */
        self.header['nfast'] = N.fromstring(l[80:84],N.uint32)[0]  # UINT32 ; /* number of pixels in one line */
        self.header['nslow'] = N.fromstring(l[84:88],N.uint32)[0]  # UINT32 ; /* number of lines in image */
        self.header['depth'] = N.fromstring(l[88:92],N.uint32)[0]  # UINT32 ; /* number of bytes per pixel */
        #self.header['record_length'] = N.fromstring(l[92:96],N.uint32)[0]  # UINT32 ; /* number of pixels between succesive rows */
        self.header['signif_bits'] = N.fromstring(l[96:100],N.uint32)[0]  # UINT32 ; /* true depth of data, in bits */
        #self.header['data_type'] = N.fromstring(l[100:104],N.uint32)[0]  # UINT32 ; /* (signed,unsigned,float...) */
        #self.header['saturated_value'] = N.fromstring(l[104:108],N.uint32)[0]  # UINT32 ; /* value marks pixel as saturated */
        self.header['sequence'] = N.fromstring(l[108:112],N.uint32)[0]  # UINT32 ; /* TRUE or FALSE */
        self.header['nimages'] = N.fromstring(l[112:116],N.uint32)[0]  # UINT32 ; /* total number of images - size of each is nfast*(nslow/nimages) */
        self.header['origin'] = N.fromstring(l[116:120],N.uint32)[0]  # UINT32 ; /* corner of origin */
        self.header['orientation'] = N.fromstring(l[120:124],N.uint32)[0]  # UINT32 ; /* direction of fast axis */
        self.header['view_direction'] = N.fromstring(l[124:128],N.uint32)[0]  # UINT32 ; /* direction to view frame */
        self.header['overflow_locatio'] = N.fromstring(l[128:132],N.uint32)[0]  # UINT32 n;/* FOLLOWING_HEADER, FOLLOWING_DATA */
        self.header['over_8_bits'] = N.fromstring(l[132:136],N.uint32)[0]  # UINT32 ; /* # of pixels with counts > 255 */
        self.header['over_16_bits'] = N.fromstring(l[136:140],N.uint32)[0]  # UINT32 ; /* # of pixels with count > 65535 */
        self.header['multiplexed'] = N.fromstring(l[140:144],N.uint32)[0]  # UINT32 ; /* multiplex flag */
        self.header['nfastimages'] = N.fromstring(l[144:148],N.uint32)[0]  # UINT32 ; /* # of images in fast direction */
        self.header['nslowimages'] = N.fromstring(l[148:152],N.uint32)[0]  # UINT32 ; /* # of images in slow direction */
        self.header['background_applied'] = N.fromstring(l[152:156],N.uint32)[0]  # UINT32 ; /* flags correction has been applied hold magic number ? */
        self.header['bias_applied'] = N.fromstring(l[156:160],N.uint32)[0]  # UINT32 ; /* flags correction has been applied - hold magic number ? */
        self.header['flatfield_applied'] = N.fromstring(l[160:164],N.uint32)[0]  # UINT32 ; /* flags correction has been applied hold magic number ? */
        self.header['distortion_applied'] = N.fromstring(l[164:168],N.uint32)[0]  # UINT32 ; /* flags correction has been applied hold magic number ? */
        #self.header['original_header_type'] = N.fromstring(l[168:172],N.uint32)[0]  # UINT32 ; /* Header/frame type from file that frame is read from */
        #self.header['file_saved'] = N.fromstring(l[172:176],N.uint32)[0]  # UINT32 ; /* Flag that file has been saved, should be zeroed if modified */
        #/* Goniostat parameters (128 bytes) */
        self.header['xtal_to_detector'] = N.fromstring(l[640:644],N.int32)[0]*1000  #INT32 ; /* 1000*distance in millimeters */
        self.header['beam_x'] = N.fromstring(l[644:648],N.int32)[0]*1000  #INT32 ; /* 1000*x beam position (pixels) */
        self.header['beam_y'] = N.fromstring(l[648:652],N.int32)[0]*1000  #INT32 ; /* 1000*y beam position (pixels) */
        self.header['integration_time'] = N.fromstring(l[652:656],N.int32)[0]  #INT32 ; /* integration time in milliseconds */
        self.header['exposure_time'] = N.fromstring(l[656:660],N.int32)[0]  #INT32 ; /* exposure time in milliseconds */
        self.header['readout_time'] = N.fromstring(l[660:664],N.int32)[0]  #INT32 ; /* readout time in milliseconds */
        self.header['nreads'] = N.fromstring(l[664:668],N.int32)[0]  #INT32 ; /* number of readouts to get this image */
        self.header['start_twotheta'] = N.fromstring(l[668:672],N.int32)[0]*1000  #INT32 ; /* 1000*two_theta angle */
        self.header['start_omega'] = N.fromstring(l[676:680],N.int32)[0]*1000  #INT32 ; /* 1000*omega angle */
        self.header['start_chi'] = N.fromstring(l[680:684],N.int32)[0]*1000  #INT32 ; /* 1000*chi angle */
        self.header['start_kappa'] = N.fromstring(l[684:688],N.int32)[0]*1000  #INT32 ; /* 1000*kappa angle */
        self.header['start_phi'] = N.fromstring(l[688:692],N.int32)[0]*1000  #INT32 ; /* 1000*phi angle */
        self.header['start_delta'] = N.fromstring(l[692:696],N.int32)[0]*1000  #INT32 ; /* 1000*delta angle */
        self.header['start_gamma'] = N.fromstring(l[696:700],N.int32)[0]*1000  #INT32 ; /* 1000*gamma angle */
        self.header['start_xtal_to_detector'] = N.fromstring(l[700:704],N.int32)[0]*1000  #INT32 ; /* 1000*distance in mm (dist in um)*/
        self.header['end_twotheta'] = N.fromstring(l[704:708],N.int32)[0]*1000  #INT32 ; /* 1000*two_theta angle */
        self.header['end_omega'] = N.fromstring(l[708:712],N.int32)[0]*1000  #INT32 ; /* 1000*omega angle */
        self.header['end_chi'] = N.fromstring(l[712:716],N.int32)[0]*1000  #INT32 ; /* 1000*chi angle */
        self.header['end_kappa'] = N.fromstring(l[716:720],N.int32)[0]*1000  #INT32 ; /* 1000*kappa angle */
        self.header['end_phi'] = N.fromstring(l[720:724],N.int32)[0]*1000  #INT32 ; /* 1000*phi angle */
        self.header['end_delta'] = N.fromstring(l[724:728],N.int32)[0]*1000  #INT32 ; /* 1000*delta angle */
        self.header['end_gamma'] = N.fromstring(l[728:732],N.int32)[0]*1000  #INT32 ; /* 1000*gamma angle */
        self.header['end_xtal_to_detector'] = N.fromstring(l[732:736],N.int32)[0]*1000  #INT32 ; /* 1000*distance in mm (dist in um)*/
        self.header['rotation_axis'] = N.fromstring(l[736:740],N.int32)[0]  #INT32 ; /* active rotation axis */
        self.header['rotation_range'] = N.fromstring(l[740:744],N.int32)[0]*1000  #INT32 ; /* 1000*rotation angle */
        self.header['detector_rotx'] = N.fromstring(l[744:748],N.int32)[0]*1000  #INT32 ; /* 1000*rotation of detector around X */
        self.header['detector_roty'] = N.fromstring(l[748:752],N.int32)[0]*1000  #INT32 ; /* 1000*rotation of detector around Y */
        self.header['detector_rotz'] = N.fromstring(l[752:756],N.int32)[0]*1000  #INT32 ; /* 1000*rotation of detector around Z */
        #/* Detector parameters (128 bytes) */
        self.header['detector_type'] = N.fromstring(l[768:772],N.int32)[0]  #INT32 ; /* detector type */
        self.header['pixelsize_x'] = N.fromstring(l[772:776],N.int32)[0]  #INT32 ; /* pixel size (nanometers) */
        self.header['pixelsize_y'] = N.fromstring(l[776:780],N.int32)[0]  #INT32 ; /* pixel size (nanometers) */
        self.header['mean_bias'] = N.fromstring(l[780:784],N.int32)[0]*1000  #INT32 ; /* 1000*mean bias value */
        self.header['photons_per_100adu'] = N.fromstring(l[784:788],N.int32)[0]  #INT32 ; /* photons / 100 ADUs */
        self.header['measured_bias'] = N.fromstring(l[788:792],N.int32)[0]*1000  #INT32 [MAXIMAGES]; /* 1000*mean bias value for each image*/
        self.header['measured_temperature'] = N.fromstring(l[792:796],N.int32)[0] #INT32  [MAXIMAGES]; /* Temperature of each detector in milliKelvins */
        self.header['measured_pressure'] = N.fromstring(l[796:800],N.int32)[0] #INT32 [MAXIMAGES] ; /* Pressure of each chamber in microTorr */
        #/* X-ray source parameters (8*4 bytes) */
        #self.header['source_type'] = N.fromstring(l[896:900],N.int32)[0]  #INT32 ; /* (code) - target, synch. etc */
        #self.header['source_dx'] = N.fromstring(l[900:904],N.int32)[0]  #INT32 ; /* Optics param. - (size microns) */
        #self.header['source_dy'] = N.fromstring(l[904:908],N.int32)[0]  #INT32 ; /* Optics param. - (size microns) */
        self.header['source_wavelength'] = N.fromstring(l[908:912],N.int32)[0]  #INT32 ; /* wavelength (femtoMeters) */
        #self.header['source_power'] = N.fromstring(l[912:916],N.int32)[0]  #INT32 ; /* (Watts) */
        #self.header['source_voltage'] = N.fromstring(l[916:920],N.int32)[0]  #INT32 ; /* (Volts) */
        #self.header['source_current'] = N.fromstring(l[920:924],N.int32)[0]  #INT32 ; /* (microAmps) */
        #self.header['source_bias'] = N.fromstring(l[924:928],N.int32)[0]  #INT32 ; /* (Volts) */
        #self.header['source_polarization_x'] = N.fromstring(l[928:932],N.int32)[0]  #INT32 ; /* () */
        #self.header['source_polarization_y'] = N.fromstring(l[932:936],N.int32)[0]  #INT32 ; /* () */
        #/* X-ray optics_parameters (8*4 bytes) */
        #self.header['optics_type'] = N.fromstring(l[960:964],N.int32)[0]  #INT32 ; /* Optics type (code)*/
        #self.header['optics_dx'] = N.fromstring(l[964:968],N.int32)[0]  #INT32 ; /* Optics param. - (size microns) */
        #self.header['optics_dy'] = N.fromstring(l[968:972],N.int32)[0]  #INT32 ; /* Optics param. - (size microns) */
        #self.header['optics_wavelength'] = N.fromstring(l[972:976],N.int32)[0]  #INT32 ; /* Optics param. - (size microns) */
        #self.header['optics_dispersion'] = N.fromstring(l[976:980],N.int32)[0]  #INT32 ; /* Optics param. - (*10E6) */
        #self.header['optics_crossfire_x'] = N.fromstring(l[980:984],N.int32)[0]  #INT32 ; /* Optics param. - (microRadians) */
        #self.header['optics_crossfire_y'] = N.fromstring(l[984:988],N.int32)[0]  #INT32 ; /* Optics param. - (microRadians) */
        #self.header['optics_angle'] = N.fromstring(l[988:992],N.int32)[0]  #INT32 ; /* Optics param. - (monoch. 2theta microradians) */
        #self.header['optics_polarization_x'] = N.fromstring(l[992:996],N.int32)[0]  #INT32 ; /* () */
        #self.header['optics_polarization_y'] = N.fromstring(l[996:1000],N.int32)[0]  #INT32 ; /* () */
        #/* File parameters (1024 bytes) */
        self.header['filetitle'] = l[1024:1024+l[1024:1152].find(clip)]#char[128]; /* Title */
        self.header['filepath'] = l[1152:1152+l[1152:1280].find(clip)] #char[128]; /* path name for data file */
        self.header['filename'] = l[1280:1280+l[1280:1344].find(clip)] #char[64]; /* name of data file */
        #self.header['acquire_timestamp'] = l[1344:1344+l[1344:1376].find(clip)] #char[32]; /* date and time of acquisition */
        #self.header['header_timestamp'] = l[1376:1376+l[1376:1408].find(clip)] #char[32]; /* date and time of header update */
        #self.header['save_timestamp'] = l[1408:1408+l[1408:1440].find(clip)] #char[32]; /* date and time file saved */
        self.header['file_comments'] = l[1440:1440+l[1440:1952].find(clip)] #char[512]; /* comments - can be used as desired */
        #/* Dataset parameters (512 bytes) */
        self.header['dataset_comments'] = l[2048:2048+l[2048:512].find(clip)] #char[512] ; /* comments - can be used as desired */
