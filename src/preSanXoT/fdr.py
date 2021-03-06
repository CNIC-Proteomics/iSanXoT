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

###################
# Local functions #
###################
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


def targetdecoy(df, tagDecoy):
    '''
    Assing target and decoy proteins
    '''    
    z = list(df["Protein Accessions"].str.split(";"))
    p = [(all(tagDecoy  in item for item in i )) for i in z]
    r = [0 if i==True else 1 for i in p]
    return r

def Jumps(df, JumpsAreas):
    '''
    Correct monoisotopic mass
    '''
    s1=df["DeltaM [ppm]"]
    s2=(df["Theo. MH+ [Da]"]-(df["MH+ [Da]"]-1.003355))/df["Theo. MH+ [Da]"]*1e6
    s3=(df["Theo. MH+ [Da]"]-(df["MH+ [Da]"]+1.003355))/df["Theo. MH+ [Da]"]*1e6
    s4=(df["Theo. MH+ [Da]"]-(df["MH+ [Da]"]-2*1.003355))/df["Theo. MH+ [Da]"]*1e6
    s5=(df["Theo. MH+ [Da]"]-(df["MH+ [Da]"]+2*1.003355))/df["Theo. MH+ [Da]"]*1e6
    df1 = pd.DataFrame( {"1":s1,"2":s2,"3":s3,"4":s4,"5":s5 })
    if JumpsAreas == 1:
        j = ["1"]
    elif JumpsAreas == 3: 
        j = ["1","2","3"]
    elif JumpsAreas == 5: 
        j = ["1","2","3","4","5"]
    Deltamass=df1[j].abs().min(axis=1)

    x = list( zip(s1,s2,s3,s4,s5) )

    return Deltamass,x

def cXCorr(df):
    '''
    Calculate cXCorr
    '''
    rc=np.where(df['Charge']>=3, '1.22', '1').astype(float)
    cXCorr1= np.log(df['XCorr']/rc)/np.log(2*df['Sequence'].str.len())
    return cXCorr1

def preProcessing(file, deltaMassThreshold, tagDecoy, JumpsAreas):
    '''
    Pre-processing the data: assign target-decoy, correct monoisotopic mass, calculate cXCorr
    '''    
    # read input file
    df = pd.read_csv(file, sep="\t")
    # assing target and decoy proteins
    df["T_D"] = targetdecoy(df, tagDecoy)
    df = df[df["Search Engine Rank"] == 1 ]
    # correct monoisotopic mass
    df["JDeltaM [ppm]"],df["JDeltaM"] = Jumps(df, JumpsAreas)
    df = df[ df["JDeltaM [ppm]"].abs() <= deltaMassThreshold ]
    # calculate cXCorr
    df["cXCorr"] = cXCorr(df)
    return df

def SequenceMod(df, mods):
    '''
    Extract modifications and replace for final values
    '''
    # extract modifications and replace for final values
    s = df['Modifications'].fillna('').replace(mods, regex=True)
    # create indexes list
    sn = list( s.replace({
        '(\S*N-Term\S*)': '',
        '\([^)]*\)': '',
        '(\s)': '',
        '([A-Z])': '',
    }, regex=True).str.split(";") )
    sn = [list(filter(None,i)) for i in sn]
    sn = [[int(i) for i in j] for j in sn]
    [[a.insert(0,0) ] for a in sn]
    # create Modifications list
    sa = list( s.replace({
        '(\S*N-Term\S*)': '',
        '[^\(\)]*\(([^\)]+)\)': "["+ r"\1];"
    }, regex=True).str.split(";") )
    sa = [list(filter(None,i)) for i in sa]
    # split sequence and insert modification
    l = list(df["Sequence"])
    f = [[a[i:j]for i,j in zip(b,b[1:]+[None])] for a,b in zip(l,sn)]
    x = ["".join(list(itertools.chain.from_iterable(list(itertools.zip_longest(i,j,fillvalue=''))))) for i,j in list(zip(f,sa))]
    return x

def FdrXc(df, typeXCorr, FDRlvl, mods):
    '''
    Calculate FDR and filter by cXCorr
    '''
    # get the dataframe from the input tuple df=(exp,df)
    df = df[1].sort_values(by=[typeXCorr,"T_D"], ascending=False)
    df["rank"] = df.groupby("T_D").cumcount()+1
    df["rank_T"] = np.where(df["T_D"]==1, df["rank"], 0)
    df["rank_T"] = df["rank_T"].replace(to_replace=0, method='ffill')
    df["rank_D"] = np.where(df["T_D"]==0, df["rank"], 0)
    df["rank_D"] = df["rank_D"].replace(to_replace=0, method='ffill')
    df["FdrXc"] = df["rank_D"]/df["rank_T"]
    df = df[ df["FdrXc"] <= FDRlvl ] # filter by input FDR
    df = df[ df["T_D"] == 1 ] # discard decoy
    if mods:
        df["SequenceMod"] = SequenceMod(df, mods)
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
    
  
    logging.info("pre-processing the data: assign target-decoy, correct monoisotopic mass, calculate cXCorr")
    ddf = preProcessing(args.infile, deltaMassThreshold, tagDecoy, JumpsAreas)

      
    logging.info("create modifications dictionary from xml-doc of UNIMOD")
    with concurrent.futures.ProcessPoolExecutor(max_workers=args.n_workers) as executor:        
        mods = executor.map(extract_modifications, ddf['Modifications'], chunksize=int(len(ddf)/args.n_workers))
    modifications = join_modifications(mods)
    logging.debug(modifications)


    logging.info("calculate the FDR by experiment")
    with concurrent.futures.ProcessPoolExecutor(max_workers=args.n_workers) as executor:        
        ddf = executor.map(FdrXc, list(ddf.groupby("Experiment")), repeat(typeXCorr), repeat(FDRlvl), repeat(modifications))
    ddf = pd.concat(ddf)

    
    logging.info("print the output")
    # print to tmp file
    f = f"{args.outfile}.tmp"
    ddf.to_csv(f, sep="\t", index=False)
    # rename tmp file
    os.rename(f, os.path.splitext(f)[0])


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
    parser.add_argument('-x',  '--type_xcorr', type=str, choices=['XCorr','cXCorr'], default='XCorr', help='Calculate FDR from the type of XCorr (default: %(default)s)')
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