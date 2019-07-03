import sys
import os
import pandas
import numpy
import re
from Bio import SeqIO


class builder:
    '''
    Builder class
    '''
    # def __init__(self, infile, nworkers):
    #     '''
    #     Converter builder
    #     '''
    #     # for evidences.txt file (MaxQuant)
    #     self.df = pandas.read_csv(infile, usecols=['Modified sequence','Experiment','Raw file','MS/MS scan number','Charge','Proteins','Intensity'], sep="\t", low_memory=False)        

    def __init__(self, infile, nworkers):
        '''
        Converter builder
        '''
        # for modificationSpecificPeptides.txt file (MaxQuant)
        self.df = pandas.read_csv(infile, sep="\t", na_values = [0], low_memory=False)
        r = re.compile(r'Sequence|Modifications|Proteins|Gene Names|Protein Names|Charges|MS/MS scan number|Raw file|Intensity ')
        lst = [value for value in self.df.columns.values if r.search(value)]
        self.df = self.df[lst]
        self.df.columns = self.df.columns.str.replace('Intensity ', '')
        self.df.columns = self.df.columns.str.replace('\s+', '_', regex=True)

    def evidence2idq(self):
        '''
        Converter the evidence file from MaXQuant to ID-q (label-free result)        
        '''
        # extract the intensity and their proteins for experiment based on sequence
        # handle the unique values...
        df = self.df.groupby(['Modified sequence','Experiment','MS/MS scan number']).agg({
            'Proteins': 'unique',            
            'Intensity': 'first'
        })
        df['Proteins'] = df['Proteins'].apply(numpy.array2string)
        df['Proteins'] = df['Proteins'].replace(to_replace=r'^\[', value='', regex=True)
        df['Proteins'] = df['Proteins'].replace(to_replace=r'\]$', value='', regex=True)
        df['Proteins'] = df['Proteins'].replace(to_replace=r'\'\s+\'', value='\';\'', regex=True)
        df['Proteins'] = df['Proteins'].replace(to_replace=r'\'', value='', regex=True)
        df['Proteins'] = df['Proteins'].apply( lambda x: ';'.join(sorted(x.split(';'))) )
        # pivot table
        df3 = df.pivot_table(index=['Modified sequence','MS/MS scan number','Proteins'], columns=['Experiment','MS/MS scan number'], values='Intensity')
        df3.reset_index(inplace=True)
        # create  unique value for sequence
        idx = df3.index.map(str)+"_"+df3['Modified sequence']
        df3.insert(loc=0, column='SeqId', value=idx)
        return df3

    def modificationSpecificPeptides2idq(self, df=None):
        '''
        Converter the evidence file from MaXQuant to ID-q (label-free result)        
        '''        
        df = self.df if df is None else df
        # join type of modifications to the sequence
        df['Modifications'].replace('\s*','', regex=True, inplace=True)
        df['Modifications'].replace('Unmodified','', regex=True, inplace=True)
        s = df['Sequence']+"_"+df['Modifications']
        s = s.replace('\_$','',regex=True)
        df.insert(loc=0, column='SequenceMod', value=s)
        # replace 0 to empty
        df.replace('0','', regex=False, inplace=True)
        # create  unique value for sequence
        idx = df.index.map(str)+"_"+df['SequenceMod']
        df.insert(loc=0, column='SeqId', value=idx)
        # retrieve the first protein of list
        prot  = df['Proteins'].apply( lambda x: sorted(x.split(';'))[0] if isinstance(x, str) and x != '' else '')
        df.insert(loc=4, column='Protein', value=prot)
        return df

    def _species_report(self, dbfile):
        '''
        Create a report with the FASTA sequence ()
        '''
        out = {}
        for seq_record in SeqIO.parse(dbfile, "fasta"):
            idx  = seq_record.id
            desc = seq_record.description
            species = None
            if desc.startswith('sp') or desc.startswith('tr'): # UniProt case
                match = re.search(r'[^\|]*\|([^\|]*)\|', desc, re.I | re.M)
                idx = match[1]
                match = re.search(r'OS=(\w+\s+\w+)', desc, re.I | re.M)
                species = match[1] if match else None
            if species:
                out[idx] = species
        return out

    def addSpecies(self, dbfile, df=None):
        '''
        Add organism column from database based on the protein column
        '''
        df = self.df if df is None else df
        prot  = df['Proteins'].values
        # create a dictionary with the protein_id => desc,species,...
        db_rep = self._species_report(dbfile)
        # add species into column
        species = df['Protein'].apply( lambda x: db_rep[x] if x in db_rep else '')
        df.insert(loc=7, column='Species', value=species)
        return df


    def to_csv(self, df, outfile):
        '''
        Print to CSV
        '''
        if df is not None:
            df.to_csv(outfile, sep="\t", index=False)

