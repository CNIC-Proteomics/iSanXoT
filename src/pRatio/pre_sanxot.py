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

import core

###################
# Local functions #
###################
def main(args):
    '''
    Main function
    '''
    logging.info("create builder")
    c = core.builder(args.infile, args.n_workers)

    logging.info("get the parameters from the input data file")
    Expt, lblCtr = c.infiles_adv(args.datfile)

    logging.info("calculate ratios")
    df = c.calculate_ratio(Expt, lblCtr)

    logging.info('print output file')
    c.to_csv(df, args.outfile)




if __name__ == "__main__":
    # parse arguments
    parser = argparse.ArgumentParser(
        description='Calculate the ratios',
        epilog='''
        Example:
            python pre_sanxot.py
        ''')
    parser.add_argument('-w',  '--n_workers', type=int, help='Number of threads (n_workers)')
    parser.add_argument('-i',  '--infile', required=True, help='Input file with Identification: ID.tsv')
    parser.add_argument('-d',  '--datfile', required=True, help='File with the input data: experiments, task-name, ratio (num/den),...')
    parser.add_argument('-o',  '--outfile', required=True, help='ID-q file')
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
    logging.info('start script: '+"{0}".format(" ".join([x for x in sys.argv])))
    main(args)
    logging.info('end script')