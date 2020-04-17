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
import re
from functools import reduce



####################
# Global variables #
####################
LEVELS_ORDER = ['s2p','p2a','p2q','q2a','q2c','c2a']
LEVELS_NAMES = {
    's': 'scan',
    'p': 'peptide',
    'q': 'protein',
    'c': 'category'
}
INFILE_SUFFIX = 'outStats.tsv'

COL_VALUES  = ['idinf', 'idsup', 'name']
COL_VALUES += ['n', 'Z', 'FDR']
# COL_VALUES += ['tags', 'Xsup', 'Vsup', 'Xinf', 'Vinf']

ROOT_FOLDER = '/names/'



###################
# Local functions #
###################
def read_infiles(file):
    # read file
    df = pd.read_csv(file, sep="\t", dtype=str, na_values=['NA'], low_memory=False)
    # get the name of 'experiment' until the root folder
    # By default, we get the last folder name of path
    fpath = os.path.dirname(file)
    name = os.path.basename(fpath)
    # split until the root folder
    if ROOT_FOLDER in fpath:
        s = fpath.split(ROOT_FOLDER)
        if len(s) > 1:
            s = s[1]
            name = re.sub(r'[/|\\]+', '_', s) # replace
    df['name'] = name
    return df
    
#################
# Main function #
#################
def main(args):
    '''
    Main function
    '''
    
    # Important note! We are not using the given input files.
    # We are going to take the folders and then, obtain the files from the calculated prefixes
    logging.info("get the list of folder from the given files")
    folders = []
    for files in args.inffiles.split(";"):
        folders += [os.path.dirname(f) for f in glob.glob(files, recursive=True)]
    for files in args.supfiles.split(";"):
        folders += [os.path.dirname(f) for f in glob.glob(files, recursive=True)]
    folders = list(set(folders))
    logging.debug(folders)


    logging.info("get the elements between the given inferior level and superior level")
    i = LEVELS_ORDER.index(args.inf_level)
    s = LEVELS_ORDER.index(args.sup_level)
    prefixes = LEVELS_ORDER[i:s+1]
    if not prefixes:
        sys.exit(f"ERROR!! The given levels are not consecutives. InfLevel:{args.inf_level} SupLevel:{args.sup_level}")
    logging.debug(prefixes)


    logging.info("create a dictionary using the calculated prefixes and the all given folders")
    dictfiles = defaultdict(list)
    for prefix in prefixes:
        listfiles = []
        for folder in folders:
            file = os.path.join(folder, f"{prefix}_{INFILE_SUFFIX}")
            listfiles += [f for f in glob.glob(file, recursive=True)]
        if not listfiles:
            sys.exit(f"ERROR!! There are not files for the level:{prefix}")
        dictfiles[prefix] = listfiles
    logging.debug(dictfiles)


    logging.info("compile the level files...")
    listdf = []
    for prefix,ifiles in dictfiles.items():
        # get the characters of inferior and superior level
        (prefix_i,prefix_s) = re.findall(r'^(\w+)2(\w+)', prefix)[0]
        
        logging.info(f"  {prefix}: read and concat files")
        l = []
        for ifile in ifiles:
            l.append( read_infiles(ifile) )
        df = pd.concat(l)

        logging.info(f"  {prefix}: remove columns excepts: ["+','.join(COL_VALUES)+"]")
        df.drop(df.columns.difference(COL_VALUES), 1, inplace=True)
        
        logging.info(f"  {prefix}: print dataframe")
        outdir = os.path.dirname(args.outfile)
        outfile = os.path.join(outdir, f"{prefix}_{INFILE_SUFFIX}")
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
    df.rename(columns=LEVELS_NAMES, inplace=True)
    

    logging.info("revome 'all' column")
    if 'a' in df.columns:
        df.drop(columns=['a'], axis=1, inplace=True)
    

    logging.info("reorder columns")
    # get a list of columns
    cols = list(df)
    # move the column to head of list using index, pop and insert
    for l in reversed( ['name']+list(LEVELS_NAMES.values()) ):
        if l in cols:
            cols.insert(0, cols.pop(cols.index(l)))
    df = df.reindex(columns=cols)
    

    logging.info("pivot table")
    # get the current columns that from the LEVELS
    cols_idx = list( set( list(LEVELS_NAMES.values()) )    &   set( list(df) ) )
    df = pd.pivot_table(df, index=cols_idx, columns=['name'], aggfunc='first', fill_value='NaN')
    df.reset_index(inplace=True)

    
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
    parser.add_argument('-i',   '--inf_level', required=True, choices=['s2p','p2a','p2q','q2a','q2c','c2a'], help='Prefix of inferior level')
    parser.add_argument('-s',   '--sup_level', required=True, choices=['s2p','p2a','p2q','q2a','q2c','c2a'], help='Prefix of superior level')
    parser.add_argument('-ii',  '--inffiles',  required=True, help='Multiple input files separated by comma')
    parser.add_argument('-ss',  '--supfiles',  required=True, help='Multiple input files separated by comma')
    parser.add_argument('-o',   '--outfile',   required=True, help='Output file with the reports')
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
