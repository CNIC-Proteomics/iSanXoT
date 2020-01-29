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
import io
import pandas as pd
import re
import concurrent.futures
import itertools

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
    for f in ifiles.split(";"):
        with open(f, "r") as file:
            idta += file.read()
    match = re.findall(r'\s*#([^\s]*)\s*([^#]*)', idta, re.I | re.M)
    idta = [(c,pd.read_csv(io.StringIO(l), sep='\t', dtype=str, skip_blank_lines=True).dropna(how="all").dropna(how="all", axis=1).astype('str')) for c,l in match]    
    for c, d in idta:
        if c in indata:
            indata[c] = pd.concat( [indata[c], d], sort=False)
        else:
            for c2 in c.split('&'):
                indata[c2] = d
    return indata

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
    Expt1=[".*[\W|\_]*("+i+")[\W|\_]*.*" for i in Expt]
    df["Experiment"] = df["Spectrum_File"].replace(dict(itertools.zip_longest(Expt1,[],fillvalue="\\1")), regex=True)
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
    indata = read_command_table(args.intbl)

    if 'CREATE_ID' in indata:
        logging.info("extract the list of files from the given experiments")
        infiles = indata['CREATE_ID']['infile'].unique()
        logging.debug(infiles)
        
        logging.info("extract the list of experiments")
        Expt    = indata['CREATE_ID']['experiment'].unique()
        logging.debug(Expt)
        
        logging.info("processing the input file from the PD")
        with concurrent.futures.ProcessPoolExecutor(max_workers=args.n_workers) as executor:            
            ddf = executor.map( processing_infiles_PD, infiles, itertools.repeat(Expt) )
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
