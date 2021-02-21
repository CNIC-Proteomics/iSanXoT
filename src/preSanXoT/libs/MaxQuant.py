#!/usr/bin/python

# import modules
import pandas as pd


###################
# Local functions #
###################

def processing_infiles(file, Expt):
    '''
    Pre-processing the data: assign target-decoy, correct monoisotopic mass, calculate cXCorr
    '''    
    # read input file
    df = pd.read_csv(file, sep="\t")
    # add Experiment column
    df["Experiment"] = Expt
    # rename Intensity columns
    df.columns = df.columns.str.replace('Intensity\s+', '')
    # join type of modifications to the sequence
    s = df['Sequence'] +"_"+ df['Modifications']
    s = s.replace('\_Unmodified$','',regex=True)
    s = s.replace('\s*','', regex=True)
    df["SequenceMod"] = s
    # add unique value for sequence
    idx = df.index.map(str)+"_"+df['SequenceMod']
    df["SeqId"] = idx
    # replace 0 to empty in the whole input dataframe
    df.replace('0','', regex=False, inplace=True)
    # retrieve the first protein of list
    prot  = df['Proteins'].apply( lambda x: sorted(x.split(';'))[0] if isinstance(x, str) and x != '' else '')
    df['Protein'] = prot
    return df

if __name__ == "__main__":
	print("It is a library used by preSanXoT and its satellite module")
    