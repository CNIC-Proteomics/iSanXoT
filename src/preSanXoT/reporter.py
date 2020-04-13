# -*- coding: utf-8 -*-
#!/usr/bin/python

# Module metadata variables
__author__ = ["Ricardo Magni", "Jose Rodriguez"]
__credits__ = ["Ricardo Magni", "Jose Rodriguez", "Jesus Vazquez"]
__license__ = "Creative Commons Attribution-NonCommercial-NoDerivs 4.0 Unported License https://creativecommons.org/licenses/by-nc-nd/4.0/"
__version__ = "0.0.1"
__maintainer__ = "Jose Rodriguez"
__email__ = "jmrodriguezc@cnic.es"
__status__ = "Development"

import os
import sys
import argparse
import logging
import glob
from collections import defaultdict
import pandas as pd
import concurrent.futures
import re
from functools import reduce



####################
# Global variables #
####################
LEVELS = {
    's': 'scan',
    'p': 'peptide',
    'q': 'protein',
    'c': 'category'
}


###################
# Local functions #
###################
def read_infiles(file):
    df = pd.read_csv(file, sep="\t", dtype=str, na_values=['NA'], low_memory=False)
    df['name'] = os.path.basename(os.path.dirname(file)) # get the last directory name
    return df
    
#################
# Main function #
#################
def main(args):
    '''
    Main function
    '''
    logging.info("increase the list of input files from the given list of files (inferior level and superior level)")
    listfiles = []
    for files in args.inffiles.split(";"):
        listfiles += [f for f in glob.glob(files, recursive=True)]
    for files in args.supfiles.split(";"):
        listfiles += [f for f in glob.glob(files, recursive=True)]
    logging.debug(listfiles)
    
    logging.info("create a dictionary with the filename as key both inferior level and superior level")
    dictfiles = defaultdict(list)
    for file in listfiles:
        # get filename and extension separately.
        (fname, ext) = os.path.splitext(os.path.basename(file))
        dictfiles[fname].append(file)
    logging.debug(dictfiles)
    
    logging.info("compile the level files...")
    listdf = []
    for level,ifiles in dictfiles.items():
        # get prefix of level
        prefix = re.findall(r'^([^\_]*)', level)[0]
        # get the characters of inferior and superior level
        (prefix_i,prefix_s) = re.findall(r'^(\w+)2(\w+)', prefix)[0]
        
        logging.info(f"  {prefix}: concat files")
        with concurrent.futures.ProcessPoolExecutor(max_workers=args.n_workers) as executor:            
            df = executor.map(read_infiles,ifiles)
        df = pd.concat(df)
        
        logging.info(f"  {prefix}: print dataframe")
        outdir = os.path.dirname(args.outfile)
        outfile = os.path.join(outdir, f"{level}.tsv")
        df.to_csv(outfile, sep="\t", index=False)
        
        logging.info(f"  {prefix}: add prefix to some columns")  
        keep_same = ['idinf', 'idsup', 'name']
        df.columns = ['{}{}'.format(c, '' if c in keep_same else f"_{prefix}") for c in df.columns]
        
        logging.info(f"  {prefix}: rename inf,sup columns")
        df.rename(columns={'idinf': prefix_i, 'idsup': prefix_s}, inplace=True)
                
        listdf.append(df)
        
    logging.info("merge levels")
    df = reduce(lambda x, y: pd.merge(x, y), listdf)
    
    logging.info("rename columns")
    df.rename(columns=LEVELS, inplace=True)
    
    logging.info("revome 'all' column")
    if 'a' in df.columns:
        df.drop(columns=['a'], axis=1, inplace=True)
    
    logging.info("reorder columns")
    # get a list of columns
    cols = list(df)    
    # move the column to head of list using index, pop and insert
    for l in reversed( ['name']+list(LEVELS.values()) ):
        if l in cols:
            cols.insert(0, cols.pop(cols.index(l)))
    df = df.reindex(columns=cols)
    
    logging.info(f"print output file")
    df.to_csv(args.outfile, sep="\t", index=False)





if __name__ == "__main__":
    # parse arguments
    parser = argparse.ArgumentParser(
        description='Program that retrieves the results of iSanXoT',
        epilog='''
        Example:
            python reporter.py
        ''')
    parser.add_argument('-w',   '--n_workers', type=int, default=2, help='Number of threads/n_workers (default: %(default)s)')
    parser.add_argument('-i',   '--inf_level', required=True, help='File name of inferior level')
    parser.add_argument('-s',   '--sup_level', required=True, help='File name of superior level')
    parser.add_argument('-ii',  '--inffiles',  required=True, help='Multiple input files separated by comma')
    parser.add_argument('-ss',  '--supfiles',  required=True, help='Multiple input files separated by comma')
    parser.add_argument('-o',   '--outfile',   required=True, help='Output file with the reports')
    # parser.add_argument('-o',   '--outdir',    required=True, help='Output folder where reports will be saved')
    parser.add_argument('-vv', dest='verbose', action='store_true', help="Increase output verbosity")
    args = parser.parse_args()

    # get the name of script
    script_name = os.path.splitext(os.path.basename(__file__))[0].upper()

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
