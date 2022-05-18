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
        iname = re.sub('\_[^\_]*$','',iname)
        # get variance from _infoFile.txt
        fh = open(infile, "r").read()
        k = re.findall("K = (.*)", fh)
        k = k[0] if k else np.nan
        v = re.findall("Variance = (.*)", fh)
        v = v[0] if v else np.nan
        # get the link to graphs
        vgraph = os.path.join(dname, f"{iname}_outGraph_VValue.png")
        vgraph = vgraph if os.path.isfile(vgraph) else np.nan        
        rgraph = os.path.join(dname, f"{iname}_outGraph_VRank.png")
        rgraph = rgraph if os.path.isfile(rgraph) else np.nan        
        # return data
        df = pd.DataFrame([(sname,iname,k,v,vgraph,rgraph)], columns=cols)
    except Exception as exc:
        print("ERROR!! Getting the time values:\n{}".format(exc), flush=True)
    return df


def main(args):
    '''
    Main function
    '''
    logging.info("getting the list of info files...")
    infiles = glob.glob(os.path.join(args.indir,'**/*_kinfoFile.txt'), recursive = True)
    if not infiles:
        sys.exit("ERROR!! There are not input files")
    
    
    logging.info(f"getting values for every file in parallel ({args.n_workers})...")
    cols = ['sample','integration','kvalue','variance','vvalue_graph','rank_graph']
    # with concurrent.futures.ProcessPoolExecutor(max_workers=args.n_workers) as executor:            
    #     ddf = executor.map( get_values, infiles, repeat(cols) )
    # ddf = pd.concat(ddf)
    # begin: for debugging in Spyder
    ddf = get_values( infiles[2], cols)
    # end: for debugging in Spyder
    
    logging.info("sorting by...")
    ddf.sort_values(['integration','sample'], ascending=False, inplace=True)
    
    logging.info('printing tsv output...')
    ddf.to_csv(args.outfile, index=False, sep="\t", line_terminator='\n', columns=[c for c in cols if c != 'vvalue_graph' and c!= 'rank_graph'])
    
    logging.info('printing html output...')
    # include the sigmoide image in base64
    ddf_html = ddf.to_html(index=False, escape=False, justify='center', formatters={'vvalue_graph': image_formatter,'rank_graph': image_formatter}, columns=cols)
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
        description='Extract the values from calibration',
        epilog='''
        Example:
            python getKlibrateVals.py -i jobs/ -o stats/klibrates.tsv

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