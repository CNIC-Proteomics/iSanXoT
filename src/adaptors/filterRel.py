#!/usr/bin/python

# import global modules
import os
import sys
import argparse
import logging
import pandas as pd
import numpy as np
import re
import concurrent.futures


# Module metadata variables
__author__ = "Jose Rodriguez"
__credits__ = ["Jose Rodriguez", "Jesus Vazquez"]
__license__ = "Creative Commons Attribution-NonCommercial-NoDerivs 4.0 Unported License https://creativecommons.org/licenses/by-nc-nd/4.0/"
__version__ = "1.0.1"
__maintainer__ = "Jose Rodriguez"
__email__ = "jmrodriguezc@cnic.es"
__status__ = "Development"

###################
# Local functions #
###################
def read_infiles(file):
    indat = pd.read_csv(file, sep="\t", na_values=['NA'], low_memory=False)
    return indat


#################
# Main function #
#################
def main(args):
    '''
    Main function
    '''    
    logging.info("read infiles")
    with concurrent.futures.ProcessPoolExecutor(max_workers=args.n_workers) as executor:            
        indat = executor.map( read_infiles,re.split(r'\s*;\s*', args.infiles.strip()) )
    indat = pd.concat(indat)

    # discards the tags
    logging.info("discard the given tags")
    if args.tags and not args.tags.isspace():
        for t in re.split(r'\s*&\s*', args.tags.strip()):
            if t.startswith('!') or t.startswith('\!') or t.startswith('/!'):
                t = t.replace('!','').replace('\!','').replace('/!','')
                indat.iloc[:,2].replace(np.nan, '', regex=True, inplace=True)
                indat = indat[indat.iloc[:,2] != t ]
    
    logging.info("print output file without header")
    indat.to_csv(args.outfile, sep="\t", index=False)



if __name__ == "__main__":
    # parse arguments
    parser = argparse.ArgumentParser(
        description='Filters the third column from the given relationship files',
        epilog='''Examples:
        python  src/SanXoT/createSansonHighLevel.py
          -ii w1/p2c_tagged.tsv;w2/p2c_tagged.tsv
          -t '!out'
          -o p2c_filt.tsv
        ''',
        formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('-w',  '--n_workers', type=int, default=2, help='Number of threads/n_workers (default: %(default)s)')
    parser.add_argument('-ii',  '--infiles',  required=True, help='Multiple relationship files separated by comma')
    parser.add_argument('-o',  '--outfile',  required=True, help='Output file with the relationship table')
    parser.add_argument('-t',  '--tags',     help='Multiple Relationship file separated by comma')
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
