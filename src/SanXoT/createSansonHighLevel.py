#!/usr/bin/python

# import global modules
import os
import sys
import argparse
import logging
import pandas as pd
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
    indat = pd.read_csv(file, sep="\t", dtype=str, na_values=['NA'], low_memory=False)
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
    # logging.info("read files")
    # with concurrent.futures.ProcessPoolExecutor(max_workers=args.n_workers) as executor:            
    #     indat = executor.map(read_infiles,args.infiles.split(";"))
    # indat = pd.concat(indat)
    indat = pd.read_csv(args.infiles, sep="\t", dtype=str, na_values=['NA'], low_memory=False)

    # - Remove all the information (including all the headings) except for the names of the relevant categories.
    # - Remove duplicates
    indat = indat['idinf']
    indat.drop_duplicates(inplace=True)

    logging.info(f"print output file without header")
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
    parser.add_argument('-ii',  '--infiles',  required=True, help='Multiple input files separated by comma')
    parser.add_argument('-o',   '--outfile', required=True, help='Output file with the relationship table')
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
