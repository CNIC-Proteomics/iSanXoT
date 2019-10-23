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
import glob
import itertools
import argparse
import logging
import re
import pandas as pd
import numpy as np
import dask.dataframe as dd
from dask.delayed import delayed
from distributed import Client
import xml.etree.ElementTree as etree
import shutil



###################
# Local functions #
###################
def create_modifications(ddf):
    '''
    Create modifications dictionary from xml-doc of UNIMOD
    '''
    # declare
    modifications = {}
    # create xml-doc from UNIMOD
    localdir = os.path.dirname(os.path.abspath(__file__))
    root = etree.parse(localdir+'/unimod.xml').getroot()
    ns = {'umod': 'http://www.unimod.org/xmlns/schema/unimod_2'}
    xdoc_mods = root.find('umod:modifications', ns)
    # extract the unique labels of modifications from the input files
    m = ddf['Modifications'].str.extractall(r'\(([^\)]*)').compute()
    lmods = np.unique(m.values)
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
    z=list(df["Protein Accessions"].str.split(";"))
    p=[(all(tagDecoy  in item for item in i )) for i in z]
    # p=list(map(int, p))
    # return p
    r = [0 if i==True else 1 for i in p]
    return r

def Jumps(df, JumpsAreas):
    '''
    Correct monoisotopic mass
    '''
    # s1=(df["Theo. MH+ [Da]"]-df["MH+ [Da]"])/df["Theo. MH+ [Da]"]*1e6
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
    cXCorr1= np.log(df.XCorr/rc)/np.log(2*df.Sequence.str.len())
    return cXCorr1

def preProcessing(file, Expt, deltaMassThreshold, tagDecoy, JumpsAreas):
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
    # delete suffix in the headers coming from PD 2.3
    col = list(df.columns.values)
    col[:] = [s.replace('Abundance: ', '') for s in col]
    df.columns = col
    # add Experiment column
    df["Experiment"] = next((x for x in Expt if x in file), False)
    # assing target and decoy proteins
    df["T_D"] = targetdecoy(df, tagDecoy)
    df = df[df["Search Engine Rank"] == 1 ]
    # correct monoisotopic mass
    df["JDeltaM [ppm]"],df["JDeltaM"] = Jumps(df, JumpsAreas)
    df = df[ df["JDeltaM [ppm]"].abs() <= deltaMassThreshold ]
    # calculate cXCorr
    df["cXCorr"] = cXCorr(df)
    return df

def ProteinsGenes(df, tagDecoy):
    '''
    Extract the protein, genes (with redundances) and species discarding DECOY proteins
    '''
    def _pattern_gene(i):
        m = re.search('GN=([^\s]*)', i)
        r = m.group(1) if m else ''
        return r
    def _pattern_species(i):
        m = re.search('OS=([^\s]+\s+[^\s]+)', i)
        r = m.group(1) if m else ''
        return r
    a = list(df["Protein Accessions"].fillna("").str.split(";"))
    d = list(df["Protein Descriptions"].fillna("").str.split(";"))
    ad = [ list(itertools.chain(list(itertools.zip_longest(i,j,fillvalue='')))) for i,j in list(zip(a,d)) ]
    ad = [ ["|".join(i) for i in s] for s in ad ]
    # discard DECOY proteins and sort
    ad = [ [i for i in sorted(s) if not (tagDecoy in i)] for s in ad ]
    # get the protein list: the first element, the rest => reduncances, and descriptions
    p = [ [i.split("|")[0].strip() for i in s] for s in ad ]
    pm = [ i[0] for i in p ]
    pr = [ ";".join(i[1:]) for i in p ]
    pd = [ ";".join(i) for i in ad ]
    # get the gene list: the first element, the rest => reduncances
    g = [ [_pattern_gene(i) for i in s] for s in ad ]
    gm = [ i[0] for i in g ]
    gr = [ ";".join(i[1:]) for i in g ]
    # get the list of unique species
    x = [ [_pattern_species(i) for i in s] for s in ad ]
    s = [ ";".join(set(i)) for i in x ]
    return pm,pr,pd,gm,gr,s

def SequenceMod(df, mods):
    '''
    Extract modifications and replace for final values
    '''
    # extract modifications and replace for final values
    s = df.Modifications.fillna('').replace(mods, regex=True)
    # create indexes list
    sn = list( s.replace({
        'foo': '', # Due the test part of DASK
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

def FdrXc(df, typeXCorr, FDRlvl):
    '''
    Calculate FDR and filter by cXCorr
    '''
    # df = df.sort_values(by=["XCorr","T_D"], ascending=False)
    df = df.sort_values(by=[typeXCorr,"T_D"], ascending=False)
    df["rank"] = df.groupby("T_D").cumcount()+1
    df["rank_T"] = np.where(df["T_D"]==1, df["rank"], 0)
    df["rank_T"] = df["rank_T"].replace(to_replace=0, method='ffill')
    df["rank_D"] = np.where(df["T_D"]==0, df["rank"], 0)
    df["rank_D"] = df["rank_D"].replace(to_replace=0, method='ffill')
    df["FdrXc"] = df["rank_D"]/df["rank_T"]
    df = df[ df["FdrXc"] <= FDRlvl ] # filter by input FDR
    df = df[ df["T_D"] == 1 ] # discard decoy
    return df

def pro(ddf, typeXCorr, FDRlvl, mods, tagDecoy, Expt):
    '''
    Multi-task function: Calculate FDR and filter by cXCorr, create sequence with the mono_mas by mods, retrieve the list of protein,gene and species
    '''
    # calculate FDR and filter by cXCorr
    ddf = FdrXc(ddf, typeXCorr, FDRlvl)
    # extract modifications and replace for final values
    if mods:
        ddf["SequenceMod"] = SequenceMod(ddf, mods)
    # extract the redundance protein/genes discarding DECOY proteins
    ddf["Protein"],ddf["Protein_Redundancy"],ddf["Protein_Descriptions"],ddf["Gene"],ddf["Gene_Redundancy"],ddf["Species"] = ProteinsGenes(ddf, tagDecoy)
    # # rename columns
    # ddf.rename(columns={
    #     "Spectrum File": "Spectrum_File",
    #     "First Scan": "Scan"
    # }, inplace=True)
    return ddf



def main(args):
    '''
    Main function
    '''

    logging.info("prepare input parameters")
    inputfolder = args.indir
    deltaMassThreshold = args.threshold
    tagDecoy = args.lab_decoy
    FDRlvl = args.fdr
    typeXCorr = args.type_xcorr
    JumpsAreas = args.jump_areas
    Expt = args.expt.split(",")
    Expt.sort()
    logging.debug(Expt)

  
    logging.info("extract the list of files from the given experiments")
    infiles_aux = glob.glob( os.path.join(inputfolder,"*_PSMs.txt"), recursive=True )
    infiles = [ f for f in infiles_aux if any(x in os.path.splitext(f)[0] for x in Expt) ]
    logging.debug(infiles)


    logging.info("pre-processing the data: assign target-decoy, correct monoisotopic mass, calculate cXCorr")
    ddf = dd.from_delayed([delayed(preProcessing) (file, Expt, deltaMassThreshold, tagDecoy, JumpsAreas) for file in infiles])


    logging.info("create modifications dictionary from xml-doc of UNIMOD")
    modifications = create_modifications(ddf)
    logging.debug(modifications)


    logging.info("processing the data dividing by experiments")
    with Client(n_workers=args.n_workers) as client:
        ddf = ddf.set_index('Experiment')
        Exptr=Expt+[Expt[-1]] # I don´t know why but we have to repeat the last experiment in the list for the repartition
        ddf = ddf.repartition(divisions=Exptr)

        logging.info("map partitions")
        ddf = ddf.map_partitions(pro, typeXCorr, FDRlvl, modifications, tagDecoy, Expt)
        # ddf = d.compute()
        # ddf.to_csv( args.outfile, sep="\t")

        logging.info('print output file')
        outfiles = []
        for e in Expt:
            outdir_exp = args.outdir+"/"+e
            if not os.path.exists(outdir_exp):
                os.makedirs(outdir_exp, exist_ok=False)
            outfiles.append(outdir_exp+"/ID.tsv")
        logging.debug( outfiles )
        ddf.to_csv( outfiles, sep="\t", line_terminator='\n')

        ddf.compute()


    logging.info("remove temporal directory")
    tmp_dir = "{}/{}".format(os.getcwd(), 'dask-worker-space')
    shutil.rmtree(tmp_dir)






if __name__ == "__main__":
    # parse arguments
    parser = argparse.ArgumentParser(
        description='Calculate the FDR',
        epilog='''
        Example:
            python fdr.py -i tests/pratio/Tissue_10ppm  -e "TMTHF" -l "DECOY_" -o tests/pratio/Tissue_10ppm

        ''')
    parser.add_argument('-w',  '--n_workers', type=int, default=2, help='Number of threads/n_workers (default: %(default)s)')
    parser.add_argument('-i',  '--indir', required=True, help='Input directory')
    parser.add_argument('-e',  '--expt', required=True, type=str, help='String with the list of Experiments separated by comma')
    parser.add_argument('-f',  '--fdr', type=float, default=0.01, help='FDR value (default: %(default)s)')
    parser.add_argument('-x',  '--type_xcorr', type=str, choices=['XCorr','cXCorr'], default='XCorr', help='Calculate FDR from the type of XCorr (default: %(default)s)')
    parser.add_argument('-t',  '--threshold', type=int, default=20, help='Threshold of delta mass (default: %(default)s)')
    parser.add_argument('-j',  '--jump_areas', type=int, choices=[1,3,5], default=5, help='Number of jumps [1,3,5] (default: %(default)s)')
    parser.add_argument('-l',  '--lab_decoy', required=True, help='Label of decoy sequences in the db file')
    parser.add_argument('-o',  '--outdir',   required=True, help='Output directory')
    parser.add_argument('-v', dest='verbose', action='store_true', help="Increase output verbosity")
    args = parser.parse_args()

    # logging debug level. By default, info level
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG,
                            format='%(asctime)s - %(levelname)s - %(message)s',
                            datefmt='%m/%d/%Y %I:%M:%S %p')
    else:
        logging.basicConfig(level=logging.INFO,
                            format='%(asctime)s - %(levelname)s - %(message)s',
                            datefmt='%m/%d/%Y %I:%M:%S %p')

    # start main function
    logging.info('start script: '+"{0}".format(" ".join([x for x in sys.argv])))
    main(args)
    logging.info('end script')