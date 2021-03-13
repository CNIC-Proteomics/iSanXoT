#!/usr/bin/python

# import modules
import pandas as pd
import numpy as np
import itertools


###################
# Local functions #
###################
def cXCorr(df):
    '''
    Calculate cXCorr
    '''
    rc=np.where(df['Charge']>=3, '1.22', '1').astype(float)
    cXCorr1= np.log(df['XCorr']/rc)/np.log(2*df['Sequence'].str.len())
    return cXCorr1

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
        'MHplus in Da': 'MH+ [Da]',
        'Theo MHplus in Da': 'Theo. MH+ [Da]',
        'Delta M in ppm': 'DeltaM [ppm]',
        'Spectrum File': 'Spectrum_File',
        'First Scan': 'Scan'
    }, inplace=True)
    # delete suffix value    
    df["Spectrum_File"] = df["Spectrum_File"].replace('\.[^$]*$', '', regex=True)
    # create Scan_Id
    df["Scan_Id"] = df["Spectrum_File"].map(str) + '-' + df["Scan"].map(str) + '-' + df["Charge"].map(str)
    # calculate cXCorr
    df["cXCorr"] = cXCorr(df)
    # delete suffix in the headers coming from PD 2.3
    # delete # in the headers
    col = list(df.columns.values)
    col[:] = [s.replace('Abundance: ', '').replace('# ', '') for s in col]
    df.columns = col
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

def SequenceMod(df, mods):
    '''
    Create a sequence with modifications
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


if __name__ == "__main__":
	print("It is a library used by preSanXoT and its satellite module")