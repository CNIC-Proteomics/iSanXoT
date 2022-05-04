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



def main(args):
    '''
    Main function
    '''
    logging.info("get the list of variance files from input folder recursively")
    infiles = glob.glob(os.path.join(args.indir,'**/*_infoFile.txt'), recursive = True)
    if not infiles:
        sys.exit("ERROR!! There are not variance files")
    # only accepts the files with the structure "low_level2high_level"
    infiles = [ i for i in infiles if re.search(r'([^2]+)2([^\.]+)', os.path.basename(i))]
    
    
    logging.info("read every file and extract the integration/variance")
    dat = []    
    for infile in infiles:
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
        # get the N elems depending of the type of integration
        if re.search(r'[^2]+2.*(all)', iname): # integrations to all
            # get the TotalNElements based on the _outStats.tsv
            sfile = os.path.join(dname, f"{iname}_outStats.tsv")
            df = pd.read_csv(sfile, nrows=1, sep="\t", index_col=False)
            ni = df['n'][0] # integrated N elems
            nt,ne = ni,ni # total N and excluded N are the same than integrated N elems
        else: # the rest of integrations
            # get the total N elements from _infoFile.txt
            n = re.findall('Total elements excluded using tags: (\d+) \(of (\d+)\)', fh)
            if n:
                n = n[0] # [('totalN','excluN')]
                nt = n[1] # total N elems
                ne = n[0] # excluded N elems
                ni = int(n[1])-int(n[0]) # integrated N elems
            else:
                nt,ne,ni = np.nan,np.nan,np.nan
                
        # get the link to sigmoide... Important: The sigmoide with outliers (first sanxot)
        gname = os.path.join(dname, f"{iname}_outGraph1.png")
        gname = gname if os.path.isfile(gname) else np.nan        
        # append data
        dat.append((sname,iname,v,nt,ne,ni,gname))
    
    
    logging.info("create a dataframe with the integration/variance")
    cols = ['sample','integration','variance','totalNelems','excludedNelems','integratedNelems','sigmoide']
    outdat = pd.DataFrame(dat, columns=cols)
    
    # sort by integrations
    outdat.sort_values(['integration','sample'], ascending=False, inplace=True)
    
    logging.info('print tsv output')
    outdat.to_csv(args.outfile, index=False, sep="\t", line_terminator='\n', columns=[c for c in cols if c != 'sigmoide'])
    
    logging.info('print html output')
    # include the sigmoide image in base64
    outdat_html = outdat.to_html(index=False, escape=False, justify='center', formatters={'sigmoide': image_formatter}, columns=cols)
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
    f = os.path.splitext(os.path.basename(args.outfile))[0]+'.html'
    f = os.path.join( os.path.dirname(args.outfile), f)
    fh = open(f, "w")
    fh.write(outhtml)
    fh.close()

    
    

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