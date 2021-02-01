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
import pandas as pd
import re



####################
# Global variables #
####################
LEVELS_NAMES = {
    's': 'scan',
    'p': 'peptide',
    'q': 'protein',
    'c': 'category',
    'd': 'description'
}
INFILE_SUFFIX = 'outStats.tsv'

COL_IDS  = ['name']
COL_IDS_VARS = {
    'llvl': 'idinf',
    'hlvl': 'idsup',
}
COL_VARS = {
    'n':    'n',
    'tags': 'tags',
    'z':    'Z',
    'fdr':  'FDR',
    'xs':   'Xsup',
    'vs':   'Vsup',
    'xi':   'Xinf',
    'vi':   'Vinf'
}

ROOT_FOLDER = '/names/'



###################
# Local functions #
###################
def read_infiles(file):
    # read file
    # df = pd.read_csv(file, sep="\t", dtype=str, na_values=['NA', 'excluded'], low_memory=False)
    df = pd.read_csv(file, sep="\t", na_values=['NA', 'excluded'], low_memory=False)
    
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
    logging.info("compile the level files...")
    # get the characters of inferior and superior level
    (prefix_i,prefix_s) = re.findall(r'^(\w+)2(\w+)', prefix)[0]
    
    logging.info(f"{prefix}: read and concat files")
    l = []
    for ifile in ifiles:
        l.append( read_infiles(ifile) )
    df = pd.concat(l)

    logging.info(f"{prefix}: remove columns excepts: ["+','.join(col_values)+"]")
    df.drop(df.columns.difference(col_values), 1, inplace=True)
    
    # logging.info("mark the variables with the outliers")
    # for c in col_vars:
    #     df[c] = np.where((df['tags'].notna() & df['tags'].str.contains('out')), 'out_'+df[c], df[c])
    # df.drop(columns=['tags'], axis=1, inplace=True)
    
    logging.info(f"{prefix}: add prefix to all columns except some")  
    keep_same = ['idinf', 'idsup', 'name']
    df.columns = ['{}{}'.format(c, '' if c in keep_same else f"_{prefix}") for c in df.columns]
    
    logging.info(f"{prefix}: rename inf,sup columns")
    df.rename(columns={'idinf': prefix_i, 'idsup': prefix_s}, inplace=True)

    logging.info("revome 'all' column")
    if 'a' in df.columns:
        df.drop(columns=['a'], axis=1, inplace=True)
    
    logging.info("rename columns")
    df.rename(columns=LEVELS_NAMES, inplace=True)
    
    logging.info("pivot table")
    # get the current columns that from the LEVELS
    cols = list(df.columns.get_level_values(0))
    cols_idx = list( set(list(LEVELS_NAMES.values())) & set(cols) )
    df = pd.pivot_table(df, index=cols_idx, columns=['name'], aggfunc='first')
    # df = df.reset_index()
    
    return df.reset_index()

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
    logging.info("read intermediate file")
    # df2 = pd.read_csv(file, sep="\t", dtype=str, header=[0,1], na_values=['NA', 'excluded'], low_memory=False) # two header rows
    df2 = pd.read_csv(file, sep="\t", header=[0,1], na_values=['NA', 'excluded'], low_memory=False) # two header rows
    
    # rename multi-level header allowing the merge among dataframes
    logging.info("rename multi-level header allowing the merge among dataframes")
    df2.rename(columns=lambda x: re.sub('^Unnamed:.*','',x), inplace=True)
    
    # get the current columns that from the LEVELS
    logging.info("get the current columns that from the LEVELS")
    cols_2_l0 = list(df2.columns.get_level_values(0))
    cols_2_idx = list( set(list(LEVELS_NAMES.values())) & set(cols_2_l0) )

    # get the current columns that from the LEVELS
    cols = list(df.columns.get_level_values(0))
    cols_idx = list( set(list(LEVELS_NAMES.values())) & set(cols) )

    # merge with given intermediate report based on the intersection relationship from peptide/protein/category
    # Only if there is intersection between the relationship columns (peptide/protein/category)
    logging.info("get the relationships intersection for the merging")
    cols_12_idx = list(set(cols_idx) & set(cols_2_idx))
    if cols_12_idx:
        # merge with given intermediate report
        logging.info(f"merge with given intermediate report {cols_12_idx}")
        df3 = pd.merge(df2,df, on=cols_12_idx)
        
        # set row index with the columns (peptides,protein, or category) - level 0-
        logging.info("set row index with the columns (peptides,protein, or category) - level 0-")
        cols_3_l0 = list(df3.columns.get_level_values(0))
        cols_idx_3 = list( set(list(LEVELS_NAMES.values())) & set(cols_3_l0) )
        df3.set_index(cols_idx_3, inplace=True)
        
        # # for each column from the first dataframe (input file)
        # # we add NaN values in the cell where there is not relationship
        # # we take the prefix where the current level is selected.
        # #   protein  -> n_yy2q   
        # #   category -> n_yy2c
        # prefix_templ = list(set([c for c in cols_3_l0 if c.startswith('n_') and c.endswith(f"2{prefix_i}")]))
        # if prefix_templ:
        #     # get the columns from the first df. without the relationship columns (peptide/protein/category)
        #     cols = list(df.columns.get_level_values(0))
        #     cols_diff = list( set(cols) - set(list(LEVELS_NAMES.values())) )
        #     for c in cols_diff:
        #         df3[c] = np.where(pd.isna(df3[prefix_templ]), np.NaN, df3[c])
        
        # assign to final variable
        # df = df3.reset_index()
        return df3.reset_index()
        
def filter_dataframe(df, flt):
    '''
    Filter the dataframe

    Parameters
    ----------
    df : pandas dataframe
        Report.
        
    flt : str
        Boolean expression.

    Returns
    -------
    Filtered dataframe.

    '''
    # variable with the boolean operators
    comparisons = ['>=', '<=', '!=', '<>', '==', '>', '<']
    # logicals = ['\|', '&', '~']
    logicals = ['&'] # for the moment only works with AND
    rc = r'|'.join(comparisons)
    rl = r'|'.join(logicals)
    # variable with index
    idx = pd.Series([])
    
    # go throught the comparisons
    comps = re.split(rl,flt)
    for cmp_str in comps:
        try:
            # extract the variable/operator/values from the logical condition
            x = re.match(rf"\s*\(?\s*([^\s]*)\s([{rc}])\s*([^\s]*)\s*\)?\s*", cmp_str)
            if x:
                var = x.group(1)
                cmp = x.group(2)
                val = x.group(3)
            # filter the column names
            # remember the columns are multiindex. For example, ('n_protein2category, '126_vs_Mean')
            # This is the reason we have included \(' in the regex
            d = df.filter(regex=f"^\('{var}", axis=1)
        except Exception as exc:
            # not filter
            logging.error(f"It is not filtered. There was a problem getting the columns: {cmp_str}\n{exc}")
            df_new = df
            break
        try:
            # evaluate condition
            ix = pd.eval(f"(d {cmp} {val})").any(axis=1)
            # comparison between two index Series
            # all -> &
            # any -> |
            if not idx.empty:
                if not ix.empty:
                    idx = pd.eval("(idx & ix)")
            else:
                idx = ix
        except Exception as exc:
            # not filter
            logging.error(f"It is not filtered. There was a problem evaluating the condition: {cmp_str}\n{exc}")
            df_new = df
            break

    # extract the dataframe from the index
    try:        
        if not idx.empty:
            df_new = df[idx]
    except Exception as exc:
        # not filter
        logging.error(f"It is not filtered. There was a problem extracting the datafram from the index rows: {exc}")
        df_new = df

    return df_new

def add_relations(idf, file):
    # read relationship file
    # column name to lowercase
    # add level to the columns
    # df = pd.read_csv(file, sep="\t", dtype=str, na_values=['NA', 'excluded'], low_memory=False)
    df = pd.read_csv(file, sep="\t", na_values=['NA', 'excluded'], low_memory=False)
    
    df.columns = map(str.lower, df.columns)
    df.columns = pd.MultiIndex.from_product([df.columns, ['']])
    # check how many columns are available in the givn df
    # col_i = [c[0] for c in idf.columns]
    # col_r = df.columns.to_list()
    # ints = list(set(col_i) & set(col_r))
    col_i = [c for c in idf.columns]
    col_r = [c for c in df.columns]
    ints = [i for i in col_i for r in col_r if i == r]
    # only we apply the operation when there is only one value in the dataframe
    # to add the relationship
    if len(ints) == 1:
        r = ints[0]
        idf = pd.merge(idf, df, on=[r])
    return idf

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
    param_ids_vars = [COL_IDS_VARS[v.lower()] for v in re.split(r'\s*,\s*', args.vars.strip()) if v.lower() in COL_IDS_VARS]
    # if the user does not give the lower and high level, we include both
    param_ids_vars = list(COL_IDS_VARS.values()) if not param_ids_vars else param_ids_vars
    param_vars = [COL_VARS[v.lower()] for v in re.split(r'\s*,\s*', args.vars.strip()) if v.lower() in COL_VARS]
    param_values = COL_IDS + param_ids_vars + param_vars


    logging.info("create report from list of input files")
    df = create_report(listfiles, prefix, param_values)
    

    # if apply and there is a relationship, we add an intermediate report
    # check if given additional file exits
    if args.rep_file and os.path.isfile( os.path.join(os.path.dirname(args.outfile), args.rep_file) ):
        rep_file = os.path.join(os.path.dirname(args.outfile), args.rep_file)
        logging.info(f"add an intermediate report {rep_file}")
        df = merge_intermediate(rep_file, df)


    # if apply and there is a external relationship, we add an intermediate report
    # check if given additional file exits
    if args.ext_rep_file and os.path.isfile(args.ext_rep_file):
        rep_file = args.ext_rep_file
        logging.info(f"add an external intermediate report {rep_file}")
        df = merge_intermediate(rep_file, df)            

 
    # remove columns with the same value. In special for the columns with 1's
    logging.info("discard the columns with 1's")
    df = df[[col for col in df.columns if not df[col].nunique()==1]]
    
    
    if args.filter:
        logging.info(f"filter the report {args.filter}")
        df = filter_dataframe(df, args.filter)


    if args.rel_file:
        logging.info(f"add the relationship values {args.rel_file}")
        df = add_relations(df, args.rel_file)


    logging.info("reorder columns")
    # sort list of tuples by specific ordering
    cols = list(df.columns)
    cols_order = list(LEVELS_NAMES.values()) + list(COL_VARS.values())
    cols = [i for j in cols_order for i in filter(lambda k: k[0].startswith(j), cols)]
    # reindex columns with the new ordered list of tuples
    df = df.reindex(columns=cols)
    
    
    logging.info("print output file")
    df.to_csv(args.outfile, sep="\t", index=False)





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
    parser.add_argument('-v',   '--vars',          required=True, default='Z,FDR,N', help='List of reported variables separated by comma')
    parser.add_argument('-ir',  '--rep_file',      help='Add intermediate report file')
    parser.add_argument('-xr',  '--ext_rep_file',  help='Add intermediate report file with absolute path')
    parser.add_argument('-f',   '--filter',        help='Boolean expression for the filtering of report')
    parser.add_argument('-r',   '--rel_file',      help='Relationship file')
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
