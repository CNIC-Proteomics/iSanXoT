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
import pandas as pd


###################
# Local functions #
###################


def main(args):
    '''
    Main function
    '''
    logging.info("read input file")
    indat = pd.read_csv(args.infile, sep="\t", comment='#', na_values=['NA'], low_memory=False)


    logging.info("join the columns sequence+modifications to have unique peptides")
    indat['Seq+Mod'] = indat['Sequence']+'+'+indat['Modifications']
    
    logging.info("get statistics from identification results")
    # For Comet-PTM
    # outdat = indat.groupby('Filename').agg({
    #     'Raw_FirstScan': 'count',
    #     'SiteSequence': lambda x: len(x.unique()),
    #     'Protein_Accession': lambda x: len(x.unique())
    # })
    outdat = indat.groupby('Spectrum_File').agg({
        'Scan_Id': 'count',
        'Seq+Mod': lambda x: len(x.unique()),
        'Protein_MPP': lambda x: len(x.unique())
    })
    outdat = outdat.reset_index()
    outdat.rename(columns={'Spectrum_File': 'spectrum_files', 'Scan_Id':'scans', 'Seq+Mod': 'peptides', 'Protein_MPP': 'proteins'}, inplace=True)

    
    logging.info('print output')
    outdat.to_csv(args.outfile, sep="\t", index=False)


if __name__ == '__main__':
    # parse arguments
    parser = argparse.ArgumentParser(
        description='Create the statistics from ID file',
        epilog='''
        Example:
            python getIDstats.py -i ID.tsv -o stats_ID.tsv

        ''')
    parser.add_argument('-i',  '--infile', required=True, help='Input file: ID.tsv')
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