#!/usr/bin/python

# import modules
import pandas as pd
import re
import itertools


###################
# Local functions #
###################
def parser_protein_acessions(prot):
    p=list(prot)
    p=[re.sub(r".*(\|(.*?)\|).*", r'\2', i) for i in p]
    return p

def processing_infiles(file, Expt):
    '''
    Pre-processing the data:
    - rename columns
    - add needed columns
    '''    
    # read input file
    df = pd.read_csv(file, sep="\t")
    # add Experiment column
    df["Experiment"] = Expt
    # rename columns
    df.rename(columns={
        'scannum':           'Scan',
        'hit_rank':          'Search Engine Rank',
        'charge':            'Charge',
        'peptide':           'Sequence',
        'protein':           'Protein Accessions',
        'modification_info': 'Modifications'
    }, inplace=True)
    # add the Spectrum File column from the input file name
    df["Spectrum_File"] = file.split(".")[0]
    # TODO!! we have to think in the Protein Accessions columns between the different search engines
    # df["Protein Accessions"]=parser_protein_acessions(df["Protein Accessions"])
    return df

def targetdecoy(df, tagDecoy, sep):
    '''
    Assing target and decoy proteins
    '''    
    z = list(df["Protein Accessions"].str.split(sep))
    p = [(all(tagDecoy  in item for item in i )) for i in z]
    r = [0 if i==True else 1 for i in p]
    return r

def Jumps(df, JumpsAreas):
    '''
    Correct monoisotopic mass
    '''
    h_mass=1.00727647

    s1=(df["massdiff"]/(df["calc_neutral_pep_mass"]+h_mass))*1e6
    s2=(df["massdiff"]-1.0033)/(df["calc_neutral_pep_mass"]+h_mass)*1e6
    s3=(df["massdiff"]+1.0033)/(df["calc_neutral_pep_mass"]+h_mass)*1e6
    s4=(df["massdiff"]-2*1.0033)/(df["calc_neutral_pep_mass"]+h_mass)*1e6
    s5=(df["massdiff"]+2*1.0033)/(df["calc_neutral_pep_mass"]+h_mass)*1e6
    df1 = pd.DataFrame( {"1":s1,"2":s2,"3":s3,"4":s4,"5":s5 })
        
    Deltamass=df1.iloc[:, 0:JumpsAreas] .abs().min(axis=1)
    
    x = list( zip(s1,s2,s3,s4,s5) )

    return Deltamass,x

def preProcessing(file, deltaMassThreshold, tagDecoy, JumpsAreas):
    '''
    Pre-processing the data: assign target-decoy, correct monoisotopic mass
    '''    
    # read input file
    df = pd.read_csv(file, sep="\t", comment='#')
    # assing target and decoy proteins
    df["T_D"] = targetdecoy(df, tagDecoy, ";")
    df = df[df["Search Engine Rank"] == 1 ]
    # correct monoisotopic mass
    df["JDeltaM [ppm]"],df["JDeltaM"] = Jumps(df, JumpsAreas)
    df = df[ df["JDeltaM [ppm]"].abs() <= deltaMassThreshold ]
    return df

def SequenceMod(df):
    '''
    Create a sequence with modifications
    '''
    s=list(df["Modifications"].fillna("0A").replace({'N-term(.+?)\)':'0A',"\(":"[","\)":"]",",":"",'([A-Z])':";"},regex=True).str.split(" ") ) 
    s=[[a.split(";") for a in i]for i in s]
    sn=[[a for a,b in i]for i in s]
    si=[[b for a,b in i]for i in s]
    sn=[list(filter(None,i)) for i in sn]
    sn=[[int(i) for i in j]for j in sn]
    [[a.insert(0,0) ]for a in sn]
    l=list(df["Sequence"])
    f=[[a[i:j]for i,j in zip(b,b[1:]+[None])] for a,b in zip(l,sn)]
    x=["".join(list(itertools.chain.from_iterable(list(itertools.zip_longest(i,j,fillvalue=''))))) for i,j in list(zip(f,si))]
    return x



if __name__ == "__main__":
	print("It is a library used by preSanXoT and its satellite module")
    