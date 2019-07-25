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
import pandas
import glob
import re
from time import strftime

###################
# Local functions #
###################
def main(args):
    '''
    Main function
    '''
    logging.info("get the list of SanXoT results from the given directory")
    listfiles = [f for f in glob.glob( args.indir+"/**/"+args.regex, recursive=True )]
    logging.debug(listfiles)

    logging.info("merge the list of results")
    li = []
    for filename in listfiles:
        # extract the experiment name and tag name from the file name
        # spl = re.compile('[/|\\]').split(filename)
        spl = re.split(r'/|\\', filename)
        tag = spl[-2]
        exp = spl[-3]
        # read and add the experiment and tag columns
        df = pandas.read_csv(filename, sep="\t", low_memory=False, encoding='ISO-8859-1')
        df['Tag']   = tag
        df['Expto'] = exp
        # append for the merge with the rest
        li.append(df)
    # merge all the files
    df_all = pandas.concat(li, ignore_index=True)

    logging.info("write ouput file")
    df_all.to_csv( args.outfile, sep="\t", index=False)



if __name__ == "__main__":
    # parse arguments
    parser = argparse.ArgumentParser(
        description='Merge the all SanXoT results depending on the list of input file names (prefixes)',
        epilog='''
        Example:
            python collector.py
        ''')        
    parser.add_argument('-i',  '--indir',    required=True, help='Input directory with SanXoT results')
    parser.add_argument('-r',  '--regex',    required=True, help='Regular expression that selects the specific SanXoT results')
    parser.add_argument('-o',  '--outfile',   required=True, help='Output file')
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
