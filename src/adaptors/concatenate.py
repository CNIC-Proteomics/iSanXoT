#!/usr/bin/python

# Module metadata variables
__author__ = "Jose Rodriguez"
__credits__ = ["Jose Rodriguez", "Jesus Vazquez"]
__license__ = "Creative Commons Attribution-NonCommercial-NoDerivs 4.0 Unported License https://creativecommons.org/licenses/by-nc-nd/4.0/"
__version__ = "0.0.1"
__maintainer__ = "Jose Rodriguez"
__email__ = "jmrodriguezc@cnic.es"
__status__ = "Development"

# import global modules
import os
import sys
import argparse
import logging
from time import strftime

###################
# Local functions #
###################
def join(files, outfile):
    '''
    Concatenate text files
    '''
    with open(outfile, 'w') as outfname:
        for fname in files:
            with open(fname) as infile:
                for line in infile:
                    outfname.write(line)
def main(args):
    '''
    Main function
    '''
    logging.info("join input files")
    join(args.infiles, args.outfile)



if __name__ == "__main__":
    # parse arguments
    parser = argparse.ArgumentParser(
        description='Join files',
        epilog='''
        Example:
            python concatenate.py -ii ~/indir/file1.txt ~/indir/indir2/file2.txt -o ~/outdir/outfile.txt
        ''')
    parser.add_argument('-ii',  '--infiles',  required=True, nargs='+', help='Input files')
    parser.add_argument('-o',   '--outfile',  required=True, help='Joined file')
    parser.add_argument('-v', dest='verbose', action='store_true', help="Increase output verbosity")
    args = parser.parse_args()

    # logging debug level. By default, info level
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG,
                            format='%(asctime)s - %(levelname)s - %(message)s',
                            datefmt='%m/%d/%Y %I:%M:%S %p')
    else:
        logging.basicConfig(level=logging.INFO,
                            format='%(asctime)s - %(levelname)s - %(message)s',
                            datefmt='%m/%d/%Y %I:%M:%S %p')

    # start main function
    logging.info("** {} - {} - start script : {}".format( strftime("%Y-%m-%d %H:%M:%S"), os.getpid(), " ".join([x for x in sys.argv]) ))
    main(args)
    logging.info("** {} - {} - end  script : {}".format( strftime("%Y-%m-%d %H:%M:%S"), os.getpid(), os.path.basename(__file__) ))