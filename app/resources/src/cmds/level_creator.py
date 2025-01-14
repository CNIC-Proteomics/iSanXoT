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


###################
# Local functions #
###################

def chech_tags_available(df, rnum, rden):
    '''
    check if all tags are available in the input table
    '''
    # removes whitespaces before/after comma. discard empty values
    rnum = re.split('\s*,\s*', rnum.strip())
    rden = re.split('\s*,\s*', rden.strip())
    rnum = [r for r in rnum if r != '']
    rden = [r for r in rden if r != '']
    if not all([True if c in df.columns else False for c in rnum+rden]):
        c = [c for c in rnum+rden if c not in df.columns]
        sms = f"The tags are not available in your data: {','.join(c)}"
        logging.error(sms)
        sys.exit(sms)
    return rnum,rden

def filter_by_exp_from_ratios(idf, expt, feat, rnum, rden):
    '''
    Filter by batch and the given columns.
    '''
    # filter the input dataframe by the experiments
    idf = idf[idf['Batch']==expt]
    # extract the columns
    cols = set([feat] + rnum + rden)
    idf = idf[cols]
    return idf


def calculate_ratio(df, feat, label, controlTag, flagVab=False):
    '''
    Calculate ratios: Xs, Vs
    '''
    # if apply, calculate the mean for the numerator tags (list)
    if len(label) > 1:
        lb = "-".join(label)+"_Mean"
        df[lb] = df[label].mean(axis=1)
    # calculate the mean for the control tags (denominator)
    ct = "-".join(controlTag)+"_Mean"
    df[ct] = df[controlTag].mean(axis=1)
    # calculate the Xs
    Xs = df[label].divide(df[ct], axis=0).applymap(np.log2)
    Xs = Xs.add_prefix("Xs_").add_suffix("_vs_"+ct)
    # calculate the Vs
    Vs = df[label].gt(df[ct], axis=0)
    Vs = Vs.mask(Vs==False,df[ct], axis=0).mask(Vs==True, df[label], axis=0)
    Vs = (Vs*Xs.notna().values).replace(0,"")
    Vs = Vs.add_prefix("Vs_").add_suffix("_vs_"+ct)
    #calculate the absolute values for all
    if flagVab:
        Vab = df[label]
        Vab = Vab.add_prefix("Vs_").add_suffix("_ABS")
        Vs = Vab
    # extract values
    df = pd.concat([df[feat],Xs,Vs], axis=1)
    # remove row with any empty columns
    df.replace('', np.nan, inplace=True)
    df.dropna(inplace=True)
    return df



def main(args):
    '''
    Main function
    '''
    logging.info("read input file")
    df = pd.read_csv(args.infile, sep="\t", low_memory=False)
    
    logging.info("check if all tags are available in the input table")
    rnum,rden = chech_tags_available(df, args.rnum, args.rden)

    logging.info("filter by given parameters")
    df = filter_by_exp_from_ratios(df, args.exp, args.feat, rnum, rden)

    logging.info("calculate the log2-ratios")
    df = calculate_ratio(df, args.feat, rnum, rden)
    
    logging.info('print output')
    # print to tmp file
    f = f"{args.outfile}.tmp"
    df.to_csv(f, sep="\t", index=False)
    # rename tmp file
    os.rename(f, os.path.splitext(f)[0])




if __name__ == "__main__":
    # parse arguments
    parser = argparse.ArgumentParser(
        description='Calculate the ratios',
        epilog='''
        Example:
            python ratios.py
        ''', formatter_class=RawTextHelpFormatter)
    parser.add_argument('-i',  '--infile', required=True, help='Input file with Identification')
    parser.add_argument('-e',  '--exp', required=True, help='Filter given table by batch')
    parser.add_argument('-f',  '--feat', required=True, help='Column that identify the feature')
    parser.add_argument('-n',  '--rnum', required=True, help='Numerator to calculate the log2-ratios')
    parser.add_argument('-d',  '--rden', required=True, help='Denominator to calculate the log2-ratios')
    parser.add_argument('-o',  '--outfile', help='Output file with the ratios')
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