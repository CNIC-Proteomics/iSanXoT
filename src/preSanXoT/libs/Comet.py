#!/usr/bin/python

# import modules
import pandas as pd
import re


###################
# Local functions #
###################
def parser_protein_acessions(prot):
	p=list(prot.replace(",",";",regex=True).str.split(";"))
	p=[";".join(re.sub(r".*(\|(.*?)\|).*", r'\2', i)) for i in p]
	return p

def processing_infiles(file, Expt):
    '''
    Pre-processing the data: assign target-decoy, correct monoisotopic mass, calculate cXCorr
    '''    
    # read input file
    df = pd.read_csv(file, sep="\t")
    # add Experiment column
    df["Experiment"] = Expt
    # rename columns
    df.rename(columns={
        'scan': 'Scan',
        "num": 'Search Engine Rank',
        'charge': 'Charge',
        "xcorr": "XCorr",
        "plain_peptide": 'Sequence',
        "protein": 'Protein Accessions'
    }, inplace=True)
    # add the Spectrum File column from the input file name
    df["Spectrum_File"] = file.split(".")[0]
    # TODO!! we have to think in the Protein Accessions columns between the different search engines
    # df["Protein Accessions"]=parser_protein_acessions(df["Protein Accessions"])
    return df

if __name__ == "__main__":
	print("It is a library used by preSanXoT and its satellite module")
    