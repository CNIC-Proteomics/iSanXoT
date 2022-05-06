#!/usr/bin/python

# Module metadata variables
__author__ = ["Ricardo Magni", "Jose Rodriguez"]
__credits__ = ["Ricardo Magni", "Jose Rodriguez", "Jesus Vazquez"]
__license__ = "Creative Commons Attribution-NonCommercial-NoDerivs 4.0 Unported License https://creativecommons.org/licenses/by-nc-nd/4.0/"
__version__ = "1.0.1"
__maintainer__ = "Jose Rodriguez"
__email__ = "jmrodriguezc@cnic.es"
__status__ = "Development"

# import global modules
import os
import sys
# import itertools
import argparse
import logging
import pandas as pd
import numpy as np
import concurrent.futures
from itertools import repeat

#########################
# Import local packages #
#########################
sys.path.append(f"{os.path.dirname(__file__)}/../libs")
import common
import PD
import MSFragger
import Comet

###################
# Local functions #
###################

def read_infile(file):
    '''
    Read file
    '''
    # read input file
    try:
        df = pd.read_csv(file, sep="\t")
    except Exception as exc:
        sms = "Reading input file: {}".format(exc)
        logging.error(sms)
        sys.exit(sms)
    return df


def preProcessing(df, se, deltaMassThreshold, tagDecoy, JumpsAreas):
    # processing the input files depending on
    if se == "PD": df = PD.preProcessing(df, deltaMassThreshold, tagDecoy, JumpsAreas)
    elif se == "Comet": df = Comet.preProcessing(df, deltaMassThreshold, tagDecoy, JumpsAreas)
    elif se == "MSFragger": df = MSFragger.preProcessing(df, deltaMassThreshold, tagDecoy, JumpsAreas)
    else: df = None
    return df

def FdrXc(df, typeXCorr, FDRlvl):
    '''
    Calculate FDR and filter by cXCorr
    '''
    # sort by the type of score
    df = df.sort_values(by=[typeXCorr,"T_D"], ascending=False)
    # rank the target and decoy individually
    df["rank"] = df.groupby("T_D").cumcount()+1
    df["rank_T"] = np.where(df["T_D"]==1, df["rank"], 0)
    df["rank_T"] = df["rank_T"].replace(to_replace=0, method='ffill')
    df["rank_D"] = np.where(df["T_D"]==0, df["rank"], 0)
    df["rank_D"] = df["rank_D"].replace(to_replace=0, method='ffill')
    # calcultate FDR: FDR = rank(D)/rank(T)
    df["FdrXc"] = df["rank_D"]/df["rank_T"]
    # filter by input FDR
    df = df[ df["FdrXc"] <= FDRlvl ]
    # discard decoy
    df = df[ df["T_D"] == 1 ]
    return df

def processing(df, indata, se):
    # get the dataframe from the input tuple df=(exp,df)
    # get the indata from the dataframe group by experiment
    exp_df = df[0]
    df = df[1]
    indata = indata[indata['experiment']==exp_df]
    if not indata.empty:
        # get params
        deltaMassThreshold = int(indata['threshold'].values[0])
        tagDecoy = str(indata['lab_decoy'].values[0])
        FDRlvl = float(indata['fdr'].values[0])
        typeXCorr = str(indata['type_xcorr'].values[0])
        JumpsAreas = int(indata['jump_areas'].values[0])
        # pre-processing the data: rename columns, assign target-decoy, correct monoisotopic mass
        df = preProcessing(df, se, deltaMassThreshold, tagDecoy, JumpsAreas)
        # calculate FDR and filter
        df = FdrXc(df, typeXCorr, FDRlvl)
    else:
        df = None
    return df

def calc_fdr(n_workers, ses, df, indata):
    '''
    Calculate the FDR
    '''    
    with concurrent.futures.ProcessPoolExecutor(max_workers=n_workers) as executor:        
        ddf = executor.map(processing, list(df.groupby("Experiment")), repeat(indata), repeat(ses))
    ddf = pd.concat(ddf)
    # begin: for debugging in Spyder
    # ddf = processing( list(df.groupby("Experiment"))[0], indata, ses)
    # end: for debugging in Spyder
    return ddf


def main(args):
    '''
    Main function
    '''
    # read the task-tables
    logging.info("reading the task-table")
    indata = common.read_task_table(args.intbl)
    if indata.empty:
        sms = "There is not task-table"
        logging.error(sms)
        sys.exit(sms)


    logging.info("reading in file depending on search engine")
    df = read_infile(args.infile)


    logging.info("selecting the search engine")
    se = common.select_search_engine(df)
    logging.debug(se)
    if not se:
        sms = "The search engines has not been recognized"
        logging.error(sms)
        sys.exit(sms)


    logging.info("calculating the FDR by experiment")
    ddf = calc_fdr(args.n_workers, se, df, indata)
        
    
    logging.info("printing the output")
    # print to tmp file
    f = f"{args.outfile}.tmp"
    ddf.to_csv(f, sep="\t", index=False)
    # rename tmp file deleting before the original file 
    common.rename_tmpfile(f)



if __name__ == '__main__':
    # parse arguments
    parser = argparse.ArgumentParser(
        description='Calculate the FDR',
        epilog='''
        Example:
            python fdr.py -i tests/pratio/Tissue_10ppm  -e "TMTHF" -l "DECOY_" -o tests/pratio/Tissue_10ppm

        ''')
    parser.add_argument('-w',  '--n_workers', type=int, default=2, help='Number of threads/n_workers (default: %(default)s)')
    parser.add_argument('-i',  '--infile', required=True, help='Input file: ID.tsv')
    parser.add_argument('-t',  '--intbl', required=True, help='File with the input data: experiments, threshold, score, etc')
    parser.add_argument('-o',  '--outfile',   required=True, help='Output file')
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