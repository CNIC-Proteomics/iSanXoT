#!/usr/bin/python

# import modules
import pandas as pd

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
def preprocessing_data(df):
    '''
    Pre-processing the data
    '''
    # rename columns for Quant module
    df.rename(columns={
        'scannum': 'Scan',
    }, inplace=True)
    return df


def targetdecoy(df, tagDecoy, sep):
    '''
    Assing target and decoy proteins
    '''    
    z = list(df["protein"].str.split(sep))
    p = [(all(tagDecoy  in item for item in i )) if type(i) is list else True for i in z]
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

def preProcessing(df, deltaMassThreshold, tagDecoy, JumpsAreas):
    '''
    Pre-processing the data: assign target-decoy, correct monoisotopic mass
    '''
    # pre-processing input df
    df = preprocessing_data(df)
    # assing target and decoy proteins
    df["T_D"] = targetdecoy(df, tagDecoy, ";")
    df = df[df["hit_rank"] == 1 ]
    # correct monoisotopic mass
    df["JDeltaM [ppm]"],df["JDeltaM"] = Jumps(df, JumpsAreas)
    df = df[ df["JDeltaM [ppm]"].abs() <= deltaMassThreshold ]
    return df



if __name__ == "__main__":
	print("It is a library used by SanXoT and its adaptor modules")
    