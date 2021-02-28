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
import re
import io
import pandas as pd
import concurrent.futures
import itertools

#########################
# Import local packages #
#########################
sys.path.append(f"{os.path.dirname(__file__)}/libs")
import PD
import MSFragger
import Comet
import MaxQuant

####################
# Common functions #
####################
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
                if c2 in indata:
                    indata[c2] = pd.concat( [indata[c2], d], sort=False)
                else:
                    indata[c2] = d
    return indata

def select_search_engines(file):
    # read the first row
    # determines which kind of searh engines we have.
    # PD has to be "First Scan" column
    # The first line is a commnet line in Comet
    # MSFragger has to be "sannum" column
    # MaxQuant has to be "PEP" column
    d = pd.read_csv(file, nrows=0, sep="\t", index_col=False)    
    search_engines = ["PD","Comet","MSFragger","MaxQuant"]
    cond = ("First Scan" in list(d.columns), len(d.columns) == 4, "scannum" in list(d.columns), "PEP" in list(d.columns))
    se = [i for (i, v) in zip(search_engines, cond) if v][0]
    return se

def print_outfile(f):
    '''
    Rename the temporal files deleting the last suffix
    '''
    # get the output file deleting the last suffix
    ofile = os.path.splitext(f)[0]
    # remove obsolete output file
    if os.path.isfile(ofile):
        os.remove(ofile)
    # rename the temporal file
    os.rename(f, ofile)

###################
# Local functions #
###################
def processing_infiles(file, Expt, se):
    
    # se = 'Comet'
    
    # processing the input files depending on
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

def print_by_experiment(df, expt_se_files, outdir):
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
    ofile = f"{outdir_e}/ID.tsv.tmp"
    if os.path.isfile(ofile):
        os.remove(ofile)
    # print the experiment files with the header
    # we extract the search engine and the input files for the current experiment
    # create comment line given the following information:
    #   - search engines
    #   - list of input files
    of = open(ofile, 'w')
    se = [(i[1],i[2]) for i in expt_se_files if i[0] == exp] # zip(Expt, search_engine, inputfile)
    if se:
        s = se[0][0] # get the first value of "search engine"
        f = [i[1] for i in se] # get the list of input files
        of.write(f"# search_engine: {s}\n")
        of.write( "# infiles:\n")
        of.write( "# {}\n".format("\n# ".join(f)) )
    df[1].to_csv(of, index=False, sep="\t", line_terminator='\n')
    of.close()
    # df[1].to_csv(ofile, sep="\t", index=False)
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
    indata = read_command_table(args.intbl)

    if 'CREATE_ID' in indata:
        logging.info("extract the list of files from the given experiments")
        infiles = list(indata['CREATE_ID']['infile'])
        # Append input directory to file list
        infiles = [i if os.path.isfile(i) else f"{args.indir}/{i}" for i in infiles] 
        logging.debug(infiles)
        
        logging.info("extract the search engines from the given experiments")
        ses = [select_search_engines(i) for i in infiles] 
        logging.debug(ses)
        
        logging.info("extract the list of experiments")
        Expt    = list(indata['CREATE_ID']['experiment'])
        logging.debug(Expt)
        
        
        logging.info("processing the input file")
        with concurrent.futures.ProcessPoolExecutor(max_workers=args.n_workers) as executor:            
            ddf = executor.map( processing_infiles, infiles, Expt, ses )
        ddf = pd.concat(ddf)

                
        logging.info("print the ID files by experiments")
        with concurrent.futures.ProcessPoolExecutor(max_workers=args.n_workers) as executor:        
            tmpfiles = executor.map( print_by_experiment, list(ddf.groupby("Experiment")), itertools.repeat(zip(Expt,ses,infiles)), itertools.repeat(args.outdir) )  
        # rename tmp file deleting before the original file 
        [print_outfile(f) for f in list(tmpfiles)]
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
    parser.add_argument('-i',  '--indir', required=True, help='Input Directory')
    parser.add_argument('-t',  '--intbl', required=True, help='File with the input data: filename, experiments')
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
