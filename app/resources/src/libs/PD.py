#!/usr/bin/python

# import modules
import pandas as pd
import numpy as np

###################
# Local variables #
###################
COLS_NEEDED = ['Spectrum File','First Scan','Sequence','Modifications','Protein Accessions','Protein Descriptions']
COLS_NEEDED_acid = [
    'Search Engine Rank', # for preProcessing func.
    'DeltaM [ppm]', # for Jump func.
    'Theo. MH+ [Da]', # for Jump func.
    'MH+ [Da]', # for Jump func.
    'Sequence', # for SequenceMod func.
    'Modifications', # for SequenceMod func.
    'Protein Accessions', # for tagDecoy func.
    'Protein Descriptions'
    ]


###################
# Local functions #
###################
def preprocessing_data(df):
    '''
    Pre-processing the data:
    - rename columns
    '''    
    # rename columns
    df.rename(columns={
        # for older version (PD 2.1, 2.2, 2.3)
        'MHplus in Da': 'MH+ [Da]',
        'Theo MHplus in Da': 'Theo. MH+ [Da]',
        'Delta M in ppm': 'DeltaM [ppm]',
    }, inplace=True)
    # add columns for Quant module
    df['Scan'] = df['First Scan']
    return df

def targetdecoy(df, tagDecoy, sep):
    '''
    Assing target and decoy proteins
    '''    
    z = list(df["Protein Accessions"].str.split(sep))
    p = [(all(tagDecoy  in item for item in i )) if type(i) is list else True for i in z]
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

def preProcessing(df, deltaMassThreshold, tagDecoy, JumpsAreas):
    '''
    Pre-processing the data: assign target-decoy, correct monoisotopic mass
    '''
    # pre-processing input df
    df = preprocessing_data(df)
    # calculate cXCorr
    df["cXCorr"] = cXCorr(df)
    # assing target and decoy proteins
    df["T_D"] = targetdecoy(df, tagDecoy, ";")
    df = df[df["Search Engine Rank"] == 1 ]
    # correct monoisotopic mass
    df["JDeltaM [ppm]"],df["JDeltaM"] = Jumps(df, JumpsAreas)
    df = df[ df["JDeltaM [ppm]"].abs() <= deltaMassThreshold ]
    return df



if __name__ == "__main__":
	print("It is a library used by SanXoT and its adaptor modules")