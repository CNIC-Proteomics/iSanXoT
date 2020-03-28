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

def extract_column(idf, df, level):
    for s in level.split("-"):
        if df[level].isnull().all():
            df[level] = idf[s]
        else:
            df[level] = df[level] + "-" + idf[s]
    return df

def main(args):
    '''
    Main function
    '''        
    logging.info("read files")
    with concurrent.futures.ProcessPoolExecutor(max_workers=args.n_workers) as executor:            
        indat = executor.map(read_infiles,args.infiles.split(";"))
    indat = pd.concat(indat)
    
# TODO!!! CHECK IF EVERYTHING IS ALLRIGHT IN THE INPUT FILES
       
    logging.info("init output dataframe")
    outdat = pd.DataFrame({args.inf_header: [], args.sup_header: []} )

    logging.info("extract the inf level")
    outdat = extract_column(indat, outdat, args.inf_header)

    logging.info("extract the sup level")
    outdat = extract_column(indat, outdat, args.sup_header)

    if args.thr_header:
        logging.info("extract the third level")
        outdat = extract_column(indat, outdat, args.thr_header)

    logging.info("remove duplicates")
    outdat.drop_duplicates(inplace=True)

    logging.info("remove row with any empty columns")
    outdat.dropna(inplace=True)

    logging.info('print output')
    outdat.to_csv(args.outfile, sep="\t", index=False)






if __name__ == "__main__":
    # parse arguments
    parser = argparse.ArgumentParser(
        description='Create the relationship tables from several files',
        epilog='''Examples:
        python  src/preSanXoT/createRels.py
          -ii TMT1/ID-q.tsv;TMT2/ID-q.tsv
          -o rels_table.tsv
        ''',
        formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('-w',   '--n_workers', type=int, default=2, help='Number of threads/n_workers (default: %(default)s)')
    parser.add_argument('-ii',  '--infiles',  required=True, help='Multiple input files separated by comma')
    parser.add_argument('-i',   '--inf_header',  required=True, help='Column(s) for the inferior level')
    parser.add_argument('-j',   '--sup_header',  required=True, help='Column(s) for the superior level')
    parser.add_argument('-k',   '--thr_header',  help='Column(s) for the third level')    
    parser.add_argument('-o',  '--outfile', required=True, help='Output file with the relationship table')
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
