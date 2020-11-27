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

# import core_dask as core
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

    # logging.info("converter the evidence file from MaXQuant to ID-q (label-free result)")
    # df = c.evidence2idq()

    # logging.info('print output file')
    # c.to_csv(df, args.outfile)

    logging.info("converter the evidence file from MaXQuant to ID-q (label-free result)")
    df = c.modificationSpecificPeptides2idq()

    logging.info("add the species column")
    df = c.addSpecies(args.dbfile, df)

    logging.info('print output file')
    c.to_csv(df, args.outfile)



if __name__ == "__main__":
    # parse arguments
    parser = argparse.ArgumentParser(
        description='Convert the result from MaxQuant (txt/evidences) to ID-q file: label-free',
        epilog='''
        Example:
            python convert2idq.py
        ''')
    parser.add_argument('-w',  '--n_workers', type=int, help='Number of threads (n_workers)')
    parser.add_argument('-i',  '--infile',    required=True, help='Input file with MaxQuant result: modificationSpecificPeptides.txt')
    parser.add_argument('-d',  '--dbfile',    required=True, help='Database file in FASTA format')
    parser.add_argument('-o',  '--outfile',   required=True, help='ID-q file')
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