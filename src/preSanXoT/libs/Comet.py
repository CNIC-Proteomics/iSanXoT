#!/usr/bin/python

# import modules
import os
import pandas as pd
import numpy as np
import re
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

def parser_protein_acessions(prot):
    '''
    Parse the protein description if it comes from UniProt (SwissProt and TrEMBL)
    '''
    p = list(prot.replace(",",";",regex=True).str.split(";"))
    p = [";".join([ re.sub(r".*(\|(.*?)\|).*", r'\2', i) if re.match(r'^[sp|tr]', i) else i for i in x]) for x in p]
    return p

def processing_infiles(file, Expt):
    '''
    Pre-processing the data:
    - rename columns
    - add needed columns
    '''    
    # read input file
    df = pd.read_csv(file, sep="\t", skiprows=1)
    # add Experiment column
    df["Experiment"] = Expt
    # rename columns
    df.rename(columns={
        'scan':          'Scan',
        'num':           'Search Engine Rank',
        'charge':        'Charge',
        'xcorr':         'XCorr',
        'plain_peptide': 'Sequence',
        'modifications': 'Modifications'
    }, inplace=True)
    # add the Spectrum File column from the input file name
    df["Spectrum_File"] = os.path.basename(file)
    # create Scan_Id
    df["Scan_Id"] = df["Spectrum_File"].replace('\.[^$]*$', '', regex=True) + '-' + df["Scan"].map(str) + '-' + df["Charge"].map(str)
    # calculate cXCorr
    df["cXCorr"] = cXCorr(df)
    # parse the protein description
    df["Protein_Accessions"] = parser_protein_acessions(df["protein"])
    # add the protein description
    df["Protein_Descriptions"] = df["protein"]
    # In the case of duplicated scans, we take the scans with the best cXCorr and if the xcore is duplicated we then get the first one.
    # move the Scan_Id to the last column
    df = df.sort_values(by=["Scan_Id","cXCorr","Protein_Accessions"], ascending=[True, False, False]) \
        .groupby(["Scan_Id"], sort=False) \
        .first() \
        .reset_index()
    c = list(df.columns)
    c = c[1:] + [c[0]]
    df = df[c]
    return df

def targetdecoy(df, tagDecoy, sep):
    '''
    Assing target and decoy proteins
    '''    
    z = list(df["Protein_Accessions"].str.split(sep))
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

def preProcessing(file, deltaMassThreshold, tagDecoy, JumpsAreas):
    '''
    Pre-processing the data: assign target-decoy, correct monoisotopic mass
    '''    
    # read input file
    df = pd.read_csv(file, sep="\t", comment='#')
    # assing target and decoy proteins
    df["T_D"] = targetdecoy(df, tagDecoy, ",")
    df = df[df["Search Engine Rank"] == 1 ]
    # correct monoisotopic mass
    df["JDeltaM [ppm]"],df["JDeltaM"] = Jumps(df, JumpsAreas)
    df = df[ df["JDeltaM [ppm]"].abs() <= deltaMassThreshold ]
    return df

def SequenceMod(df):
    '''
    Create a sequence with modifications
    '''
    s=list(df["Modifications"].fillna("0A").fillna("0_A_").replace({'^.*_n':'0_A_','_[A-Z]_':";"},regex=True).str.split(",") ) 
    s=[[a.split(";") for a in i]for i in s]
    sn=[[a for a,b in i]for i in s]
    si=[["["+b+"]" if b!="" else b for a,b in i]for i in s]
    sn=[list(filter(None,i)) for i in sn]
    sn=[[int(i) for i in j]for j in sn]
    [[a.insert(0,0) ]for a in sn]
    l=list(df["Sequence"])
    f=[[a[i:j]for i,j in zip(b,b[1:]+[None])] for a,b in zip(l,sn)]
    x=["".join(list(itertools.chain.from_iterable(list(itertools.zip_longest(i,j,fillvalue=''))))) for i,j in list(zip(f,si))]
    return x


if __name__ == "__main__":
	print("It is a library used by preSanXoT and its satellite module")
    