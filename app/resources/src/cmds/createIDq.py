#!/usr/bin/python

# Module metadata variables
__author__ = ["Jose Rodriguez", "Ricardo Magni"]
__credits__ = ["Jose Rodriguez", "Ricardo Magni", "Jesus Vazquez"]
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
import shutil
import pandas as pd
import numpy as np
import concurrent.futures
from itertools import repeat
import re



#########################
# Import local packages #
#########################
sys.path.append(f"{os.path.dirname(__file__)}/../libs")
import common
import extractquant
import fdr
import ProteinAssigner_v5



###################
# Local functions #
###################
def parse_arguments(argv):
    # parse arguments
    parser = argparse.ArgumentParser(
        description='Create the ID-q (identification and quantification) file for iSanXoT',
        epilog='''
        Join the results in a file and include the experiment column. If apply:
            - Add the level identifiers.
            - Extract and add the quantifications.
            - Execute the pRatio: calculate the cXCorr, FDR.
            - Calculate the most probable protein.
        ''')
    parser.add_argument('-w',   '--n_workers', type=int, default=2, help='Number of threads/n_workers (default: %(default)s)')
    # input files:
    # Identification/Quantification input file
    parser.add_argument('-ii',  '--infile', help='Input Identification/Quantification file')
    # or
    # create ID-q from proteomics pipelines
    parser.add_argument('-id',  '--indir', help='Input Directory where identifications are saved')
    parser.add_argument('-te',  '--intbl-exp', help='File has the params for the input experiments')
    parser.add_argument('-tl',  '--intbl-lev', help='File has the params for the level identifiers')
    parser.add_argument('-tlf', '--intbl-labelfree', help='File has the params for the creation intensity table from label-free')
    # optional parameters:
    parser.add_argument('-iz',  '--indir-mzml', help='Input Directory where mzML are saved')
    parser.add_argument('-tq',  '--intbl-quant', help='File has the params for the quantification extraction')
    parser.add_argument('-tf',  '--intbl-fdr', help='File has the pRatio params')
    parser.add_argument('-tp',  '--intbl-mpp', help='File has the MPP params')
    parser.add_argument('-o',   '--outfile', required=True, help='Output file')
    parser.add_argument('-vv', dest='verbose', action='store_true', help="Increase output verbosity")
    args = parser.parse_args(argv)
    
    # get the name of script
    script_name = os.path.splitext( os.path.basename(__file__) )[0].upper()
    
    # logging debug level. By default, info level
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG,
                            format=script_name+' - '+str(os.getpid())+' - %(asctime)s - %(levelname)s - %(message)s',
                            datefmt='%m/%d/%Y %I:%M:%S %p',
                            force=True)
    else:
        logging.basicConfig(level=logging.INFO,
                            format=script_name+' - '+str(os.getpid())+' - %(asctime)s - %(levelname)s - %(message)s',
                            datefmt='%m/%d/%Y %I:%M:%S %p',
                            force=True)
    return args

def add_exps(indata, indir, addExp):
    '''
    Pre-processing the data for CNIC group
    - add needed columns
    '''
    # read input file
    try:
        file = common.get_path_file(indata[0], indir)
        df = pd.read_csv(file, sep="\t")
    except Exception as exc:
        sms = "At least, one of input files is wrong: {}".format(exc)
        logging.error(sms)
        sys.exit(sms)
    # add Experiment column
    if len(indata) > 1:
        exp = indata[1]
        df['Experiment'] = exp
    # add the Spectrum File column from the input file name
    if addExp and 'Spectrum_File' not in df.columns:
        df['Spectrum_File'] = os.path.basename(file)
    return df

def add_experiments(n_workers, indir, indata, addSpecFile=False):
    '''
    Add experiment column
    '''
    with concurrent.futures.ProcessPoolExecutor(max_workers=n_workers) as executor:            
        ddf = executor.map( add_exps, indata.values.tolist(), repeat(indir), repeat(addSpecFile))
    ddf = pd.concat(ddf)
    # begin: for debugging in Spyder
    # ddf = add_exps(indata.values.tolist()[0], indir, addSpecFile)
    # end: for debugging in Spyder
    return ddf

def add_levelids(df, indata):
    '''
    Pre-processing the data:
    - add needed columns
    '''    
    # extract the info of indata
    hh = list(indata['headers_join'].str.split('\s*,\s*'))
    ll = list(indata['label_name'])
    # concatenate multi columns (fast way):
    # extract the columns
    # convert to sgring and remove spaces
    # concatenate (fastest)
    for i,h in enumerate(hh):
        l = ll[i]
        x = list( range(len(h)) )
        if len(x) > 0:
            df[l] = df[h[0]].astype(str).str.replace(" ","")
            for i in x[1:]:
                df[l] = df[l]+'__'+df[h[i]].astype(str).str.replace(" ","")
    return df


def print_in_background(df, file):
    df.to_csv(file, index=False, sep="\t", line_terminator='\n')


def main(argv):
    '''
    Main function
    '''
    
    # PARSE ARGUMENTS ---
    args = parse_arguments(argv)


    # GET THE IDQ ---
    
    # provide the IDq and there are any CNIC adaptor: quant, fdr, protein assigner
    if args.infile and not args.indir and not args.intbl_exp and (args.intbl_quant or args.intbl_fdr or args.intbl_mpp):
        logging.info("reading PROVIDE_IDQ module ---")
        # read the idq to then, the operators work on it
        df = pd.read_csv(args.infile, sep="\t")
    # provide the IDq but there are not any CNIC adaptor
    elif args.infile and not args.indir and not args.intbl_exp and not (args.intbl_quant or args.intbl_fdr or args.intbl_mpp):
        logging.info("executing PROVIDE_IDQ module ---")
        try:
            logging.info("coping the identification/quantification file")
            # print to tmp file
            f = f"{args.outfile}.tmp"
            shutil.copyfile(args.infile, f)
            # rename tmp file deleting before the original file 
            common.rename_tmpfile(f)        
        except Exception as exc:
            sms = "ERROR!! Copying file: {}".format(exc)
            logging.error(sms)
            sys.exit(sms)    
        # exit main
        return None
    # create the IDq from the proteomic pipelines
    elif args.indir and not args.infile:
        logging.info("executing CREATE_IDQ module ---")
        # add exp cols
        if args.intbl_exp:
            logging.info("reading the experiment task-table")
            indata = common.read_task_table(args.intbl_exp)
            if indata.empty:
                sms = "There is not experiment task-table"
                logging.error(sms)
                sys.exit(sms)
        logging.info("processing the input file: read, add exp")
        # add the experiment columns
        if args.intbl_quant or args.intbl_fdr:
            # in addition, add 'Spectrum_File' columns if the adaptors are then executed
            df = add_experiments(args.n_workers, args.indir, indata, True)
        else:
            df = add_experiments(args.n_workers, args.indir, indata)
        # add level ids
        if args.intbl_lev:
            logging.info("reading the level task-table")
            indata = common.read_task_table(args.intbl_lev)
            if indata.empty:
                sms = "There is not level task-table"
                logging.error(sms)
                sys.exit(sms)
            logging.info("adding level identifiers")
            df = add_levelids(df, indata)
        # create pivot table based on the intensities (for Label-Free results)
        if args.intbl_labelfree:
            logging.info("reading the label-free task-table")
            indata = common.read_task_table(args.intbl_labelfree)
            if indata.empty:
                sms = "There is not labelfree task-table"
                logging.error(sms)
                sys.exit(sms)
            logging.info("creating the pivot table from label-free results")
            
            # create the pivot table based on the given parameters
            given_vals = re.split(r'\s*,\s*', indata.loc[0,'headers_intensities'])
            given_index = indata.loc[0,'feature_id']
            # given_cols = re.split(r'\s*,\s*', indata.loc[0,'feature_exp'])
            given_cols = ['Experiment']
            # pivot table
            int_df = pd.pivot_table(df, values=given_vals, index=given_index, columns=given_cols, aggfunc=np.sum, fill_value=0)
            int_df = int_df.reset_index()
            # rename columns taking into account the first column is the "index" column from pivot table
            int_df.columns = [ c[0] if i == 0 else c[1] for i,c in enumerate(int_df.columns)]
            # merge df's based on "Index" column
            df = pd.merge(df, int_df, on=given_index)
    else:
        sms = "You have to provide one of two type of inputs: prividing ID-q by user or creating the ID-q from proteomic pipelines"
        logging.error(sms)
        sys.exit(sms)       





    # CNIC ADAPTORS ----


    if args.intbl_quant or args.intbl_fdr:
        logging.info("extracting the search engines")
        se = common.select_search_engine(df)
        logging.debug(se)
        if not se:
            sms = "The search engines has not been recognized"
            logging.warning(sms)
            # sys.exit(sms)




    if args.intbl_quant:
        logging.info("executing CNIC_ADAPTOR:ADD_QUANT module ---")
        logging.info("reading the quantification task-table")
        indata = common.read_task_table(args.intbl_quant)
        if indata.empty:
            sms = "There is not quantification task-table"
            logging.error(sms)
            sys.exit(sms)
        # add the error ppm value. TODO! It would be nice to provide this value as parameter
        indata['error_ppm'] = 10
        logging.info("extracting the quantification")
        df = extractquant.add_quantification(args.n_workers, args.indir_mzml, se, df, indata)
        if df is None or df.empty:
            sms = "There was a problem extacting the quantification"
            logging.error(sms)
            sys.exit(sms)
        logging.info("printing quantification file")
        f = os.path.join( os.path.dirname(args.outfile), 'Q-all.tsv' )
        df.to_csv(f, index=False, sep="\t", line_terminator='\n')           



    if args.intbl_fdr:
        logging.info("executing CNIC_ADAPTOR:ADD_FDR (pRatio) module ---")
        logging.info("reading the FDR task-table")
        indata = common.read_task_table(args.intbl_fdr)
        if indata.empty:
            sms = "There is not FDR task-table"
            logging.error(sms)
            sys.exit(sms)
        logging.info("calculating the FDR")
        df = fdr.calc_fdr(args.n_workers, se, df, indata)



    logging.info("printing tmp file")
    tmpfile = common.print_tmpfile(df, args.outfile)



    if args.intbl_mpp:
        logging.info("executing CNIC_ADAPTOR:ADD_MPP module ---")
        logging.info("reading the MPP task-table")
        indata = common.read_task_table(args.intbl_mpp)
        if indata.empty:
            sms = "There is not MPP task-table"
            logging.error(sms)
            sys.exit(sms)
        logging.info("preparing the parametes for protein assigner")
        indata = indata.to_dict('list')
        # fasta mode
        if 'peptide_col' in indata and 'fasta_file' in indata and 'label_decoy' in indata and 'output_col' in indata:
            seq_col = indata['peptide_col'][0]
            fasta_file = indata['fasta_file'][0]
            prot_col = indata['protein_col'][0] if 'protein_col' in indata else 'PA_accession_candidates'
            prot_col_dsc = indata['prot_desc_col'][0] if 'prot_desc_col' in indata else 'PA_description_candidates'
            prot_col_mpp = indata['output_col'][0]
            prot_col_dsc_mpp = indata['output_desc_col'][0] if 'output_desc_col' in indata else ''
            label_decoy = indata['label_decoy'][0]
            isoleu = indata['iso_leucine'][0] if 'iso_leucine' in indata else ''
            regex_previous = indata['regex_previous'][0] if 'regex_previous' in indata else '//'
            regex_previous = [re.compile(i, re.IGNORECASE) for i in re.split(r'(?<!\\)/', regex_previous.strip('/ '))] # this is heredity from ProteinAssigner program
            regex = indata['regex'][0] if 'regex' in indata else '//'
            regex = [re.compile(i, re.IGNORECASE) for i in re.split(r'(?<!\\)/', regex.strip('/ '))] # this is heredity from ProteinAssigner program
            len_seq = int(indata['len_seq'][0]) if 'len_seq' in indata else 0
            paramsDict = {
                "infile": [tmpfile],
                "outfile": [tmpfile],
                "n_cores": args.n_workers,
                "seq_column": seq_col,                
                "regex_previous": regex_previous,
                "regex": regex,
                "len_seq": len_seq,
                "mpp_a": prot_col_mpp,
                "mpp_d": prot_col_dsc_mpp,
                "mode": "fasta",
                "fasta_params": {
                    "fasta": fasta_file,
                    "decoy_prefix": label_decoy,
                    "iso_leucine": isoleu,
                    "candidate_a": prot_col,
                    "candidate_d": prot_col_dsc
                }
            }
        # columns mode
        elif 'peptide_col' in indata and 'protein_col' in indata and 'output_col' in indata:
            seq_col = indata['peptide_col'][0]
            prot_col = indata['protein_col'][0]
            prot_col_dsc = indata['prot_desc_col'][0] if 'prot_desc_col' in indata else ''
            sep_chr = indata['prot_sep'][0] if 'prot_sep' in indata else ';'
            prot_col_mpp = indata['output_col'][0]
            prot_col_dsc_mpp = indata['output_desc_col'][0] if 'output_desc_col' in indata else ''
            regex_previous = indata['regex_previous'][0] if 'regex_previous' in indata else '//'
            regex_previous = [re.compile(i, re.IGNORECASE) for i in re.split(r'(?<!\\)/', regex_previous.strip('/ '))] # this is heredity from ProteinAssigner program            
            regex = indata['regex'][0] if 'regex' in indata else '//'
            regex = [re.compile(i, re.IGNORECASE) for i in re.split(r'(?<!\\)/', regex.strip('/ '))] # this is heredity from ProteinAssigner program
            len_seq = int(indata['len_seq'][0]) if 'len_seq' in indata else 0
            paramsDict = {
                "infile": [tmpfile],
                "outfile": [tmpfile],
                "n_cores": args.n_workers,
                "seq_column": seq_col,
                "regex_previous": regex_previous,
                "regex": regex,
                "len_seq": len_seq,
                "mpp_a": prot_col_mpp,
                "mpp_d": prot_col_dsc_mpp,
                "mode": "column",
                "column_params": {
                    "candidate_a": prot_col,
                    "candidate_d": prot_col_dsc,
                    "sep_char": sep_chr
                }
            }
        if paramsDict:
            logging.info("calculating the MPP")
            logging.debug(paramsDict)
            ProteinAssigner_v5.main(paramsDict)


    # rename tmp file deleting before the original file 
    logging.info("renaming tmp file")
    common.rename_tmpfile(tmpfile)

        



if __name__ == '__main__':
    # start main function
    logging.info('start script: '+"{0}".format(" ".join([x for x in sys.argv])))
    main(sys.argv[1:])
    logging.info('end script')
