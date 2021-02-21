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
    # delete suffix in the headers coming from PD 2.3
    col = list(df.columns.values)
    col[:] = [s.replace('Abundance: ', '') for s in col]
    df.columns = col
    return df

if __name__ == "__main__":
	print("It is a library used by preSanXoT and its satellite module")