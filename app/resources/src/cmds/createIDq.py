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
import shutil
import pandas as pd
import concurrent.futures
from itertools import repeat
# import threading



#########################
# Import local packages #
#########################
sys.path.append(f"{os.path.dirname(__file__)}/../libs")
import common
import extractQuant
import fdr
import ProteinAssigner_v3



###################
# Local functions #
###################
def add_exps(indata, indir):
    '''
    Pre-processing the data:
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
    return df

def add_exps_specfile(indata, indir):
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
    if 'Spectrum_File' not in df.columns:
        df['Spectrum_File'] = os.path.basename(file)
    return df

def add_experiments(n_workers, indir, indata, addSpecFile=False):
    '''
    Add experiment column
    '''
    if addSpecFile:
        with concurrent.futures.ProcessPoolExecutor(max_workers=n_workers) as executor:            
            ddf = executor.map( add_exps_specfile, indata.values.tolist(), repeat(indir))        
    else:
        with concurrent.futures.ProcessPoolExecutor(max_workers=n_workers) as executor:            
            ddf = executor.map( add_exps, indata.values.tolist(), repeat(indir))
    ddf = pd.concat(ddf)
    # begin: for debugging in Spyder
    # ddf = add_exps(infiles[0], Expt[0] )
    # end: for debugging in Spyder
    return ddf

def add_levelids(df, indata):
    '''
    Pre-processing the data:
    - add needed columns
    '''    
    # extract the info of indata
    hh = list(indata['headers_join'].str.split(','))
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

    

def main(args):
    '''
    Main function
    '''
    
    # PROVIDE_IDQ module ---
    if args.infile and not args.indir and not args.intbl_exp:
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
    
        # exit program
        sys.exit(0)
    
    # CREATE_IDQ module ---
    if args.indir and args.intbl_exp and not args.infile:
        logging.info("executing CREATE_IDQ module ---")
        logging.info("reading the experiment task-table")
        indata = common.read_task_table(args.intbl_exp)
        if indata.empty:
            sms = "There is not experiment task-table"
            logging.error(sms)
            sys.exit(sms)
        logging.info("processing the input file: read, add exp")
        if args.intbl_quant or args.intbl_fdr:
            # in addition, add 'Spectrum_File' columns
            df = add_experiments(args.n_workers, args.indir, indata, True)
        else:
            df = add_experiments(args.n_workers, args.indir, indata)
    else:
        sms = "You have to provide one of two type of inputs: prividing ID-q by user or creating the ID-q from proteomic pipelines"
        logging.error(sms)
        sys.exit(sms)       


    if args.intbl_lev:
        logging.info("reading the level task-table")
        indata = common.read_task_table(args.intbl_lev)
        if indata.empty:
            sms = "There is not level task-table"
            logging.error(sms)
            sys.exit(sms)
        logging.info("adding level identifiers")
        df = add_levelids(df, indata)



    # CNIC ADAPTORS ----


    if args.intbl_quant or args.intbl_fdr:
        logging.info("extracting the search engines")
        se = common.select_search_engine(df)
        logging.debug(se)
        if not se:
            sms = "The search engines has not been recognized"
            logging.error(sms)
            sys.exit(sms)




    if args.intbl_quant:
        logging.info("executing CNIC_ADAPTOR:ADD_QUANT module ---")
        logging.info("reading the quantification task-table")
        indata = common.read_task_table(args.intbl_quant)
        if indata.empty:
            sms = "There is not quantification task-table"
            logging.error(sms)
            sys.exit(sms)
        logging.info("extracting the quantification")
        df = extractQuant.add_quantification(args.n_workers, args.indir_mzml, se, df, indata)
        logging.info("printing quantification file")
        f = os.path.join( os.path.dirname(args.outfile), 'Q-all.tsv' )
        df.to_csv(f, index=False, sep="\t", line_terminator='\n')           
        # logging.info("printing quantification file (in background)")
        # f = os.path.join( os.path.dirname(args.outfile), 'Q-all.tsv' )
        # thread = threading.Thread(target=print_in_background, name="Printer", args=(df, f))
        # thread.start()




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
        if 'peptide_col' in indata and 'protein_col' in indata and 'output_col' in indata:
            seq_col = indata['peptide_col'][0]
            prot_col = indata['protein_col']
            if 'prot_desc_col' in indata: prot_col += indata['prot_desc_col']
            prot_col_mpp = indata['output_col']
            if 'output_desc_col' in indata: prot_col_mpp += indata['output_desc_col']
            sep_chr = indata['prot_sep'][0] if 'prot_sep' in indata else ';'
            # {'infile': ['S:/U_Proteomica/UNIDAD/DatosCrudos/jmrodriguezc/projects/iSanXoT/studies/adaptors/BAK_specific_adapters/Comet_CNIC/exps/ID.tsv'], 
            #  'outfile': ['S:/U_Proteomica/UNIDAD/DatosCrudos/jmrodriguezc/projects/iSanXoT/studies/adaptors/BAK_specific_adapters/Comet_CNIC/exps/ID-mpp.tsv'], 
            #  'seq_column': 'plain_peptide', 
            #  'mode': 'column', 
            #  'n_cores': 8, 
            #  'column_params': {
            #      'prot_column': ['Protein_Accessions', 'Protein_Descriptions'],
            #      'prot_column_mpp': ['Protein_MPP', 'Protein_Desc_MPP'],
            #      'sep_char': ';'}}
            paramsDict = {
                "infile": [tmpfile],
                "outfile": [tmpfile],
                "seq_column": seq_col,
                "mode": "column",
                "n_cores": args.n_workers,
                "column_params": {
                    "prot_column": prot_col,
                    "prot_column_mpp": prot_col_mpp,
                    "sep_char": sep_chr
                }
            }
            logging.info("calculating the MPP")
            ProteinAssigner_v3.main(paramsDict)


    # rename tmp file deleting before the original file 
    logging.info("renaming tmp file")
    common.rename_tmpfile(tmpfile)

        



if __name__ == '__main__':    
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
    # optional parameters:
    parser.add_argument('-iz',  '--indir-mzml', help='Input Directory where mzML are saved')
    parser.add_argument('-tq',  '--intbl-quant', help='File has the params for the quantification extraction')
    parser.add_argument('-tf',  '--intbl-fdr', help='File has the pRatio params')
    parser.add_argument('-tp',  '--intbl-mpp', help='File has the MPP params')

    parser.add_argument('-o',   '--outfile', required=True, help='Output file')
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
