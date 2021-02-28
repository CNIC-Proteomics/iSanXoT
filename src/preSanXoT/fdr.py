#!/usr/bin/python

# Module metadata variables
__author__ = ["Ricardo Magni", "Jose Rodriguez"]
__credits__ = ["Ricardo Magni", "Jose Rodriguez", "Jesus Vazquez"]
__license__ = "Creative Commons Attribution-NonCommercial-NoDerivs 4.0 Unported License https://creativecommons.org/licenses/by-nc-nd/4.0/"
__version__ = "1.0.1"
__maintainer__ = "Jose Rodriguez"
__email__ = "jmrodriguezc@cnic.es"
__status__ = "Development"

# import global modules
import os
import sys
import itertools
import argparse
import logging
import pandas as pd
import numpy as np
import re
import xml.etree.ElementTree as etree
import concurrent.futures
from itertools import repeat

#########################
# Import local packages #
#########################
sys.path.append(f"{os.path.dirname(__file__)}/libs")
import createID
import PD
import MSFragger
import Comet

###################
# Local functions #
###################

def select_search_engines(file):
    # read the first line to know which searh engine we have.
    with open(file) as f: first_line = f.readline()
    fa = re.findall(r'^# search_engine: ([^\s]*)', first_line)
    if fa: se = fa[0]
    else: se = None
    return se

def preProcessing(file, deltaMassThreshold, tagDecoy, JumpsAreas):
    # read which search engines we have
    se = select_search_engines(file)
    # processing the input files depending on
    if se == "PD": df = PD.preProcessing(file, deltaMassThreshold, tagDecoy, JumpsAreas)
    elif se == "Comet": df = Comet.preProcessing(file, deltaMassThreshold, tagDecoy, JumpsAreas)
    elif se == "MSFragger": df = MSFragger.preProcessing(file, deltaMassThreshold, tagDecoy, JumpsAreas)
    return df

def FdrXc(df, typeXCorr, FDRlvl):
    '''
    Calculate FDR and filter by cXCorr
    '''
    # get the dataframe from the input tuple df=(exp,df)
    # sort by the type of score
    df = df[1].sort_values(by=[typeXCorr,"T_D"], ascending=False)
    # rank the target and decoy individually
    df["rank"] = df.groupby("T_D").cumcount()+1
    df["rank_T"] = np.where(df["T_D"]==1, df["rank"], 0)
    df["rank_T"] = df["rank_T"].replace(to_replace=0, method='ffill')
    df["rank_D"] = np.where(df["T_D"]==0, df["rank"], 0)
    df["rank_D"] = df["rank_D"].replace(to_replace=0, method='ffill')
    # calcultate FDR: FDR = rank(D)/rank(T)
    df["FdrXc"] = df["rank_D"]/df["rank_T"]
    # filter by input FDR
    df = df[ df["FdrXc"] <= FDRlvl ]
    # discard decoy
    df = df[ df["T_D"] == 1 ]
    return df

def extract_modifications(s_ddf):
    '''
    Create modifications dictionary from xml-doc of UNIMOD
    '''
    # extract the unique labels of modifications from the input files
    m = re.findall(r'\(([^\)]*)\)', str(s_ddf))
    return m

def join_modifications(mods):
    # declare
    modifications = {}
    lmods = np.unique( list(itertools.chain.from_iterable(mods)) )
    # create xml-doc from UNIMOD
    localdir = os.path.dirname(os.path.abspath(__file__))
    root = etree.parse(localdir+'/unimod.xml').getroot()
    ns = {'umod': 'http://www.unimod.org/xmlns/schema/unimod_2'}
    xdoc_mods = root.find('umod:modifications', ns)
    # extract the delta mono_mass for each modification
    for m in lmods:
        delta = xdoc_mods.find('umod:mod[@title="'+m+'"]/umod:delta', ns)
        if delta:
            mono_mass = delta.get('mono_mass')
            m2 = r'\('+str(m)+r'\)'
            modifications[m2] = '('+mono_mass+')'
    return modifications

def SequenceMod(df, mods, file):
    '''
    Create a sequence with modifications
    '''
    # get the dataframe from the input tuple df=(exp,df)
    df = df[1]
    # read which search engines we have
    se = select_search_engines(file)
    # create sequence with modifications depending on
    if se == "PD": df["SequenceMod"] = PD.SequenceMod(df, mods)
    elif se == "Comet": df["SequenceMod"] = Comet.SequenceMod(df)
    elif se == "MSFragger": df["SequenceMod"] = MSFragger.SequenceMod(df)
    return df



def main(args):
    '''
    Main function
    '''
    logging.info("prepare input parameters")
    deltaMassThreshold = args.threshold
    tagDecoy = args.lab_decoy
    FDRlvl = args.fdr
    typeXCorr = args.type_xcorr
    JumpsAreas = args.jump_areas
    
  
    logging.info("pre-processing the data: assign target-decoy, correct monoisotopic mass")
    ddf = preProcessing(args.infile, deltaMassThreshold, tagDecoy, JumpsAreas)

      
    logging.info("calculate the FDR by experiment")
    with concurrent.futures.ProcessPoolExecutor(max_workers=args.n_workers) as executor:        
        ddf = executor.map(FdrXc, list(ddf.groupby("Experiment")), repeat(typeXCorr), repeat(FDRlvl))
    ddf = pd.concat(ddf)

    
    logging.info("create modifications dictionary from xml-doc of UNIMOD")
    with concurrent.futures.ProcessPoolExecutor(max_workers=args.n_workers) as executor:        
        mods = executor.map(extract_modifications, ddf['Modifications'], chunksize=int(len(ddf)/args.n_workers))
    modifications = join_modifications(mods)
    logging.debug(modifications)

    
    logging.info("calculate the SequenceMod by experiment")
    with concurrent.futures.ProcessPoolExecutor(max_workers=args.n_workers) as executor:        
        ddf = executor.map(SequenceMod, list(ddf.groupby("Experiment")), repeat(modifications), repeat(args.infile))
    ddf = pd.concat(ddf)


    logging.info("print the output")
    # print to tmp file
    f = f"{args.outfile}.tmp"
    ddf.to_csv(f, sep="\t", index=False)
    # rename tmp file deleting before the original file 
    createID.print_outfile(f)



if __name__ == '__main__':
    # parse arguments
    parser = argparse.ArgumentParser(
        description='Calculate the FDR',
        epilog='''
        Example:
            python fdr.py -i tests/pratio/Tissue_10ppm  -e "TMTHF" -l "DECOY_" -o tests/pratio/Tissue_10ppm

        ''')
    parser.add_argument('-w',  '--n_workers', type=int, default=2, help='Number of threads/n_workers (default: %(default)s)')
    parser.add_argument('-i',  '--infile', required=True, help='Input file: ID.tsv')
    parser.add_argument('-f',  '--fdr', type=float, default=0.01, help='FDR value (default: %(default)s)')
    parser.add_argument('-x',  '--type_xcorr', type=str, default='XCorr', help="Calculate FDR from the the given scores: 'XCorr','cXCorr','hyperscore' (default: %(default)s)")
    parser.add_argument('-t',  '--threshold', type=int, default=20, help='Threshold of delta mass (default: %(default)s)')
    parser.add_argument('-j',  '--jump_areas', type=int, choices=[1,3,5], default=5, help='Number of jumps [1,3,5] (default: %(default)s)')
    parser.add_argument('-l',  '--lab_decoy', required=True, help='Label of decoy sequences in the db file')
    parser.add_argument('-o',  '--outfile',   required=True, help='Output file')
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