#!/usr/bin/python

# Module metadata variables
__author__ = ["Jose Rodriguez"]
__credits__ = ["Ricardo Magni", "Jesus Vazquez", "Jose Rodriguez"]
__license__ = "Creative Commons Attribution-NonCommercial-NoDerivs 4.0 Unported License https://creativecommons.org/licenses/by-nc-nd/4.0/"
__version__ = "1.0.1"
__maintainer__ = "Jose Rodriguez"
__email__ = "jmrodriguezc@cnic.es"
__status__ = "Development"

# import global modules
import os
import sys
import argparse
import logging
import glob
import re
import pandas as pd
import numpy as np
import base64
from PIL import Image
from io import BytesIO



###################
# Local functions #
###################

def get_thumbnail(path):
    i = Image.open(path)
    i.thumbnail((300, 300), Image.LANCZOS)
    return i

def image_base64(im):    
    try:
        if isinstance(im, str):
            im = get_thumbnail(im)
        with BytesIO() as buffer:
            im.save(buffer, 'png')
            return base64.b64encode(buffer.getvalue()).decode()
        pass
    except Exception:
        sms = f"Unrecognized data stream contents when reading image file: {im}"
        logging.warning(sms)
        return ''
        pass

def image_formatter(im):
    return f'<img src="data:image/png;base64,{image_base64(im)}">'



def main(args):
    '''
    Main function
    '''
    logging.info("get the list of variance files from input folder recursively")
    infiles = glob.glob(os.path.join(args.indir,'**/*_variance.txt'), recursive = True)
    if not infiles:
        sys.exit("ERROR!! There are not variance files")
    
    
    logging.info("read every file and extract the integration/variance")
    dat = []    
    for infile in infiles:
        # get dir name (integration)
        dname = os.path.dirname(infile)
        bname = os.path.basename(dname)
        
        # get file name of script
        fname = os.path.splitext(os.path.basename(infile))[0]
        fname = re.sub('\_.*$','',fname)
        
        # get variance
        fh = open(infile, "r").read()
        v = re.findall("Variance = (.*)", fh)
        v = v[0] if v else np.nan
        
        # get the link to sigmoide
        sname = os.path.join(dname, f"{fname}_outGraph.png")
        sname = sname if os.path.isfile(sname) else np.nan
        
        # append data
        dat.append((bname,fname,v,sname))
    
    
    logging.info("create a dataframe with the integration/variance")
    outdat = pd.DataFrame(dat, columns=['name','integration','variance','sigmoide'])
    

    logging.info('print html output')
    # include the sigmoide image in base64
    outdat_html = outdat.to_html(index=False, escape=False, justify='center', formatters={'sigmoide': image_formatter})
    outhtml = f'''
<!DOCTYPE html>
<html>
<head lang='en'>
    <meta charset='UTF-8'>
    <title>Variance report</title>
</head>
<body>
    <h2>Variance report</h2>
     {outdat_html}
</body>
</html>'''
    f = open(args.outfile, "w")
    f.write(outhtml)
    f.close()

    
    

if __name__ == '__main__':
    # parse arguments
    parser = argparse.ArgumentParser(
        description='Create the statistics from the integration folders',
        epilog='''
        Example:
            python getVariances.py -i jobs/ -o stats/variances.tsv

        ''')
    parser.add_argument('-i',  '--indir', required=True, help='Input Directory')
    parser.add_argument('-o',  '--outfile',   required=True, help='Output file')
    parser.add_argument('-vv', dest='verbose', action='store_true', help="Increase output verbosity")
    args = parser.parse_args()

    # get the name of script
    script_name = os.path.splitext( os.path.basename(__file__) )[0].upper()

    # logging debug level. By default, info level
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG,
                            format=script_name+' - '+str(os.getpid())+' - %(asctime)s - %(levelname)s - %(message)s',
                            datefmt='%m/%d/%Y %I:%M:%S %p')
    else:
        logging.basicConfig(level=logging.INFO,
                            format=script_name+' - '+str(os.getpid())+' - %(asctime)s - %(levelname)s - %(message)s',
                            datefmt='%m/%d/%Y %I:%M:%S %p')

    # start main function
    logging.info('start script: '+"{0}".format(" ".join([x for x in sys.argv])))
    main(args)
    logging.info('end script')