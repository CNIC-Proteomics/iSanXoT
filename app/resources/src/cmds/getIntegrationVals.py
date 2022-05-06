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
import concurrent.futures
from itertools import repeat


#########################
# Import local packages #
#########################
sys.path.append(f"{os.path.dirname(__file__)}/../libs")
import common

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

def get_values(infile,cols):
    # init output
    df = pd.DataFrame(columns=cols)
    try:
        # get dir name (integration)
        dname = os.path.dirname(infile)
        # get file name
        fname = os.path.basename(infile)
        # get the sample name
        sname = common.get_job_name(infile)
        # get integration name
        iname = os.path.splitext(fname)[0]
        iname = re.sub('\_.*$','',iname)
        # get variance from _infoFile.txt
        fh = open(infile, "r").read()
        v = re.findall("Variance = (.*)", fh)
        v = v[0] if v else np.nan
        # get the N elems from the _outStats.tsv
        sfile = os.path.join(dname, f"{iname}_outStats.tsv")
        df = pd.read_csv(sfile, sep="\t", index_col=False)
        nt = len(df) # total N elems
        ne = df[df['tags'] != '']['tags'].count() # excluded N elems
        ni = nt - ne # integrated N elems
        # get the link to sigmoide... Important: The sigmoide with outliers (first sanxot)
        sgraph = os.path.join(dname, f"{iname}_outGraph1.png")
        sgraph = sgraph if os.path.isfile(sgraph) else np.nan        
        # return data
        df = pd.DataFrame([(sname,iname,v,nt,ne,ni,sgraph)], columns=cols)
    except Exception as exc:
        print("ERROR!! Getting the time values:\n{}".format(exc), flush=True)
    return df



def main(args):
    '''
    Main function
    '''
    logging.info("getting the list of info files...")
    infiles = glob.glob(os.path.join(args.indir,'**/*_infoFile.txt'), recursive = True)
    if not infiles:
        sys.exit("ERROR!! There are not input files")
    # only accepts the files with the structure "low_level2high_level"
    infiles = [ i for i in infiles if re.search(r'([^2]+)2([^\.]+)', os.path.basename(i))]
    
    
    logging.info(f"getting values for every file in parallel ({args.n_workers})...")
    cols = ['sample','integration','variance','totalNelems','excludedNelems','integratedNelems','sigmoide']
    with concurrent.futures.ProcessPoolExecutor(max_workers=args.n_workers) as executor:            
        ddf = executor.map( get_values, infiles, repeat(cols) )
    ddf = pd.concat(ddf)
    # begin: for debugging in Spyder
    # ddf = get_values( infiles[2], cols)
    # end: for debugging in Spyder

        
    logging.info("sorting by...")
    ddf.sort_values(['integration','sample'], ascending=False, inplace=True)
    
    logging.info('printing tsv output...')
    ddf.to_csv(args.outfile, index=False, sep="\t", line_terminator='\n', columns=[c for c in cols if c != 'sigmoide'])
    
    logging.info('printing html output...')
    # include the sigmoide image in base64
    ddf_html = ddf.to_html(index=False, escape=False, justify='center', formatters={'sigmoide': image_formatter}, columns=cols)
    outhtml = f'''
<!DOCTYPE html>
<html>
<head lang='en'>
    <meta charset='UTF-8'>
    <title>Variance report</title>
</head>
<body>
    <h2>Variance report</h2>
     {ddf_html}
</body>
</html>'''
    f = os.path.splitext(os.path.basename(args.outfile))[0]+'.html'
    f = os.path.join( os.path.dirname(args.outfile), f)
    fh = open(f, "w")
    fh.write(outhtml)
    fh.close()

    
    

if __name__ == '__main__':
    # parse arguments
    parser = argparse.ArgumentParser(
        description='Extract the values from integrations',
        epilog='''
        Example:
            python getIntegrationVals.py -i jobs/ -o stats/variances.tsv

        ''')
    parser.add_argument('-w',   '--n_workers', type=int, default=2, help='Number of threads/n_workers (default: %(default)s)')
    parser.add_argument('-i',  '--indir', required=True, help='Input Directory')
    parser.add_argument('-o',  '--outfile',   required=True, help='Output file')
    parser.add_argument('-x',  '--phantom_files',  help='Phantom output files needed for the handle of iSanXoT workflow (snakemake)')
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