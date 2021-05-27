# -*- coding: utf-8 -*-
#!/usr/bin/python

# Module metadata variables
__author__ = ["Jose Rodriguez"]
__credits__ = ["Jose Rodriguez", "Jesus Vazquez"]
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
import pandas as pd
import numpy as np
import re



####################
# Global variables #
####################
INFILE_SUFFIX = 'outStats.tsv'
COL_EXP  = 'NAME'
COL_IDS_VARS = ['idinf','idsup']
COL_VARS = {
    'n':      'n',
    'tags':   'tags',
    'z':      'Z',
    'fdr':    'FDR',
    'xsup':   'Xsup',
    'vsup':   'Vsup',
    'xinf':   'Xinf',
    'vinf':   'Vinf'
}

ROOT_FOLDER = '/jobs/'

#########################
# Import local packages #
#########################
sys.path.append(f"{os.path.dirname(__file__)}/libs")
import common

###################
# Local functions #
###################
def read_infiles(file):
    # read file
    df = pd.read_csv(file, sep="\t", na_values=['NA', 'excluded'], low_memory=False)
    
    # # get the name of 'experiment' using the folder name
    # fpath = os.path.dirname(file)
    # name = os.path.basename(fpath)
    # df[COL_EXP] = name

    # get the name of 'experiment' until the root folder
    # By default, we get the last folder name of path
    fpath = os.path.dirname(file)
    name = os.path.basename(fpath)
    # split until the root folder
    if ROOT_FOLDER in fpath:
        s = fpath.split(ROOT_FOLDER)
        if len(s) > 1:
            s = s[1]
            name = re.sub(r'[/|\\]+', '/', s) # replace
    df[COL_EXP] = name

    return df

def create_report(ifiles, prefix, col_values):
    '''
    Create report from list of input files

    Parameters
    ----------
    listfiles : list
        List of the input files

    prefix : str
        Prefix of input files
        
    cal_values : list
        List of columns (parameters) we are going to report

    Returns
    -------
    Dataframe with the report.
    '''
    logging.debug("compile the level files...")
    # get the characters of inferior and superior level
    (prefix_i,prefix_s) = re.findall(r'^(\w+)2(\w+)', prefix)[0]
    
    logging.debug(f"{prefix}: read and concat files")
    l = []
    for ifile in ifiles:
        l.append( read_infiles(ifile) )
    df = pd.concat(l)

    logging.debug(f"{prefix}: remove columns excepts: ["+','.join(col_values)+"]")
    df.drop(df.columns.difference(col_values), 1, inplace=True)
    
    logging.debug(f"{prefix}: add prefix to all columns except some")  
    keep_same = COL_IDS_VARS + [COL_EXP]    
    df.columns = ['{}{}'.format(c, '' if c in keep_same else f"_{prefix}") for c in df.columns]
    
    logging.debug(f"{prefix}: rename inf,sup columns")
    df.rename(columns={'idinf': prefix_i, 'idsup': prefix_s}, inplace=True)

    logging.debug("pivot table")
    # get the columns that are LEVELS (from the prefixes)
    cols_idx = [prefix_i] + [prefix_s]
    df = pd.pivot_table(df, index=cols_idx, columns=[COL_EXP], aggfunc='first')
    df = df.reset_index()
    
    logging.debug("add  'LEVEL' label")
    cols_name = [(c[0],'LEVEL') if c[1] == '' else c for c in df.columns]
    df.columns = pd.MultiIndex.from_tuples(cols_name)

    logging.debug("discard the columns with 1's (all)")
    df = df[[col for col in df.columns if not df[col].nunique()==1]]

        
    return df

def merge_intermediate(file, df):
    '''
    Merge intermediate file and given dataframe
    
    Parameters
    ----------
    file : str
        Input file.
        
    df : dataframe
        Givcen dataframe.

    Returns
    -------
    Merged dataframe.

    '''
    logging.debug("read intermediate file")
    df2 = pd.read_csv(file, sep="\t", header=[0,1], na_values=['NA', 'excluded'], low_memory=False) # two header rows
    
    logging.debug("get the columns that are LEVELS from the current df")
    # get the columns that are LEVELS from the external report
    cols_2_idx = [ c[0] for c in df2.columns if c[1] == 'LEVEL' ]
    # get the columns that are LEVELS from the current df
    cols_1_idx = [ c[0] for c in df.columns if c[1] == 'LEVEL' ]

    logging.debug("get the relationships intersection for the merging")
    # merge with given intermediate report based on the intersection relationship from peptide/protein/category
    # Only if there is intersection between the relationship columns (peptide/protein/category)
    cols_12_idx = list(set(cols_1_idx) & set(cols_2_idx))
    if cols_12_idx:
        logging.debug(f"merge with given intermediate report {cols_12_idx}")
        # merge with given intermediate report.
        # outer: use union of keys from both frames, similar to a SQL full outer join; sort keys lexicographically.
        cols_12_idx = [(c,'LEVEL') for c in cols_12_idx]
        df3 = pd.merge(df2,df, on=cols_12_idx, how='outer')
        
        return df3
        
def add_relation(idf, file):
    
    # read relationship file
    df = pd.read_csv(file, sep="\t", na_values=['NA', 'excluded'], low_memory=False)
    
    # get the characters of inferior and superior level from the file name
    prefix = os.path.splitext(os.path.basename(file))[0].lower()
    (prefix_i,prefix_s) = re.findall(r'^(\w+)2(\w+)', prefix)[0]

    # Just in case, add the prefix in the filename into the first columns and add multiindex
    # Remember, it is reverse!!
    # df.columns.values[0] = prefix_s
    df.columns.values[1] = prefix_i
    # create multiindex for the merge.
    # add the 'LEVEL' label for the indicated column (prefix_i)
    df.columns = pd.MultiIndex.from_tuples([(c,'LEVEL') if c == prefix_i else (c,'REL') for c in df.columns])
    
    # check how many columns are available in the givn df
    ints = [i for i in idf.columns if i[0] == prefix_i]
    # only we apply the operation when there is only one value in the dataframe
    # to add the relationship
    if len(ints) == 1:
        r = ints[0]
        idf = pd.merge(idf, df, on=[r], how='outer')
    return idf

#################
# Main function #
#################
def main(args):
    '''
    Main function
    '''
    
    # HANDLE with the parameters ----
    
    # Important note! We are not using the given input files.
    # We are going to take the folders and then, obtain the files from the calculated prefixes
    logging.info("get the list of folder from the given files")
    folders = []
    for files in re.split(r'\s*;\s*', args.infiles.strip()):
        folders += [os.path.dirname(f) for f in glob.glob(files, recursive=True)]
    logging.debug(folders)


    logging.info("create a dictionary using the calculated prefixes and the all given folders")
    prefix = args.level
    listfiles = []
    for folder in folders:
        file = os.path.join(folder, f"{prefix}_{INFILE_SUFFIX}")
        listfiles += [f for f in glob.glob(file, recursive=True)]
    if not listfiles:
        sys.exit(f"ERROR!! There are not files for the level:{prefix}")    


    logging.info("extract the list of given variables")
    param_vars = [COL_VARS[v.lower()] for v in re.split(r'\s*,\s*', args.vars.strip()) if v.lower() in COL_VARS]
    param_values = [COL_EXP] + COL_IDS_VARS + param_vars


    # START with the work ----

    logging.info("create report from list of input files")
    df = create_report(listfiles, prefix, param_values)
    

    # if apply and there is a relationship, we add an intermediate report
    # check if given additional file exits
    if args.rep_file:
        if os.path.isfile(args.rep_file):
            rep_file = args.rep_file
        elif os.path.isfile( os.path.join(os.path.dirname(args.outfile), args.rep_file) ):
            rep_file = os.path.join(os.path.dirname(args.outfile), args.rep_file)
        if rep_file:
            logging.info(f"add an intermediate report {rep_file}")
            df = merge_intermediate(rep_file, df)

 
    if args.rel_files:
        logging.info(f"add the relationship values {args.rel_files}")
        for file in re.split(r'\s*;\s*', args.rel_files.strip()):
            if os.path.isfile(file):
                df = add_relation(df, file)


    if args.filter:
        logging.info(f"filter the report {args.filter}")
        df = common.filter_dataframe_multiindex(df, args.filter)


    # RETRIEVE AND SORT the columns ----
    
    logging.info("show the given cols, reorder and remove duplicates")
    # get the LEVEL columns
    # get the levels to show. By default, get all LEVEL columns
    if args.show_cols:
        show_cols = re.split(r'\s*,\s*', args.show_cols.strip())
        cols_level = [(c,'LEVEL') for c in show_cols]
    else:
        cols_level = [c for c in df.columns if c[1] == 'LEVEL']
    # sort the VARS columns from the given parameter
    cols_vars = sorted([c for c in df.columns if c[1] != 'LEVEL' and c[1] != 'REL'])
    # the rest of columns (REL)
    cols_rel = [c for c in df.columns if c[1] == 'REL']
    cols = cols_level + cols_vars + cols_rel
    df = df.reindex(columns=cols)
        
    # Exception: if all column with variables are 'n_'
    all_vars_withN = all([True if c[0].startswith('n_') else False for c in cols_vars])
    if all_vars_withN:
        # group by all 'n_' columns and aggregate the maximun
        df[cols_level] = df[cols_level].replace(np.nan, '') # because the index does not accept NaN
        df_n = df.groupby(cols_level)[cols_vars].agg('max')
        df_n = df_n.reset_index()
        # merge with the rest of columns dropping the old
        df = df_n.merge(df, on=cols_level, how='left', suffixes=('', '_old'))
        df.drop([ c for c in df.columns if c[0].endswith('_old')] ,axis=1, inplace=True)

    # Remove duplicates
    df.drop_duplicates(inplace=True)

    
    logging.info("print output file")
    # print to tmp file
    f = f"{args.outfile}.tmp"
    df.to_csv(f, sep="\t", index=False)
    # rename tmp file deleting before the original file 
    common.print_outfile(f)





if __name__ == "__main__":
    # parse arguments
    parser = argparse.ArgumentParser(
        description='Program that retrieves the results of iSanXoT',
        epilog='''
        Example:
            python reporter.py
        ''')
    parser.add_argument('-ii',  '--infiles',       required=True, help='Multiple input files separated by semicolon')
    parser.add_argument('-o',   '--outfile',       required=True, help='Output file with the reports')
    parser.add_argument('-l',   '--level',         required=True, help='Prefix of level. For example, peptide2protein, protein2category, protein2all, etc.')
    parser.add_argument('-v',   '--vars',          required=True, help='List of reported variables separated by comma')
    parser.add_argument('-rp',  '--rep_file',      help='Add intermediate report file')
    parser.add_argument('-rl',  '--rel_files',      help='Multiple relationship files separated by semicolon')
    parser.add_argument('-s',   '--show_cols',     help='Which columns do you want to show in the output')
    parser.add_argument('-f',   '--filter',        help='Boolean expression for the filtering of report')
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
