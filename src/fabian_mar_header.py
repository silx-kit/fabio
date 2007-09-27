
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
            Numeric.fromstring(l[0:4], Numeric.UInt32)[0]  
        # UINT32 ; /* flag for header type (can be used as magic number) */
        self.header['header_name'] = l[4:4+l[4:20].find(clip)] # char[16] ; /* header name (MMX) */
        self.header['header_major_version'] = Numeric.fromstring(l[20:24],Numeric.UInt32)[0]  # UINT32 ; /* header_major_version (n.) */
        self.header['header_minor_version'] = Numeric.fromstring(l[24:28],Numeric.UInt32)[0]  # UINT32 ; /* header_minor_version (.n) */
        self.header['header_byte_orde'] = Numeric.fromstring(l[28:32],Numeric.UInt32)[0]  # UINT32 r;/* BIG_ENDIAN (Motorola,MIPS); LITTLE_ENDIAN (DEC, Intel) */
        self.header['data_byte_order'] = Numeric.fromstring(l[32:36],Numeric.UInt32)[0]  # UINT32 ; /* BIG_ENDIAN (Motorola,MIPS); LITTLE_ENDIAN (DEC, Intel) */
        self.header['header_size'] = Numeric.fromstring(l[36:40],Numeric.UInt32)[0]  # UINT32 ; /* in bytes */
        self.header['frame_type'] = Numeric.fromstring(l[40:44],Numeric.UInt32)[0]  # UINT32 ; /* flag for frame type */
        #self.header['magic_number'] = Numeric.fromstring(l[44:48],Numeric.UInt32)[0]  # UINT32 ; /* to be used as a flag - usually to indicate new file */
        #self.header['compression_type'] = Numeric.fromstring(l[48:52],Numeric.UInt32)[0]  # UINT32 ; /* type of image compression */
        #self.header['compression1'] = Numeric.fromstring(l[52:56],Numeric.UInt32)[0]  # UINT32 ; /* compression parameter 1 */
        #self.header['compression2'] = Numeric.fromstring(l[56:60],Numeric.UInt32)[0]  # UINT32 ; /* compression parameter 2 */
        #self.header['compression3'] = Numeric.fromstring(l[60:64],Numeric.UInt32)[0]  # UINT32 ; /* compression parameter 3 */
        #self.header['compression4'] = Numeric.fromstring(l[64:68],Numeric.UInt32)[0]  # UINT32 ; /* compression parameter 4 */
        #self.header['compression5'] = Numeric.fromstring(l[68:72],Numeric.UInt32)[0]  # UINT32 ; /* compression parameter 4 */
        #self.header['compression6'] = Numeric.fromstring(l[72:76],Numeric.UInt32)[0]  # UINT32 ; /* compression parameter 4 */
        #self.header['nheaders'] = Numeric.fromstring(l[76:80],Numeric.UInt32)[0]  # UINT32 ; /* total number of headers */
        self.header['nfast'] = Numeric.fromstring(l[80:84],Numeric.UInt32)[0]  # UINT32 ; /* number of pixels in one line */
        self.header['nslow'] = Numeric.fromstring(l[84:88],Numeric.UInt32)[0]  # UINT32 ; /* number of lines in image */
        self.header['depth'] = Numeric.fromstring(l[88:92],Numeric.UInt32)[0]  # UINT32 ; /* number of bytes per pixel */
        #self.header['record_length'] = Numeric.fromstring(l[92:96],Numeric.UInt32)[0]  # UINT32 ; /* number of pixels between succesive rows */
        self.header['signif_bits'] = Numeric.fromstring(l[96:100],Numeric.UInt32)[0]  # UINT32 ; /* true depth of data, in bits */
        #self.header['data_type'] = Numeric.fromstring(l[100:104],Numeric.UInt32)[0]  # UINT32 ; /* (signed,unsigned,float...) */
        #self.header['saturated_value'] = Numeric.fromstring(l[104:108],Numeric.UInt32)[0]  # UINT32 ; /* value marks pixel as saturated */
        self.header['sequence'] = Numeric.fromstring(l[108:112],Numeric.UInt32)[0]  # UINT32 ; /* TRUE or FALSE */
        self.header['nimages'] = Numeric.fromstring(l[112:116],Numeric.UInt32)[0]  # UINT32 ; /* total number of images - size of each is nfast*(nslow/nimages) */
        self.header['origin'] = Numeric.fromstring(l[116:120],Numeric.UInt32)[0]  # UINT32 ; /* corner of origin */
        self.header['orientation'] = Numeric.fromstring(l[120:124],Numeric.UInt32)[0]  # UINT32 ; /* direction of fast axis */
        self.header['view_direction'] = Numeric.fromstring(l[124:128],Numeric.UInt32)[0]  # UINT32 ; /* direction to view frame */
        self.header['overflow_locatio'] = Numeric.fromstring(l[128:132],Numeric.UInt32)[0]  # UINT32 n;/* FOLLOWING_HEADER, FOLLOWING_DATA */
        self.header['over_8_bits'] = Numeric.fromstring(l[132:136],Numeric.UInt32)[0]  # UINT32 ; /* # of pixels with counts > 255 */
        self.header['over_16_bits'] = Numeric.fromstring(l[136:140],Numeric.UInt32)[0]  # UINT32 ; /* # of pixels with count > 65535 */
        self.header['multiplexed'] = Numeric.fromstring(l[140:144],Numeric.UInt32)[0]  # UINT32 ; /* multiplex flag */
        self.header['nfastimages'] = Numeric.fromstring(l[144:148],Numeric.UInt32)[0]  # UINT32 ; /* # of images in fast direction */
        self.header['nslowimages'] = Numeric.fromstring(l[148:152],Numeric.UInt32)[0]  # UINT32 ; /* # of images in slow direction */
        self.header['background_applied'] = Numeric.fromstring(l[152:156],Numeric.UInt32)[0]  # UINT32 ; /* flags correction has been applied hold magic number ? */
        self.header['bias_applied'] = Numeric.fromstring(l[156:160],Numeric.UInt32)[0]  # UINT32 ; /* flags correction has been applied - hold magic number ? */
        self.header['flatfield_applied'] = Numeric.fromstring(l[160:164],Numeric.UInt32)[0]  # UINT32 ; /* flags correction has been applied hold magic number ? */
        self.header['distortion_applied'] = Numeric.fromstring(l[164:168],Numeric.UInt32)[0]  # UINT32 ; /* flags correction has been applied hold magic number ? */
        #self.header['original_header_type'] = Numeric.fromstring(l[168:172],Numeric.UInt32)[0]  # UINT32 ; /* Header/frame type from file that frame is read from */
        #self.header['file_saved'] = Numeric.fromstring(l[172:176],Numeric.UInt32)[0]  # UINT32 ; /* Flag that file has been saved, should be zeroed if modified */
        #/* Goniostat parameters (128 bytes) */
        self.header['xtal_to_detector'] = Numeric.fromstring(l[640:644],Numeric.Int32)[0]*1000  #INT32 ; /* 1000*distance in millimeters */
        self.header['beam_x'] = Numeric.fromstring(l[644:648],Numeric.Int32)[0]*1000  #INT32 ; /* 1000*x beam position (pixels) */
        self.header['beam_y'] = Numeric.fromstring(l[648:652],Numeric.Int32)[0]*1000  #INT32 ; /* 1000*y beam position (pixels) */
        self.header['integration_time'] = Numeric.fromstring(l[652:656],Numeric.Int32)[0]  #INT32 ; /* integration time in milliseconds */
        self.header['exposure_time'] = Numeric.fromstring(l[656:660],Numeric.Int32)[0]  #INT32 ; /* exposure time in milliseconds */
        self.header['readout_time'] = Numeric.fromstring(l[660:664],Numeric.Int32)[0]  #INT32 ; /* readout time in milliseconds */
        self.header['nreads'] = Numeric.fromstring(l[664:668],Numeric.Int32)[0]  #INT32 ; /* number of readouts to get this image */
        self.header['start_twotheta'] = Numeric.fromstring(l[668:672],Numeric.Int32)[0]*1000  #INT32 ; /* 1000*two_theta angle */
        self.header['start_omega'] = Numeric.fromstring(l[676:680],Numeric.Int32)[0]*1000  #INT32 ; /* 1000*omega angle */
        self.header['start_chi'] = Numeric.fromstring(l[680:684],Numeric.Int32)[0]*1000  #INT32 ; /* 1000*chi angle */
        self.header['start_kappa'] = Numeric.fromstring(l[684:688],Numeric.Int32)[0]*1000  #INT32 ; /* 1000*kappa angle */
        self.header['start_phi'] = Numeric.fromstring(l[688:692],Numeric.Int32)[0]*1000  #INT32 ; /* 1000*phi angle */
        self.header['start_delta'] = Numeric.fromstring(l[692:696],Numeric.Int32)[0]*1000  #INT32 ; /* 1000*delta angle */
        self.header['start_gamma'] = Numeric.fromstring(l[696:700],Numeric.Int32)[0]*1000  #INT32 ; /* 1000*gamma angle */
        self.header['start_xtal_to_detector'] = Numeric.fromstring(l[700:704],Numeric.Int32)[0]*1000  #INT32 ; /* 1000*distance in mm (dist in um)*/
        self.header['end_twotheta'] = Numeric.fromstring(l[704:708],Numeric.Int32)[0]*1000  #INT32 ; /* 1000*two_theta angle */
        self.header['end_omega'] = Numeric.fromstring(l[708:712],Numeric.Int32)[0]*1000  #INT32 ; /* 1000*omega angle */
        self.header['end_chi'] = Numeric.fromstring(l[712:716],Numeric.Int32)[0]*1000  #INT32 ; /* 1000*chi angle */
        self.header['end_kappa'] = Numeric.fromstring(l[716:720],Numeric.Int32)[0]*1000  #INT32 ; /* 1000*kappa angle */
        self.header['end_phi'] = Numeric.fromstring(l[720:724],Numeric.Int32)[0]*1000  #INT32 ; /* 1000*phi angle */
        self.header['end_delta'] = Numeric.fromstring(l[724:728],Numeric.Int32)[0]*1000  #INT32 ; /* 1000*delta angle */
        self.header['end_gamma'] = Numeric.fromstring(l[728:732],Numeric.Int32)[0]*1000  #INT32 ; /* 1000*gamma angle */
        self.header['end_xtal_to_detector'] = Numeric.fromstring(l[732:736],Numeric.Int32)[0]*1000  #INT32 ; /* 1000*distance in mm (dist in um)*/
        self.header['rotation_axis'] = Numeric.fromstring(l[736:740],Numeric.Int32)[0]  #INT32 ; /* active rotation axis */
        self.header['rotation_range'] = Numeric.fromstring(l[740:744],Numeric.Int32)[0]*1000  #INT32 ; /* 1000*rotation angle */
        self.header['detector_rotx'] = Numeric.fromstring(l[744:748],Numeric.Int32)[0]*1000  #INT32 ; /* 1000*rotation of detector around X */
        self.header['detector_roty'] = Numeric.fromstring(l[748:752],Numeric.Int32)[0]*1000  #INT32 ; /* 1000*rotation of detector around Y */
        self.header['detector_rotz'] = Numeric.fromstring(l[752:756],Numeric.Int32)[0]*1000  #INT32 ; /* 1000*rotation of detector around Z */
        #/* Detector parameters (128 bytes) */
        self.header['detector_type'] = Numeric.fromstring(l[768:772],Numeric.Int32)[0]  #INT32 ; /* detector type */
        self.header['pixelsize_x'] = Numeric.fromstring(l[772:776],Numeric.Int32)[0]  #INT32 ; /* pixel size (nanometers) */
        self.header['pixelsize_y'] = Numeric.fromstring(l[776:780],Numeric.Int32)[0]  #INT32 ; /* pixel size (nanometers) */
        self.header['mean_bias'] = Numeric.fromstring(l[780:784],Numeric.Int32)[0]*1000  #INT32 ; /* 1000*mean bias value */
        self.header['photons_per_100adu'] = Numeric.fromstring(l[784:788],Numeric.Int32)[0]  #INT32 ; /* photons / 100 ADUs */
        self.header['measured_bias'] = Numeric.fromstring(l[788:792],Numeric.Int32)[0]*1000  #INT32 [MAXIMAGES]; /* 1000*mean bias value for each image*/
        self.header['measured_temperature'] = Numeric.fromstring(l[792:796],Numeric.Int32)[0] #INT32  [MAXIMAGES]; /* Temperature of each detector in milliKelvins */
        self.header['measured_pressure'] = Numeric.fromstring(l[796:800],Numeric.Int32)[0] #INT32 [MAXIMAGES] ; /* Pressure of each chamber in microTorr */
        #/* X-ray source parameters (8*4 bytes) */
        #self.header['source_type'] = Numeric.fromstring(l[896:900],Numeric.Int32)[0]  #INT32 ; /* (code) - target, synch. etc */
        #self.header['source_dx'] = Numeric.fromstring(l[900:904],Numeric.Int32)[0]  #INT32 ; /* Optics param. - (size microns) */
        #self.header['source_dy'] = Numeric.fromstring(l[904:908],Numeric.Int32)[0]  #INT32 ; /* Optics param. - (size microns) */
        self.header['source_wavelength'] = Numeric.fromstring(l[908:912],Numeric.Int32)[0]  #INT32 ; /* wavelength (femtoMeters) */
        #self.header['source_power'] = Numeric.fromstring(l[912:916],Numeric.Int32)[0]  #INT32 ; /* (Watts) */
        #self.header['source_voltage'] = Numeric.fromstring(l[916:920],Numeric.Int32)[0]  #INT32 ; /* (Volts) */
        #self.header['source_current'] = Numeric.fromstring(l[920:924],Numeric.Int32)[0]  #INT32 ; /* (microAmps) */
        #self.header['source_bias'] = Numeric.fromstring(l[924:928],Numeric.Int32)[0]  #INT32 ; /* (Volts) */
        #self.header['source_polarization_x'] = Numeric.fromstring(l[928:932],Numeric.Int32)[0]  #INT32 ; /* () */
        #self.header['source_polarization_y'] = Numeric.fromstring(l[932:936],Numeric.Int32)[0]  #INT32 ; /* () */
        #/* X-ray optics_parameters (8*4 bytes) */
        #self.header['optics_type'] = Numeric.fromstring(l[960:964],Numeric.Int32)[0]  #INT32 ; /* Optics type (code)*/
        #self.header['optics_dx'] = Numeric.fromstring(l[964:968],Numeric.Int32)[0]  #INT32 ; /* Optics param. - (size microns) */
        #self.header['optics_dy'] = Numeric.fromstring(l[968:972],Numeric.Int32)[0]  #INT32 ; /* Optics param. - (size microns) */
        #self.header['optics_wavelength'] = Numeric.fromstring(l[972:976],Numeric.Int32)[0]  #INT32 ; /* Optics param. - (size microns) */
        #self.header['optics_dispersion'] = Numeric.fromstring(l[976:980],Numeric.Int32)[0]  #INT32 ; /* Optics param. - (*10E6) */
        #self.header['optics_crossfire_x'] = Numeric.fromstring(l[980:984],Numeric.Int32)[0]  #INT32 ; /* Optics param. - (microRadians) */
        #self.header['optics_crossfire_y'] = Numeric.fromstring(l[984:988],Numeric.Int32)[0]  #INT32 ; /* Optics param. - (microRadians) */
        #self.header['optics_angle'] = Numeric.fromstring(l[988:992],Numeric.Int32)[0]  #INT32 ; /* Optics param. - (monoch. 2theta microradians) */
        #self.header['optics_polarization_x'] = Numeric.fromstring(l[992:996],Numeric.Int32)[0]  #INT32 ; /* () */
        #self.header['optics_polarization_y'] = Numeric.fromstring(l[996:1000],Numeric.Int32)[0]  #INT32 ; /* () */
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
