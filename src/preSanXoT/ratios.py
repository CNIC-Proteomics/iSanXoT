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
import glob
import shutil

import pandas
import numpy
import re
import dask
import dask.dataframe as dd
from dask.delayed import delayed
from dask.distributed import Client


###################
# Local functions #
###################

def pre_processing(file, expt=None):
    '''
    Pre-processing the data: join the files
    '''    
    # read input file if has teh experiment
    df = pandas.read_csv(file, sep="\t")
    if expt:
        df["Experiment"] = next((x for x in expt if x in file), False)
    return df

def infiles_ratios(ifile):
    '''
    Handles the input data (workflow file)
    '''
    # get the matrix with the ratios
    indata = pandas.read_csv(ifile, usecols=["experiment","ratio_numerator","ratio_denominator"], converters={"experiment":str, "ratio_numerator":str, "ratio_denominator":str})
    ratios = indata.groupby("ratio_denominator")["ratio_numerator"].unique()
    ratios = ratios.reset_index().values.tolist()
    # get the list of sorted experiments discarding empty values
    expt = list( filter(None, indata["experiment"].unique()) )
    expt.sort()
    return expt, ratios


def infiles_adv(self, ifile):
    '''
    Handles the input data (workflow file)
    '''
    indata = pandas.read_csv(ifile, converters={"experiment":str, "name":str, "ratio_numerator":str, "ratio_denominator":str})
    lblCtr = {}
    # get the list of sorted experiments discarding empty values
    Expt = list( filter(None, indata["experiment"].unique()) )
    Expt.sort()
    # for each row
    for idx, indat in indata.iterrows():
        exp    = indat["experiment"]
        ratio_num = indat["ratio_numerator"]
        ratio_den = indat["ratio_denominator"]
        # ratio numerator and denominator have to be defined
        if not pandas.isnull(exp) and not exp == "" and not pandas.isnull(ratio_num) and not ratio_num == "" and not pandas.isnull(ratio_den) and not ratio_den == "":
            ratio_num = re.sub(r'\n*', '', ratio_num)
            ratio_num = re.sub(r'\s*', '', ratio_num)
            ratio_den = re.sub(r'\n*', '', ratio_den)
            ratio_den = re.sub(r'\s*', '', ratio_den)
            # save for each experiment
            # the means apply to a list of unique tags (num)
            if exp not in lblCtr:
                lblCtr[exp] = {}
            if ratio_den not in lblCtr[exp]:
                lblCtr[exp][ratio_den] = []
            if ratio_num not in lblCtr[exp][ratio_den]:
                lblCtr[exp][ratio_den].append(ratio_num)
    return Expt, lblCtr


def _calc_ratio(df, ControlTag, label):
    '''
    Calculate ratios: Xs, Vs
    '''
    # calculate the mean for the control tags (denominator)
    ct = "-".join(ControlTag)+"_Mean" if len(ControlTag) > 1 else "-".join(ControlTag)
    df[ct] = df[ControlTag].mean(axis=1)
    # calculate the Xs
    Xs = df[label].divide(df[ct], axis=0).applymap(numpy.log2)
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
    df = pandas.concat([df,Xs,Vs,Vab], axis=1)
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
    logging.info("check parameters")
    if not args.infile and not args.indir:
        parser.print_help(sys.stderr)
        sys.exit("\n\nERROR: we need at least one kind of input: infile or indir\n")


    logging.info("get the ratios and experiments from the data file")
    expt, ratios = infiles_ratios(args.datfile)
    logging.debug(expt)
    logging.debug(ratios)


    if args.infile:
        logging.info("get indata from input file")
        logging.debug(args.infile)
        df = pandas.read_csv(args.infile, sep="\t")
        
        logging.info("calculate ratios")
        df = calculate_ratio(df, ratios)

        logging.info('print output file')
        outfile = os.path.dirname(os.path.realpath(args.infile)) + "/ID-q.tsv"
        df.to_csv(outfile, sep="\t", index=False)

    elif args.indir:
        logging.info("get indata from a list of files")
        infiles_aux = glob.glob( os.path.join(args.indir,"*/ID.tsv"), recursive=True )
        infiles = [ f for f in infiles_aux if any(x in os.path.splitext(f)[0] for x in expt) ]
        logging.debug(infiles)
        ddf = dd.from_delayed( [delayed(pre_processing)(file, expt) for file in infiles] )

        logging.info('create dask client')
        with Client(n_workers=args.n_workers) as client:
            logging.info('repartition by experiments')
            ddf = ddf.set_index('Experiment')
            Exptr = expt + [expt[-1]] # I don´t know why but we have to repeat the last experiment in the list for the repartition
            ddf = ddf.repartition(divisions=Exptr)
            
            logging.info("calculate ratios")
            ddf = ddf.map_partitions(calculate_ratio, ratios)
            
            logging.info('print output file')
            outfiles = []
            outdir = args.outdir if args.outdir else args.indir
            for e in expt:
                outdir_exp = outdir+"/"+e
                if not os.path.exists(outdir_exp):
                    os.makedirs(outdir_exp, exist_ok=False)
                outfiles.append(outdir_exp+"/ID-q.tsv")
            logging.debug(outfiles)
            ddf.to_csv(outfiles, sep="\t", line_terminator='\n')

            ddf.compute()

        logging.info("remove temporal directory")
        tmp_dir = "{}/{}".format(os.getcwd(), 'dask-worker-space')
        logging.debug(tmp_dir)
        shutil.rmtree(tmp_dir)




if __name__ == "__main__":
    # parse arguments
    parser = argparse.ArgumentParser(
        description='Calculate the ratios',
        epilog='''
        Example:
            python ratios.py
        ''', formatter_class=RawTextHelpFormatter)
    required = parser.add_argument_group('required arguments')
    conditional = parser.add_argument_group('conditional arguments')

    conditional.add_argument('-if', '--infile', help='Input file with Identification: ID.tsv')
    conditional.add_argument('-id', '--indir', help='Input directory where are saved the identification files: ID.tsv')

    required.add_argument('-d',  '--datfile', required=True, help='File with the input data: experiments, task-name, ratio (num/den),...')
    
    parser.add_argument('-o',  '--outdir', help='Output directory where the ID-q file will be saved')
    parser.add_argument('-w',  '--n_workers', type=int, default=2, help='Number of threads/n_workers (default: %(default)s)')
    parser.add_argument('-vv', dest='verbose', action='store_true', help="Increase output verbosity")

    args = parser.parse_args()

    # logging debug level. By default, info level
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG,
                            format='%(asctime)s - %(levelname)s - %(message)s',
                            datefmt='%m/%d/%Y %I:%M:%S %p')
    else:
        logging.basicConfig(level=logging.INFO,
                            format='%(asctime)s - %(levelname)s - %(message)s',
                            datefmt='%m/%d/%Y %I:%M:%S %p')

    # start main function
    logging.info('start script: '+"{0}".format(" ".join([x for x in sys.argv])))
    main(args)
    logging.info('end script')