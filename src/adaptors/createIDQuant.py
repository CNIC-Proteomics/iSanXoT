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
sys.path.append(f"{os.path.dirname(__file__)}/libs")
import common
import PD
import MSFragger
import Comet
import MaxQuant
import Quant


###################
# Local functions #
###################
def processing_infiles(file, Expt, se):
    '''
    Processing the input files depending on search engine
    '''
    if se == "PD":
        df = PD.processing_infiles(file, Expt)
    elif se == "Comet":
        df = Comet.processing_infiles(file, Expt)
    elif se == "MSFragger":
        df = MSFragger.processing_infiles(file, Expt)
    elif se == "MaxQuant":
        df = MaxQuant.processing_infiles(file, Expt)
    else:
        return None
    return df

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


    logging.info("Get IDENTIFICATION from the search engine results -----")

    logging.info("extract the list of files from the given experiments")
    infiles = [common.get_path_file(i, args.indir) for i in list(indata['infile']) if not pd.isna(i)] # if apply, append input directory to file list
    logging.debug(infiles)
    if not all(infiles):
        sms = "At least, one of input files is wrong"
        logging.error(sms)
        sys.exit(sms)


    logging.info("extract the search engines from the given experiments")
    ses = [common.select_search_engines(i) for i in infiles]
    logging.debug(ses)
    if not all(ses):
        sms = "The search engines has not been recognized"
        logging.error(sms)
        sys.exit(sms)

    
    
    logging.info("extract the list of experiments")
    Expt = list(indata['experiment'])
    logging.debug(Expt)
    
    
    logging.info("processing the input file")
    with concurrent.futures.ProcessPoolExecutor(max_workers=args.n_workers) as executor:            
        ddf = executor.map( processing_infiles, infiles, Expt, ses )
    ddf = pd.concat(ddf)
    # ddf = processing_infiles(infiles[0], Expt[0], ses[0])



    # Get QUANTIFICATION from the MZ FILES (if apply) -----

    # check if mzfile and quan_method columns are fillin. Otherwise, the program does nothing.
    c = indata.columns.tolist()
    if 'mzfile' in c and 'quan_method' in c and not all(indata['mzfile'].str.isspace()) and not all(indata['quan_method'].str.isspace()):
        
        logging.info("Get QUANTIFICATION from the MZ FILES -----")
        
        # if apply, append input directory to file list
        indata['mzfile'] = [common.get_path_file(i, args.indir) for i in list(indata['mzfile']) if not pd.isna(i)]
        logging.debug(indata['mzfile'].values.tolist())

        logging.info("prepare the parameters for each experiment/spectrum file")
        # one experiment can be multiple spectrum files
        with concurrent.futures.ProcessPoolExecutor(max_workers=args.n_workers) as executor:            
            params = executor.map( Quant.prepare_params,
                                  list(ddf.groupby("Experiment")),
                                  list(indata.groupby("experiment")) )
        params = list(params)
        # params = Quant.prepare_params(list(ddf.groupby("Experiment"))[0], list(indata.groupby("experiment"))[0])

        logging.info("extract the quantification")
        with concurrent.futures.ProcessPoolExecutor(max_workers=args.n_workers) as executor:            
            quant = executor.map( Quant.extract_quantification, params)
        quant = pd.concat(quant)
        # quant = Quant.extract_quantification(params[0])


        logging.info("merge the quantification")
        with concurrent.futures.ProcessPoolExecutor(max_workers=args.n_workers) as executor:            
            ddf = executor.map( Quant.merge_quantification,
                                    list(ddf.groupby("Spectrum_File")),
                                    list(quant.groupby("Spectrum_File")) )
        ddf = pd.concat(ddf)
        # ddf = Quant.merge_quantification( list(ddf.groupby("Spectrum_File"))[0], list(quant.groupby("Spectrum_File"))[0] )


    logging.info("print the ID files by experiments")
    with concurrent.futures.ProcessPoolExecutor(max_workers=args.n_workers) as executor:        
        tmpfiles = executor.map( print_by_experiment,
                                list(ddf.groupby("Experiment")),
                                itertools.repeat(args.outdir),
                                itertools.repeat("ID.tsv") )
    [common.print_outfile(f) for f in list(tmpfiles)] # rename tmp file deleting before the original file 
        



if __name__ == '__main__':    
    # parse arguments
    parser = argparse.ArgumentParser(
        description='Create the structure of ID for iSanXoT',
        epilog='''
        Example:
            python createID.py

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
