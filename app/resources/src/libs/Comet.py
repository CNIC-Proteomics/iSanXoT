#!/usr/bin/python

# import modules
import pandas as pd
import numpy as np
import re

###################
# Local variables #
###################
COLS_NEEDED = ['scan','num','charge','xcorr','plain_peptide','modifications','protein']
COLS_NEEDED_acid = [
    'num', # for preProcessing func.
    'protein', # for tagDecoy func.
    'exp_neutral_mass', # for Jump func.
    'calc_neutral_mass', # for Jump func.
    'plain_peptide', # for createPeptideId func.
    'modifications' # for createPeptideId func.
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
        'scan': 'Scan',
    }, inplace=True)
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
    
    s1=(df["exp_neutral_mass"]-df["calc_neutral_mass"])/(df["calc_neutral_mass"]+h_mass)*1e6
    s2=((df["exp_neutral_mass"]-df["calc_neutral_mass"])-1.0033)/(df["calc_neutral_mass"]+h_mass)*1e6
    s3=((df["exp_neutral_mass"]-df["calc_neutral_mass"])+1.0033)/(df["calc_neutral_mass"]+h_mass)*1e6
    s4=((df["exp_neutral_mass"]-df["calc_neutral_mass"])-2*1.0033)/(df["calc_neutral_mass"]+h_mass)*1e6
    s5=((df["exp_neutral_mass"]-df["calc_neutral_mass"])+2*1.0033)/(df["calc_neutral_mass"]+h_mass)*1e6
    df1 = pd.DataFrame( {"1":s1,"2":s2,"3":s3,"4":s4,"5":s5 })

    Deltamass=df1.iloc[:, 0:JumpsAreas] .abs().min(axis=1)
    
    x = list( zip(s1,s2,s3,s4,s5) )

    return Deltamass,x

def cXCorr(df):
    '''
    Calculate cXCorr
    '''
    rc=np.where(df['charge']>=3, '1.22', '1').astype(float)
    cXCorr1= np.log(df['xcorr']/rc)/np.log(2*df['plain_peptide'].str.len())
    return cXCorr1

def parser_protein_acessions(prot):
    '''
    Parse the protein description if it comes from UniProt (SwissProt and TrEMBL)
    '''
    p = list(prot.replace(",",";",regex=True).str.split(";"))
    p = [";".join([ re.sub(r".*(\|(.*?)\|).*", r'\2', i) if re.match(r'^[sp|tr]', i) else i for i in x]) for x in p]
    return p

def parser_protein_descriptions(prot):
    '''
    Parse the protein description replaciong the "," to ";"
    '''
    p = prot.replace(",",";",regex=True)
    return p

def preProcessing(df, deltaMassThreshold, tagDecoy, JumpsAreas):
    '''
    Pre-processing the data: assign target-decoy, correct monoisotopic mass
    '''
    # pre-processing input df
    df = preprocessing_data(df)
    # create Scan_Id
    df["Scan_Id"] = df["Spectrum_File"].replace('\.[^$]*$', '', regex=True) + '-' + df["Scan"].map(str) + '-' + df["charge"].map(str)
    # calculate cXCorr
    df["cXCorr"] = cXCorr(df)
    # In the case of duplicated scans, we take the scans with the best cXCorr and if the xcore is duplicated we then get the first one.
    # move the Scan_Id to the last column
    df = df.sort_values(by=["Scan_Id","cXCorr","protein"], ascending=[True, False, False]) \
        .groupby(["Scan_Id"], sort=False) \
        .first() \
        .reset_index()
    c = list(df.columns)
    c = c[1:] + [c[0]]
    df = df[c]
    # assing target and decoy proteins
    df["T_D"] = targetdecoy(df, tagDecoy, ",")
    df = df[df["num"] == 1 ]
    # correct monoisotopic mass
    df["JDeltaM [ppm]"],df["JDeltaM"] = Jumps(df, JumpsAreas)
    df = df[ df["JDeltaM [ppm]"].abs() <= deltaMassThreshold ]
    return df



if __name__ == "__main__":
	print("It is a library used by SanXoT and its adaptor modules")
    