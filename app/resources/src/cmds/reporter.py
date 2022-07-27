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
SUFFIX_OUTSTATS   = 'outStats.tsv'
SUFFIX_LOWERNORMW = 'lowerNormW.tsv'
COL_EXP  = 'NAME'
COL_IDS_LEVEL = ['idinf','idsup']
COL_VARS = {
    'n':      'n',
    'tags':   'tags',
    'z':      'Z',
    'fdr':    'FDR',
    'xsup':   'Xsup',
    'vsup':   'Vsup',
    'xinf':   'Xinf',
    'vinf':   'Vinf',
    "x'inf":  "X'inf",
    "winf":   "Winf",
}
SORTED_EXP_COLS = []

#########################
# Import local packages #
#########################
sys.path.append(f"{os.path.dirname(__file__)}/../libs")
import common

###################
# Local functions #
###################
def get_all_statsfiles(prefix, folders, suffix):
    listfiles = []
    for folder in folders:
        file = os.path.join(folder, f"{prefix}_{suffix}")
        listfiles += [f for f in glob.glob(file, recursive=True)]
    if not listfiles:
        sys.exit(f"ERROR!! There are not files for the level:{prefix}")
    return listfiles

def read_infiles(file):
    # read file
    df = pd.read_csv(file, sep="\t", na_values=['NA', 'excluded'], low_memory=False)
    
    # drop rows when the Z-score and FDR is excluded or NaN
    df = df[(df['Z'].notna()) | (df['FDR'].notna())]
    
    # get the name of 'job' until the root folder
    df[COL_EXP] = common.get_job_name(file)

    return df

def create_statsDF(ifiles, prefix, col_levels, param_vars):
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
    logging.debug(f"{prefix}: read and concat files")
    l = []
    for ifile in ifiles:
        l.append( read_infiles(ifile) ) # also add column EXP
    df = pd.concat(l)

    # get only the columns with the lower+higher+Name_Exp+Reported_Vars
    col_values = COL_IDS_LEVEL + [COL_EXP] + param_vars
    logging.debug(f"{prefix}: remove columns excepts: ["+','.join(col_values)+"]")
    df.drop(df.columns.difference(col_values), 1, inplace=True)
    
    logging.debug(f"{prefix}: rename inf,sup columns")
    c = {'idinf': col_levels[0]}
    if len(col_levels) == 2: c['idsup'] = col_levels[1]
    df.rename(columns=c, inplace=True)

    logging.debug("replace NaN table")
    # important!! NaN values is important for the statistics
    # We have to do the replace; otherwise, with the ption dropnan=False in the pivot_table takes a lot of time
    df = df.replace(np.nan, '')

    # if there are not reported variables
    # report only the level columns
    if len(param_vars) == 0:
        
        logging.debug("get only the level columns")
        df = df[col_levels]

        logging.debug("remove duplicates")
        df.drop_duplicates(inplace=True)

        logging.debug("add 'LEVEL' label only for the level columns")
        cols_name = [(c,'LEVEL') for c in df.columns]
        df.columns = pd.MultiIndex.from_tuples(cols_name)
        
    # create the report for the reported variables
    else:
        
        logging.debug(f"{prefix}: add prefix to all columns except the level columns and the nema_exp column")
        keep_same = col_levels + [COL_EXP]
        df.columns = ['{}{}'.format(c, '' if c in keep_same else f"_{prefix}") for c in df.columns]
        
        logging.debug("get the given sorted columns")
        global SORTED_EXP_COLS
        SORTED_EXP_COLS = list(pd.unique(df['NAME']))
    
        logging.debug("pivot table")
        # get the columns that are LEVELS (from the prefixes)
        df = pd.pivot_table(df, index=col_levels, columns=[COL_EXP], aggfunc='first') # pivot
        df = df.reset_index()
        
        logging.debug("add  'LEVEL' label")
        cols_name = [(c[0],'LEVEL') if c[1] == '' else c for c in df.columns]
        df.columns = pd.MultiIndex.from_tuples(cols_name)
    
        logging.debug("discard the columns with 1's (all)")
        df = df[[col for col in df.columns if not (df[col].nunique()==1 and df[col].unique()[0]==1) ]]
    
    return df

    
def merge_dfs(df, df2):
    '''
    Merge dataframes
    
    Parameters
    ----------
    df : dataframe
        Given dataframe.
        
    df2 : dataframe
        Given dataframe.

    Returns
    -------
    Merged dataframe.

    '''
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
    else:
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
    
    logging.debug("merge dataframes")
    df = merge_dfs(df, df2)
    
    return df
    
def add_relation(idf, file, prefix):
    
    # read relationship file
    df = pd.read_csv(file, sep="\t", na_values=['NA', 'excluded'], low_memory=False)
    
    # get the lower and higher levels
    (prefix_i,prefix_s) = re.findall(r'^([^2]+)2([^\.]+)', prefix)[0]

    # check if lower_level is in the RT, or then check if higher_level is in the RT
    # then create multiindex for the merging with RT
    if prefix_i in df.columns:
        r = prefix_i
        df.columns = pd.MultiIndex.from_tuples([(c,'LEVEL') if c == r else (c,'REL') for c in df.columns])
        idf = pd.merge(idf, df, on=[(r,'LEVEL')], how='left')
    elif prefix_s in df.columns:
        r = prefix_s
        df.columns = pd.MultiIndex.from_tuples([(c,'LEVEL') if c == r else (c,'REL') for c in df.columns])
        idf = pd.merge(idf, df, on=[(r,'LEVEL')], how='left')
    return idf

#################
# Main function #
#################
def main(args):
    '''
    Main function
    '''
    
    # HANDLE with the parameters ----
    
    # get the characters of inferior and superior level
    prefix = args.level
    (prefix_i,prefix_s) = re.findall(r'^([^2]+)2([^\.]+)', prefix)[0]

    # Important note! We are not using the given input files.
    # We are going to take the folders and then, obtain the files from the calculated prefixes
    logging.info("get the list of folder from the given files")    
    folders = []
    for files in re.split(r'\s*;\s*', args.infiles.strip()):
        folders += [os.path.dirname(f) for f in glob.glob(files, recursive=True)]
    logging.debug(folders)


    logging.info("get all {prefix}_{SUFFIX_OUTSTATS} files")
    listfiles = get_all_statsfiles(prefix, folders, SUFFIX_OUTSTATS)


    logging.info("extract the list of given variables")
    param_vars = []
    if args.vars:
        param_vars = [COL_VARS[v.lower()] for v in re.split(r'\s*,\s*', args.vars.strip()) if v.lower() in COL_VARS]



    logging.info("create outStats df from list of input files")
    col_levels = [prefix_i] + [prefix_s] # provide the levels to extract
    df = create_statsDF(listfiles, prefix, col_levels, param_vars)


    
    # if apply, we add the lowerNormW values
    if "X'inf" in param_vars or "Winf" in param_vars:
        
        logging.info("get all {prefix}_{SUFFIX_LOWERNORMW} files")
        listfiles = get_all_statsfiles(prefix, folders, SUFFIX_LOWERNORMW)
        
        logging.info("create lowerNormW df from list of input files")
        col_levels = [prefix_i] # provide the levels to extract
        df2 = create_statsDF(listfiles, prefix, col_levels, param_vars)
        
        logging.debug("merge lowerNormW df and outStats df")
        df = merge_dfs(df, df2)


    
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
                df = add_relation(df, file, prefix)


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
    # sort VARS based on inputs. if var does not exist, then goes to the end of columns
    cols_vars = [c for c in df.columns if c[1] != 'LEVEL' and c[1] != 'REL']
    # try:
    #     s = {v: i for i, v in enumerate(SORTED_EXP_COLS)} # first!! map sorted columns to indexes
    #     cols_vars_sorted = sorted(cols_vars, key=lambda x: s[x[0]] if x[1] in s else float('inf'))
    # except:
    #     cols_vars_sorted = sorted(cols_vars)
    cols_vars_sorted = sorted(cols_vars)
    # the rest of columns (REL)
    cols_rel = [c for c in df.columns if c[1] == 'REL']
    # reindex based on the new order of columns
    cols = cols_level + cols_vars_sorted + cols_rel
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
    common.rename_tmpfile(f)





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
    parser.add_argument('-v',   '--vars',          help='List of reported variables separated by comma')
    parser.add_argument('-rp',  '--rep_file',      help='Add intermediate report file')
    parser.add_argument('-rl',  '--rel_files',     help='Multiple relationship files (external or not) separated by semicolon')
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
