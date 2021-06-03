#!/usr/bin/python

# Module metadata variables
__author__ = ["Jose Rodriguez"]
__credits__ = ["Jose Rodriguez", "Jesus Vazquez"]
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


#########################
# Import local packages #
#########################
sys.path.append(f"{os.path.dirname(__file__)}/libs")
import common


###################
# Local functions #
###################

def read_infiles(df):
    # get the keyinput from the input tuple df=(keyinput,df)
    keyin = df[0]
    df = df[1]
    # read the list of infiles
    dfs = [pd.read_csv(file, sep="\t", comment='#', na_values=['NA'], low_memory=False) for file in list(df['infile']) ]
    ddf = pd.concat(dfs)
    return keyin,ddf

def print_by_keyinput(df, outdir):
    '''
    Print the output file by keyin
    '''
    # get the keyinput from the input tuple df=(keyinput,df)
    keyin = df[0]
    df = df[1]
    # get output file
    ofile = os.path.join(outdir, keyin)
    # create workspace
    fpath = os.path.dirname(ofile)
    if not os.path.exists(fpath):
        os.makedirs(fpath, exist_ok=False)
    # remove obsolete file
    ofile = f"{ofile}.tmp"
    if os.path.isfile(ofile):
        os.remove(ofile)
    # print
    df.to_csv(ofile, index=False, sep="\t", line_terminator='\n')
    return ofile


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
    if not 'COPY_INPUTS' in indata:
        sms = "There is not 'COPY_INPUTS' task-table"
        logging.error(sms)
        sys.exit(sms)
    else:    
        indata = indata['COPY_INPUTS']

    logging.info("add the full path into infile column")
    infiles = [common.get_path_file(i, args.indir) for i in list(indata['infile']) if not pd.isna(i)] # if apply, append input directory to file list
    logging.debug(infiles)
    if not all(infiles):
        sms = "At least, one of input files is wrong"
        logging.error(sms)
        sys.exit(sms)
    indata['infile'] = infiles


    logging.info("read the input file")
    with concurrent.futures.ProcessPoolExecutor(max_workers=args.n_workers) as executor:            
        ddf = executor.map( read_infiles, list(indata.groupby('keyinput')) )
    ddf = list(ddf)
    # ddf = read_infiles( list(indata.groupby('keyinput'))[0])
    
    
    logging.info("print the input files based on keyinput")
    with concurrent.futures.ProcessPoolExecutor(max_workers=args.n_workers) as executor:        
        tmpfiles = executor.map( print_by_keyinput, ddf, itertools.repeat(args.outdir))
    # tmpfiles = print_by_keyinput( ddf[0], args.outdir)
    [common.print_outfile(f) for f in list(tmpfiles)] # rename tmp file deleting before the original file 
    



if __name__ == '__main__':    
    # parse arguments
    parser = argparse.ArgumentParser(
        description='Copy a file into project results based on the key file',
        epilog='''
        Example:
            python copyFiles.py

        ''')
    parser.add_argument('-w',  '--n_workers', type=int, default=2, help='Number of threads/n_workers (default: %(default)s)')
    parser.add_argument('-i',  '--indir', required=True, help='Input Directory')
    parser.add_argument('-t',  '--intbl', required=True, help='File with the input data: filename, experiments')
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
