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

#########################
# Import local packages #
#########################
sys.path.append(f"{os.path.dirname(__file__)}/../libs")
import common

###################
# Local functions #
###################
def read_infiles(file):
    indat = pd.read_csv(file, sep="\t", na_values=['NA'], low_memory=False)
    return indat

def read_relfiles(file):
    indat = pd.read_csv(file, sep="\t", usecols=['idinf','idsup','n','tags'], na_values=['NA'], low_memory=False)
    return indat

#################
# Main function #
#################
# BEGIN: OLD DESCRIPTION --
# Workflow stops here for the preparation of the file C2A_outStats_clean.tsv following these steps:
# i  ) Duplicate the C2A_outStats.tsv file;
# ii ) Rename the duplicate file to C2A_outStats_clean.tsv;
# iii) Remove the unnecessary categories; bear in mind that when a comma is present in a category name.
#         VLOOKUP will produce a "Not found" result.
#         So any commas must be removed from the category names in all these files:
#           C2A_outStats.tsv, Q2C_noOuts_outStats.tsv and Q2COuts_tagged.tsv
# iv ) Remove all the information (including all the headings) except for the
#         names of the relevant categories.
# END: OLD DESCRIPTION --
def main(args):
    '''
    Main function
    '''
    
    logging.info("read stats files")
    # indat = pd.read_csv(args.infiles, sep="\t", na_values=['NA'], low_memory=False)
    with concurrent.futures.ProcessPoolExecutor(max_workers=args.n_workers) as executor:            
        indat = executor.map( read_infiles,re.split(r'\s*;\s*', args.infiles.strip()) )
    indat = pd.concat(indat)


    logging.info("read relationship files")
    # redat = pd.read_csv(args.refiles, sep="\t", usecols=['idinf','idsup','n','tags'], na_values=['NA'], low_memory=False)
    with concurrent.futures.ProcessPoolExecutor(max_workers=args.n_workers) as executor:            
        redat = executor.map( read_relfiles,re.split(r'\s*;\s*', args.refiles.strip()) )
    redat = pd.concat(redat)
    # rename columns of relation file because we are going to use the 'idsup' as 'idinf'
    redat.rename(columns={'idinf':'idinf_rel', 'idsup':'idinf', 'n':'n_rel', 'tags':'tags_rel'}, inplace=True)

    # merge (intersection) df's based on 'idinf' column
    logging.info("merge df's based on 'idinf' column")
    indat = pd.merge(indat,redat, on='idinf')

    # discards the tags
    logging.info("discard the given tags")
    if args.tags and not args.tags.isspace():
        for t in re.split(r'\s*&\s*', args.tags.strip()):
            if t.startswith('!') or t.startswith('\!') or t.startswith('/!'):
                t = t.replace('!','').replace('\!','').replace('/!','')
                indat['tags_rel'].replace(np.nan, '', regex=True, inplace=True)
                indat = indat[indat['tags_rel'] != t ]
    
    # apply given filter. Recomendation: [FDR] < 0.05 & [n_rel] > 10 & [n_rel] < 100
    if args.filters and not args.filters.isspace():
        ok_flt,indat = common.filter_dataframe(indat, args.filters)
        if not ok_flt:
            sms = "The filter has not been applied"
            logging.error(sms)
            sys.exit(sms)

    
    # - Remove all the information (including all the headings) except for the names of the relevant categories.
    # - Remove duplicates
    indat = indat['idinf']
    indat = indat.drop_duplicates()

    logging.info("print output file without header")
    if indat.empty:
        sms = "ERROR!! The result is empty"
        sys.exit(sms)
    indat.to_csv(args.outfile, sep="\t", index=False, header=False)



if __name__ == "__main__":
    # parse arguments
    parser = argparse.ArgumentParser(
        description='Create a file with the list of files by experiment',
        epilog='''Examples:
        python  src/SanXoT/createSansonHighLevel.py
          -ii w1/c2a_outStats.tsv;wt2/c2a_outStats.tsv
          -o c2a_levels.tsv
        ''',
        formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('-w',  '--n_workers', type=int, default=2, help='Number of threads/n_workers (default: %(default)s)')
    parser.add_argument('-ii',  '--infiles',  required=True, help='Multiple outStats files separated by comma')
    parser.add_argument('-rr',  '--refiles',  required=True, help='Multiple Relationship file separated by comma')
    parser.add_argument('-o',   '--outfile',  required=True, help='Output file with the relationship table')
    parser.add_argument('-t',   '--tags',     help='Multiple Relationship file separated by comma')
    parser.add_argument('-f',   '--filters',  help='Boolean expression for the filtering of report')
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
