#!/usr/bin/python

# import global modules
import os
import sys
import argparse
import logging
import re
import pandas as pd
import numpy as np
import concurrent.futures
import itertools


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

def check_cols_exist(df, cols, ttable):
    '''
    Check if the given headers exist
    
    Parameters
    ----------
    df : dataframe
        Dataframe of Input file
    cols: list
        Lit with the Task-Table columns
    ttable : dataframe
        Task-table

    Returns
    -------
    None.
    
    '''
    # get the column values
    col_vals = [ ttable[c].values.tolist() for c in cols if c in ttable.columns ]
    # flat the list of list with unique values
    col_vals = sorted(list(set(itertools.chain(*col_vals))))
    # discard the values with []
    col_vals = [c for c in col_vals if '[' not in c and ']' not in c ]
    # remove 'nan' or empty values
    col_vals = [c for c in col_vals if '' != c and not pd.isna(c) and 'nan' not in c ]
    # check if all values are in the columns of input file. Otherwise, error message
    if not all([True if c in df.columns else False for c in col_vals]):
        c = [c for c in col_vals if c not in df.columns]
        sms = f"The {','.join(c)} values does not exist in the input file"
        logging.error(sms)
        sys.exit(sms)

def create_relationtables(rt_ttable, cols, df, outdir):
    '''
    Create the Relation Table files from the task-table
    
    Parameters
    ----------
    df : dataframe
        Dataframe of Input file
    ttable : dataframe
        Task-table

    Returns
    -------
    List of RT files.

    '''
    # declare variablers
    infile = rt_ttable[0]
    ttable = rt_ttable[1]
    output = ttable['output'].values[0]
    outdat = pd.DataFrame()
    # get the column values
    col_vals = [ ttable[c].values.tolist() for c in cols if c in ttable.columns ]
    # flat the list of list with unique values
    col_vals = [v for va in col_vals for v in va]
    # remove 'nan' or empty values
    col_vals = [c for c in col_vals if '' != c and not pd.isna(c) and 'nan' not in c ]
    # extract the columns
    for c in col_vals:
        if '[' in c and ']' in c:
            v = c.replace('[','').replace(']','')
            outdat[c] = v
        else:
            outdat[c] = df[c]
    # rename the columns headers based on the outfile
    (prefix_i,prefix_s) = re.findall(r'^([^2]+)2([^\.]+)', output)[0]
    outdat.rename(columns={outdat.columns[0]: prefix_i, outdat.columns[1]: prefix_s}, inplace=True)
    # change the order of columns
    cs = outdat.columns.to_list()
    cs = [cs[i] for i in [1,0,2] if (i < len(cs))]
    outdat = outdat[cs]
    # remove duplicates and remove row with any empty column
    outdat.drop_duplicates(inplace=True)
    # remove row with any empty columns
    outdat.replace('', np.nan, inplace=True)
    outdat.dropna(inplace=True)
    # print tmp output file
    outfile = os.path.join(outdir, f"{output}.tsv")
    ofile = common.print_tmpfile(outdat, outfile)
    # rename the temporal files deleting the last suffix
    common.rename_tmpfile(ofile)
    rts = [ outfile ]
    return rts
    


#################
# Main function #
#################
def main(args):
    '''
    Main function
    '''
    
    # read the file to string and split by command
    # create a list of tuples (command, dataframe with parameters)
    # dropping empty rows and empty columns
    # create a dictionary with the concatenation of dataframes for each command
    # {command} = concat.dataframes
    logging.info("read the parameter table")
    ttable = common.read_task_table(args.intbl)
    if ttable.empty:
        sms = "There is not task-table"
        logging.error(sms)
        sys.exit(sms)


    logging.info("prepare the task-table")
    # groupby the task-table on input files
    # list of tuple (input file, task-table df)
    # the list is sorted and the 'nan' file (for ID-q) it is at the end
    task_table = list(ttable.groupby('rels_infiles')) if 'rels_infiles' in ttable.columns else [('nan', ttable)]
    # add the id-q file (input file) for empty/nan input (by default)
    task_table = [ (args.infile, t[1]) if t[0] == 'nan' else t for t in task_table ]
    


    logging.info("extract the columns for the relationship table")
    for rt in task_table:
        # declare variablers
        infile = rt[0]
        ttable = rt[1]
        rts = []
        cols = ['inf_headers','sup_headers','thr_headers']
        
        logging.info(f"read input file: {infile}")
        df = pd.read_csv(infile, sep="\t", low_memory=False)
        
        logging.info("check input headers exist")
        # check if values of columns exist
        check_cols_exist(df, cols, ttable)
    
        # logging.info("preparing the ttable and input file")
        # rt_ttable = preparing_data(df, ttable)

    
        logging.info("create the relation tables")
        with concurrent.futures.ProcessPoolExecutor(max_workers=args.n_workers) as executor:    
            rts = executor.map(create_relationtables,
                                list(ttable.groupby('output')),
                                itertools.repeat(cols),
                                itertools.repeat(df),
                                itertools.repeat(args.outdir)
                            )
        # rts = pd.concat(rts)
        # begin: for debugging in Spyder
        # rts = create_relationtables(list(ttable.groupby('output'))[0], cols, df, args.outdir)
        # end: for debugging in Spyder




if __name__ == "__main__":
    
    # parse arguments
    parser = argparse.ArgumentParser(
        description='Create the relationship tables from task-table',
        epilog='''Examples:
        python  createRels.py
          -ii TMT1/ID-q.tsv;TMT2/ID-q.tsv
          -o rels_table.tsv
        ''',
        formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('-w',  '--n_workers', type=int, default=2, help='Number of threads/n_workers (default: %(default)s)')
    parser.add_argument('-i',  '--infile', required=True, help='Input file with Identification')
    parser.add_argument('-t',  '--intbl', required=True, help='Table with the input parameters')
    parser.add_argument('-o',  '--outdir',  required=True, help='Output directory')
    parser.add_argument('-x',  '--phantom_files',  help='Phantom output files needed for the handle of iSanXoT workflow (snakemake)')
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
