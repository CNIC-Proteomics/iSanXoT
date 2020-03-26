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
import re
import io
import pandas as pd
import numpy as np
import concurrent.futures
from itertools import repeat


###################
# Local functions #
###################
def read_command_table(ifiles):
    '''
    read the multiple input files to string and split by command
    create a list of tuples (command, dataframe with parameters)
    dropping empty rows and empty columns
    create a dictionary with the concatenation of dataframes for each command
    {command} = concat.dataframes
    '''
    indata = dict()
    idta = ''
    # read the multiple input files to string and split by command
    for f in ifiles.split(";"):
        with open(f, "r") as file:
            idta += file.read()
    # create a list of tuples (command, dataframe with parameters)
    match = re.findall(r'\s*#([^\s]*)\s*([^#]*)', idta, re.I | re.M)
    idta = [(c,pd.read_csv(io.StringIO(l), sep='\t', dtype=str, skip_blank_lines=True).dropna(how="all").dropna(how="all", axis=1).astype('str')) for c,l in match]
    # create a dictionary with the concatenation of dataframes for each command
    for c, d in idta:
        # discard the rows when the first empty columns
        if not d.empty:
            l = list(d[d.iloc[:,0] == 'nan'].index)
            d = d.drop(l)
        if c in indata:
            indata[c] = pd.concat( [indata[c], d], sort=False)
        else:
            for c2 in c.split('-'):
                indata[c2] = d
    return indata

def filter_by_exp_from_ratios(idf, iratios):
    '''
    Filter the input dataframe from the given experiments.
    Get the list of ratios
    '''
    # get the matrix with the ratios
    ratios = iratios.groupby("ratio_denominator")["ratio_numerator"].unique()
    ratios = ratios.reset_index().values.tolist()
    # get the list of sorted experiments discarding empty values
    expt = list( filter(None, iratios["experiment"].unique()) )
    # filter the input dataframe by the experiments in the RATIOS table
    idf = idf[idf['Experiment'].isin(expt)]
    return idf, ratios


def _calc_ratio(df, ControlTag, label):
    '''
    Calculate ratios: Xs, Vs
    '''
    df = df[1]
    # calculate the mean for the control tags (denominator)
    ct = "-".join(ControlTag)+"_Mean" if len(ControlTag) > 1 else "-".join(ControlTag)
    df[ct] = df[ControlTag].mean(axis=1)
    # calculate the Xs
    Xs = df[label].divide(df[ct], axis=0).applymap(np.log2)
    Xs = Xs.add_prefix("Xs_").add_suffix("_vs_"+ct)
    # calculate the Vs
    Vs = df[label].gt(df[ct], axis=0)
    Vs = Vs.mask(Vs==False,df[ct], axis=0).mask(Vs==True, df[label], axis=0)
    Vs = (Vs*Xs.notna().values).replace(0,"")
    Vs = Vs.add_prefix("Vs_").add_suffix("_vs_"+ct)
    #calculate the absolute values for all
    Vab = df[label]
    Vab = Vab.add_prefix("Vs_").add_suffix("_ABS")
    # concatenate all ratios
    df = pd.concat([df,Xs,Vs,Vab], axis=1)
    return df    

def calculate_ratio(df, ratios):
    '''
    Calculate the ratios
    '''
    # get the type of ratios we have to do
    for rat in ratios:
        ControlTag = rat[0]
        label = rat[1]
        ControlTag = ControlTag.split(",")
        # create the numerator tags
        labels = []
        for lbl in label:
            # if apply, calculate the mean for the numerator tags (list)
            if ',' in lbl:
                lbl = lbl.split(",")
                lb = "-".join(lbl)+"_Mean" if len(lbl) > 1 else "-".join(lbl)
                df[lb] = df[lbl].mean(axis=1)
                labels.append( lb )
            else:
                labels.append( lbl )
        df = _calc_ratio(df, ControlTag, labels)
    return df


def main(args):
    '''
    Main function
    '''
    # read the file to string and split by command
    # create a list of tuples (command, dataframe with parameters)
    # dropping empty rows and empty columns
    # create a dictionary with the concatenation of dataframes for each command
    # {command} = concat.dataframes
    logging.info("read the input file with the commands")
    indata = read_command_table(args.intbl)

    logging.info("read input file")
    ddf = pd.read_csv(args.infile, sep="\t")

    logging.info("get the ratios and experiments from the data file")
    ddf, ratios = filter_by_exp_from_ratios(ddf, indata['RATIOS'])
    logging.debug(ratios)

    logging.info("calculate the ratios (in parallel by experiment)")
    with concurrent.futures.ProcessPoolExecutor(max_workers=args.n_workers) as executor:        
        ddf = executor.map(calculate_ratio, list(ddf.groupby("Experiment")), repeat(ratios))
    ddf = pd.concat(ddf)
    # ddf = calculate_ratio(list(ddf.groupby("Experiment")), ratios)
    
    logging.info('print output')
    ddf.to_csv(args.outfile, sep="\t", index=False)







if __name__ == "__main__":
    # parse arguments
    parser = argparse.ArgumentParser(
        description='Calculate the ratios',
        epilog='''
        Example:
            python ratios.py
        ''', formatter_class=RawTextHelpFormatter)
    parser.add_argument('-w',  '--n_workers', type=int, default=2, help='Number of threads/n_workers (default: %(default)s)')
    parser.add_argument('-i', '--infile', help='Input file with Identification: ID.tsv')
    parser.add_argument('-t',  '--intbl', required=True, help='File with the input data: file, experiments')
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