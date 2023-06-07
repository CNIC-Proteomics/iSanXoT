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


#########################
# Import local packages #
#########################
sys.path.append(f"{os.path.dirname(__file__)}/../libs")
import common
import PD
import MSFragger
import Comet
import Quant


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

def preprocessing_data(df, se):
    '''
    Processing the input files depending on search engine
    '''
    if se == "PD":
        df = PD.preprocessing_data(df)
    elif se == "Comet":
        df = Comet.preprocessing_data(df)
    elif se == "MSFragger":
        df = MSFragger.preprocessing_data(df)
    else:
        return df
    return df

def add_quantification(n_workers, indir, se, ddf, indata):
    '''
    Extract the quantification
    '''
    # pre-processing the df
    ddf = preprocessing_data(ddf, se)
    
    # check if spectrum_file, mzfile and quan_method columns are fillin. Otherwise, the program does nothing.
    c = indata.columns.tolist()
    if 'spectrum_file' in c and 'mzfile' in c and 'quan_method' in c and not all(indata['spectrum_file'].str.isspace()) and not all(indata['mzfile'].str.isspace()) and not all(indata['quan_method'].str.isspace()):
        
        
        # if apply, append input directory to file list
        indata['mzfile'] = [common.get_path_file(i, indir) for i in list(indata['mzfile']) if not pd.isna(i)]
        logging.debug(indata['mzfile'].values.tolist())

        logging.info("compare spectrum_file/mzfile from the input_data and param_data")
        # convert groupby 'Spectrum_File' to dict for the input_data and param_data        
        ie_spec = dict(tuple(ddf.groupby("Spectrum_File")))
        in_spec = dict(tuple(indata.groupby("spectrum_file")))
        # check if all spectrum_files from inpu_data have a pair with  mzml coming from param_data        
        ie_spec_keys = list(ie_spec.keys())
        in_spec_keys = list(in_spec.keys())
        a = [ x for x in ie_spec_keys if not x in in_spec_keys ]
        if len(a) == 0:
            # for the 'spec_file' of input_data, get the mzMl of param_data
            pair_spec_ie_in = [ (k,v,in_spec[k]) for k,v in ie_spec.items() if k in in_spec]
    
            logging.info("prepare the params for each spectrum_file/mzfile pair")
            # one experiment can be multiple spectrum files
            with concurrent.futures.ProcessPoolExecutor(max_workers=n_workers) as executor:            
                params = executor.map( Quant.prepare_params, pair_spec_ie_in )
            params = [i for s in list(params) for i in s]
            # begin: for debugging in Spyder
            # params = Quant.prepare_params(pair_spec_ie_in[0])
            # end: for debugging in Spyder
    
            logging.info("extract the quantification")
            with concurrent.futures.ProcessPoolExecutor(max_workers=n_workers) as executor:            
                quant = executor.map( Quant.extract_quantification, params )
            quant = pd.concat(quant)
            # begin: for debugging in Spyder
            # quant = Quant.extract_quantification(params[0])
            # end: for debugging in Spyder
    
    
            logging.info("merge the quantification")
            with concurrent.futures.ProcessPoolExecutor(max_workers=n_workers) as executor:            
                ddf = executor.map( Quant.merge_quantification,
                                        list(ddf.groupby("Spectrum_File")),
                                        list(quant.groupby("Spectrum_File")) )
            ddf = pd.concat(ddf)
            # begin: for debugging in Spyder
            # ddf = Quant.merge_quantification( list(ddf.groupby("Spectrum_File"))[0], list(quant.groupby("Spectrum_File"))[0] )
            # end: for debugging in Spyder
        else:
            logging.error(f"The following Spectrum_Files have not mzML files: {a}")
            return None

    return ddf
    
def print_by_experiment(df, outdir, outfname):
    '''
    Print the output file by experiments
    '''
    # get the experiment names from the input tuple df=(exp,df)
    exp = df[0]
    # create workspace
    outdir_e = os.path.join(outdir, exp)
    if not os.path.exists(outdir_e):
        os.makedirs(outdir_e, exist_ok=False)
    # remove obsolete file
    ofile = f"{outdir_e}/{outfname}.tmp"
    if os.path.isfile(ofile):
        os.remove(ofile)
    # print
    df[1].to_csv(ofile, index=False, sep="\t", line_terminator='\n')
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
    indata = common.read_task_table(args.intbl)
    if indata.empty:
        sms = "There is not task-table"
        logging.error(sms)
        sys.exit(sms)


    logging.info("reading the idq file")
    df = read_infile(args.infile)


    logging.info("extracting the search engines")
    se = common.select_search_engine(df)
    logging.debug(se)
    if not se:
        sms = "The search engines has not been recognized"
        logging.error(sms)
        sys.exit(sms)


    logging.info("extracting the quantification")
    ddf = add_quantification(args.n_workers, args.indir, se, df, indata)


    logging.info("print the ID files by experiments")
    with concurrent.futures.ProcessPoolExecutor(max_workers=args.n_workers) as executor:        
        tmpfiles = executor.map( print_by_experiment,
                                list(ddf.groupby("Experiment")),
                                itertools.repeat(args.outdir),
                                itertools.repeat("ID.tsv") )
    [common.rename_tmpfile(f) for f in list(tmpfiles)] # rename tmp file deleting before the original file 
        



if __name__ == '__main__':    
    # parse arguments
    parser = argparse.ArgumentParser(
        description='Create the structure of ID for iSanXoT',
        epilog='''
        Example:
            python createID.py

        ''')
    parser.add_argument('-w',  '--n_workers', type=int, default=2, help='Number of threads/n_workers (default: %(default)s)')
    parser.add_argument('-i',  '--infile', required=True, help='Input file: ID.tsv')
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
