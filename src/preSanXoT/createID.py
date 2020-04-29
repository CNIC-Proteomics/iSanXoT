#!/usr/bin/python

# Module metadata variables
__author__ = ["Ricardo Magni", "Jose Rodriguez"]
__credits__ = ["Ricardo Magni", "Jose Rodriguez", "Jesus Vazquez"]
__license__ = "Creative Commons Attribution-NonCommercial-NoDerivs 4.0 Unported License https://creativecommons.org/licenses/by-nc-nd/4.0/"
__version__ = "1.0.1"
__maintainer__ = "Jose Rodriguez"
__email__ = "jmrodriguezc@cnic.es"
__status__ = "Development"

# import modules
import os
import sys
import argparse
import logging
import pandas as pd
import concurrent.futures
import itertools

import common

###################
# Local functions #
###################
def processing_infiles_PD(file, Expt):
    '''
    Pre-processing the data: assign target-decoy, correct monoisotopic mass, calculate cXCorr
    '''    
    # read input file
    df = pd.read_csv(file, sep="\t")
    # rename columns
    df.rename(columns={
        'MHplus in Da': 'MH+ [Da]',
        'Theo MHplus in Da': 'Theo. MH+ [Da]',
        'Delta M in ppm': 'DeltaM [ppm]',
        'Spectrum File': 'Spectrum_File',
        'First Scan': 'Scan'
    }, inplace=True)
    # delete suffix value    
    df["Spectrum_File"] = df["Spectrum_File"].replace('\.[^$]*$', '', regex=True)
    # delete suffix in the headers coming from PD 2.3
    col = list(df.columns.values)
    col[:] = [s.replace('Abundance: ', '') for s in col]
    df.columns = col
    # add Experiment column
    df["Experiment"] = Expt
    return df

def print_by_experiment(df, outdir):
    '''
    Calculate FDR and filter by cXCorr
    '''
    # get the experiment names from the input tuple df=(exp,df)
    # create workspace
    outdir_e = os.path.join(outdir, df[0])
    if not os.path.exists(outdir_e):
        os.makedirs(outdir_e, exist_ok=False)
    # print the experiment files
    df[1].to_csv(os.path.join(outdir_e, "ID.tsv"), sep="\t", index=False)


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
    indata = common.read_command_table(args.intbl)

    if 'CREATE_ID' in indata:
        logging.info("extract the list of files from the given experiments")
        infiles = list(indata['CREATE_ID']['infile'])
        logging.debug(infiles)
        
        logging.info("extract the list of experiments")
        Expt    = list(indata['CREATE_ID']['experiment'])
        logging.debug(Expt)
        
        logging.info("processing the input file from the PD")
        with concurrent.futures.ProcessPoolExecutor(max_workers=args.n_workers) as executor:            
            ddf = executor.map( processing_infiles_PD, infiles, Expt )
        ddf = pd.concat(ddf)
            
        logging.info("print the ID files by experiments")
        with concurrent.futures.ProcessPoolExecutor(max_workers=args.n_workers) as executor:        
            executor.map( print_by_experiment, list(ddf.groupby("Experiment")), itertools.repeat(args.outdir) )
    else:
        logging.error("there is not 'CREATE_ID' command")



if __name__ == '__main__':    
    # parse arguments
    parser = argparse.ArgumentParser(
        description='Create the structure of ID for iSanXoT',
        epilog='''
        Example:
            python createID.py

        ''')
    parser.add_argument('-w',  '--n_workers', type=int, default=2, help='Number of threads/n_workers (default: %(default)s)')
    parser.add_argument('-t',  '--intbl', required=True, help='File with the input data: file, experiments')
    parser.add_argument('-o',  '--outdir',  required=True, help='Output directory')
    parser.add_argument('-x',  '--phantom_files',  help='Phantom files needed for the iSanXoT workflow (snakemake)')
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
