#!/usr/bin/python

# import global modules
import os
import sys
import argparse
import logging
import pandas
import concurrent.futures
import pandas as pd


# Module metadata variables
__author__ = "Jose Rodriguez"
__credits__ = ["Jose Rodriguez", "Jesus Vazquez"]
__license__ = "Creative Commons Attribution-NonCommercial-NoDerivs 4.0 Unported License https://creativecommons.org/licenses/by-nc-nd/4.0/"
__version__ = "1.0.1"
__maintainer__ = "Jose Rodriguez"
__email__ = "jmrodriguezc@cnic.es"
__status__ = "Development"


#########################
# Import local packages #
#########################
sys.path.append(f"{os.path.dirname(__file__)}/../libs")
import common

####################
# Global variables #
####################
COLUMN_ELEMENT = ['Id','Xs','Vs']

###################
# Local functions #
###################
def parse_arguments(argv):
    # parse arguments
    parser = argparse.ArgumentParser(
        description='Program that join multiple files in one',
        epilog='''Examples:
        python  src/SanXoT/joiner.py
          -ii TMT1/ID-q.tsv;TMT2/ID-q.tsv
          -o ID-q.tsv
        ''',
        formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('-w',  '--n_workers', type=int, default=2, help='Number of threads/n_workers (default: %(default)s)')
    parser.add_argument('-ii',  '--infiles',  required=True, help='Multiple input files separated by comma')
    parser.add_argument('-o',  '--outfile', required=True, help='Output file with the masterQ column')
    parser.add_argument('-vv', dest='verbose', action='store_true', help="Increase output verbosity")
    args = parser.parse_args(argv)

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
    return args

def read_infiles(file):
    # rename the column headers
    indat = pandas.read_csv(file, sep="\t", comment='#', na_values=['NA'], low_memory=False)
    indat.columns = COLUMN_ELEMENT
    return indat

#################
# Main function #
#################
def main(argv):
    '''
    Main function
    '''
    # PARSE ARGUMENTS ---
    args = parse_arguments(argv)
    
    logging.info("read files")
    with concurrent.futures.ProcessPoolExecutor(max_workers=args.n_workers) as executor:            
        indat = executor.map(read_infiles,args.infiles.split(";"))
    indat = pd.concat(indat)
    
    logging.info('print output')
    # print to tmp file
    f = f"{args.outfile}.tmp"
    indat.to_csv(f, sep="\t", index=False)
    # rename tmp file deleting before the original file 
    common.rename_tmpfile(f)




if __name__ == "__main__":
    # start main function
    logging.info('start script: '+"{0}".format(" ".join([x for x in sys.argv])))
    main(sys.argv[1:])
    logging.info('end script')
