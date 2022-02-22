#!/usr/bin/python

# import modules
import os
import pandas as pd
import itertools

###################
# Local variables #
###################
COLS_NEEDED = ['scannum','hit_rank','charge','peptide','modification_info','protein']
COLS_NEEDED_acid = [
    'hit_rank', # for preProcessing func.
    'protein', # for tagDecoy func.
    'massdiff', # for Jump func.
    'calc_neutral_pep_mass', # for Jump func.
    'peptide', # for createPeptideId func.
    'modification_info' # for createPeptideId func.
    ]



###################
# Local functions #
###################
def createPeptideId(df):
    '''
    Create a peptide id using the sequence and modifications
    '''
    s=list(df["modification_info"].fillna("0A").replace({'N-term(.+?)\)':'0A',"\(":"[","\)":"]",",":"",'([A-Z])':";"},regex=True).str.split(" ") ) 
    s=[[a.split(";") for a in i]for i in s]
    sn=[[a for a,b in i]for i in s]
    si=[[b for a,b in i]for i in s]
    sn=[list(filter(None,i)) for i in sn]
    sn=[[int(i) for i in j]for j in sn]
    [[a.insert(0,0) ]for a in sn]
    l=list(df["peptide"])
    f=[[a[i:j]for i,j in zip(b,b[1:]+[None])] for a,b in zip(l,sn)]
    x=["".join(list(itertools.chain.from_iterable(list(itertools.zip_longest(i,j,fillvalue=''))))) for i,j in list(zip(f,si))]
    return x

def processing_infiles(file, Expt):
    '''
    Pre-processing the data:
    - rename columns
    - add needed columns
    '''    
    # read input file
    df = pd.read_csv(file, sep="\t", comment='#')
    # add Experiment column
    df["Experiment"] = Expt
    # add the Spectrum File column from the input file name
    df["Spectrum_File"] = os.path.basename(file)
    # rename columns for Quant module
    df.rename(columns={
        'scannum': 'Scan',
    }, inplace=True)
    # create Scan_Id
    df["Scan_Id"] = df["Spectrum_File"].replace('\.[^$]*$', '', regex=True) + '-' + df["Scan"].map(str) + '-' + df["charge"].map(str)
    # create Peptide_Id
    df["Peptide_Id"] = createPeptideId(df)
    return df

def targetdecoy(df, tagDecoy, sep):
    '''
    Assing target and decoy proteins
    '''    
    z = list(df["protein"].str.split(sep))
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
    df = df[df["hit_rank"] == 1 ]
    # correct monoisotopic mass
    df["JDeltaM [ppm]"],df["JDeltaM"] = Jumps(df, JumpsAreas)
    df = df[ df["JDeltaM [ppm]"].abs() <= deltaMassThreshold ]
    return df



if __name__ == "__main__":
	print("It is a library used by SanXoT and its adaptor modules")
    