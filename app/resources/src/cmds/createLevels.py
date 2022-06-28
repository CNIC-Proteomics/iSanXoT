#!/usr/bin/python

# Module metadata variables
__author__ = "Jose Rodriguez"
__credits__ = ["Jose Rodriguez", "Jesus Vazquez"]
__license__ = "Creative Commons Attribution-NonCommercial-NoDerivs 4.0 Unported License https://creativecommons.org/licenses/by-nc-nd/4.0/"
__version__ = "0.0.1"
__maintainer__ = "Jose Rodriguez"
__email__ = "jmrodriguezc@cnic.es"
__status__ = "Development"

# import global modules
import os
import sys
import argparse
from argparse import RawTextHelpFormatter
import logging
import pandas as pd
import numpy as np
import re
import concurrent.futures
import itertools


#########################
# Import local packages #
#########################
sys.path.append(f"{os.path.dirname(__file__)}/../libs")
import common

###################
# Local functions #
###################

def check_cols_exist(df, ttable):
    def _check_cols_exist(df, tags):
        '''
        check if the given parameters are available in the input file
        '''
        # get unique values from the serie of tags
        tags = tags.unique().tolist()
        # split by comma if there are multiple tags
        tags = [re.split('\s*,\s*', t) for t in tags if t != '']
        # flat the list of list with unique values
        # tags = [t for ta in tags for t in ta]
        tags = list(set(itertools.chain(*tags)))
        # check if all values are in the columns of input file. Otherwise, error message
        if not all([True if c in df.columns else False for c in tags]):
            c = [c for c in tags if c not in df.columns]
            sms = f"The following values does not exist in your input file: {','.join(c)}"
            logging.error(sms)
            sys.exit(sms)

    # columns with the tags
    cols = ['feat_col','ratio_numerator','ratio_denominator']
    # removes whitespaces before/after comma
    ttable[cols] = ttable[cols].apply(lambda x: x.str.strip().str.replace('\s*,\s*', ',', regex=True) )
    # check if tags are available
    ttable[cols].apply(lambda x: _check_cols_exist(df, x))
    # return ttable    
    return ttable

def preparing_data(df, ttable):
    '''
    Preparing the ttable and input file

    Parameters
    ----------
    df : TYPE
        DESCRIPTION.
    ttable : TYPE
        DESCRIPTION.

    Returns
    -------
    out : list
        Create a list with the tuples:
            output (sample name)
            exp (experiment)
            feat (name of header)
            label (ratio numerator)
            controlTag (ratio denominator)
            df[exp,feat,label,controlTags]
    '''
    # declare output
    out = []
    # create a list with samples and parameter table
    ttable_samples = list(ttable.groupby('output'))
    # craete list of params
    for tt_sample in ttable_samples:
        # get parameters from ttable
        sample = tt_sample[0]
        ttable = tt_sample[1]
        exp = ttable['experiment'].values[0] if 'experiment' in ttable.columns else None
        feat = ttable['feat_col'].values[0] 
        # If level is not in the task-table (WSPP_SBT modules), then 'uscan' is by default.
        level = ttable['level'].values[0] if 'level' in ttable else 'uscan'
        label = ttable['ratio_numerator'].values[0]
        label = re.split('\s*,\s*', label.strip())
        controlTag = ttable['ratio_denominator'].values[0]
        controlTag = re.split('\s*,\s*', controlTag.strip())
        flagVab = False
        # get the unique values for tags
        params = [ re.split('\s*,\s*', p.strip()) for p in label+controlTag ]
        # flat the list of list with unique values
        params = list(set(itertools.chain.from_iterable(params)))
        # extract the columns from input file
        cols = ['Experiment']+[feat]+params if 'Experiment' in df.columns else [feat]+params
        indata = df[cols]
        out.append((
            sample,
            exp,
            feat,
            level,
            label,
            controlTag,
            flagVab,
            indata
            ))
    return out


def calculate_ratio(sample_ttable):
    '''
    Calculate ratios: Xs, Vs
    '''
    # get parameters from ttable
    sample = sample_ttable[0]
    exp = sample_ttable[1]
    feat = sample_ttable[2]
    level = sample_ttable[3]
    label = sample_ttable[4]
    controlTag = sample_ttable[5]
    flagVab = sample_ttable[6]
    df = sample_ttable[7]
    # filter by experiment
    if exp is not None:
        df = df[df['Experiment']==exp] if 'Experiment' in df.columns else df
    # declare tmp df
    tmpout = pd.DataFrame()
    # if apply, calculate the mean for the numerator tags (list)
    if len(label) > 1:
        lb = "-".join(label)+"_Mean"
        tmpout[lb] = df[label].mean(axis=1)
    else:
        lb = label
        tmpout[lb] = df[label]
    # calculate the mean for the control tags (denominator)
    ct = "-".join(controlTag)+"_Mean"
    tmpout[ct] = df[controlTag].mean(axis=1)
    # calculate the Xs
    Xs = tmpout[lb].divide(tmpout[ct], axis=0).applymap(np.log2)
    Xs_header = f"Xs_{Xs.columns.values[0]}_vs_{ct}"
    Xs.columns.values[0] = 'Xs'
    # calculate the Vs
    Vs = tmpout[lb].gt(tmpout[ct], axis=0)
    Vs = Vs.mask(Vs==False, tmpout[ct], axis=0).mask(Vs==True, tmpout[lb], axis=0)
    Vs = (Vs*Xs.notna().values).replace(0,"")
    Vs_header = f"Vs_{Vs.columns.values[0]}_vs_{ct}"
    Vs.columns.values[0] = 'Vs'
    #calculate the absolute values for all
    if flagVab:
        Vab = tmpout[lb]
        Vab = Vab.add_prefix("Vs_").add_suffix("_ABS")
        Vs = Vab
    # extract values
    out = pd.concat([df[feat],Xs,Vs], axis=1)
    # remove row with any empty columns
    out.replace('', np.nan, inplace=True)
    out.dropna(inplace=True)
    # add the sample name
    out['sample'] = sample
    # add the level name
    out['level'] = level
    # add the Xs and Vs headers
    out['Xs_header'] = Xs_header
    out['Vs_header'] = Vs_header
    return out

def print_per_sample(df, outdir):
    '''
    Print the ratios Xs,Vs per sample
    '''
    # get the sample and level name and input data df=((sample,level),df)
    (sample,level,xs_header,vs_header) = df[0]
    df = df[1]
    # get the 3 first columns
    df = df.iloc[:,:3]
    # rename Xs and Vs columns
    df.rename(columns={'Xs':xs_header, 'Vs':vs_header}, inplace=True)
    # create workspace
    outdir_e = os.path.join(outdir, sample)
    if not os.path.exists(outdir_e):
        os.makedirs(outdir_e, exist_ok=False)
    # remove obsolete file
    ofile = f"{outdir_e}/{level}.tsv.tmp"
    if os.path.isfile(ofile):
        os.remove(ofile)
    # print
    df.to_csv(ofile, index=False, sep="\t", line_terminator='\n')
    # rename the temporal files deleting the last suffix
    common.rename_tmpfile(ofile)


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

    logging.info("read input file")
    df = pd.read_csv(args.infile, sep="\t", low_memory=False)
    
    logging.info("check if the given parameters are available in the input file")
    ttable = check_cols_exist(df, ttable)

    logging.info("preparing the ttable and input file")
    indata_samples = preparing_data(df, ttable)

    logging.info("calculate the log2-ratios")
    with concurrent.futures.ProcessPoolExecutor(max_workers=args.n_workers) as executor:    
        ddf = executor.map(calculate_ratio, indata_samples )
    ddf = pd.concat(ddf)
    # begin: for debugging in Spyder
    # ddf = calculate_ratio(indata_samples[0])
    # end: for debugging in Spyder
    
    logging.info('print ratios per sample output')
    with concurrent.futures.ProcessPoolExecutor(max_workers=args.n_workers) as executor:        
        executor.map( print_per_sample,
                                list(ddf.groupby(['sample','level','Xs_header','Vs_header'])),
                                itertools.repeat(args.outdir) )
    # begin: for debugging in Spyder
    # print_per_sample(list(ddf.groupby(['sample','level','Xs_header','Vs_header']))[0], args.outdir)
    # end: for debugging in Spyder




if __name__ == "__main__":
    # parse arguments
    parser = argparse.ArgumentParser(
        description='Calculate the ratios',
        epilog='''
        Example:
            python createLevels.py
        ''', formatter_class=RawTextHelpFormatter)
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