
def convert_header(header, fimg=None):
    """Convert a CBF header into a Bruker100 header
    
    :param header: CBF header
    :param fimg: The complete CbfImage object ...  
    """"
    new = {"VERSION": "18",
           "TYPE": 'Some Frame',
           'SITE': 'Some Site',
           "MODEL": "?",
           "USER": "FabIO Converter",
           "SAMPLE": "Not specified",
           "SETNAME": "",
           "RUN": "1",
           "SAMPNUM": "1",
           "TITLE": "\n"*8,
           
           
           }
    return new
    
    
     