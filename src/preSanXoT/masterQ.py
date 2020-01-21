#!/usr/bin/python

# import global modules
import os
import sys
import argparse
import logging
import pandas
import numpy as np
import re
import itertools
from Bio import SeqIO



# Module metadata variables
__author__ = "Jose Rodriguez"
__credits__ = ["Jose Rodriguez", "Jesus Vazquez"]
__license__ = "Creative Commons Attribution-NonCommercial-NoDerivs 4.0 Unported License https://creativecommons.org/licenses/by-nc-nd/4.0/"
__version__ = "1.0.1"
__maintainer__ = "Jose Rodriguez"
__email__ = "jmrodriguezc@cnic.es"
__status__ = "Development"

INCOLS = ['SequenceMod', 'Protein', 'Protein_Redundancy', 'Protein_Descriptions']


class corrector:
    '''
    Make the calculations in the workflow
    '''
    def __init__(self, infile, species=None, pretxt=None, indb=None, incols=None):
        # create species filter
        self.species = species
        # create preferenced text
        self.pretxt = pretxt
        # create an index from the fasta sequence, if apply
        self.indb = None        
        if indb is not None:
            # get the index of proteins: for UniProt case!! (key_function)
            self.indb = SeqIO.index(indb, "fasta", key_function=lambda rec : rec.split("|")[1])
        # read infile
        self.indat = pandas.read_csv(infile, sep="\t", na_values=['NA'], low_memory=False)
        # get the list of columns
        if incols is not None:
            cols = incols.strip(' ').split(",")
        else:
            cols = INCOLS
        df = self.indat[cols]
        # create the report with the peptides and proteins
        [self.peptides, self.proteins] = self.get_reports(df, incols)


    def _extract_proteins_species(self, in_ids, seq, peptides):
        '''
        Create reaport with the list of hits (proteins mostly).
        Input:
            Array with three elements:
            1. Main id
            2. Redundances ids
            3. (Optional) Descriptions of Main id and Redundances ids
        '''        
        ids,desc = [],[]
        prot_ids = {}
        if len(in_ids) > 0: # discard NaN values
            # extract hits: main+redundances            
            ids.append(in_ids[0])            
            if len(in_ids) >= 2 and in_ids[1] != "":
                ids = ids + in_ids[1].split(";")
            # extract descriptions, if apply
            if len(in_ids) >= 3 and in_ids[2] != "":
                desc = in_ids[2].split(";")
            # create report for the protein adding the description from the FASTA file
            for i, p_id in enumerate(ids):
                if p_id != "" and p_id in self.indb:
                    p_dsc = ">"+self.indb[p_id].description
                    p_db = self.indb[p_id].name.split("|")[0]
                    p_len = len(self.indb[p_id].seq)
                    if p_id not in peptides[seq]['proteins']:
                        peptides[seq]['proteins'][p_id] = { 'id': p_id, 'dsc': p_dsc, 'db': p_db, 'len': p_len, 'scans': 1}
                        prot_ids[p_id] = { 'id': p_id, 'dsc': p_dsc, 'db': p_db, 'len': p_len }
                    else:
                        peptides[seq]['proteins'][p_id]['scans'] += 1
                    # extract species
                    # UniProt match
                    sp = re.search(r'OS=(\w* \w*)', p_dsc, re.I | re.M)
                    if sp:
                        sp = sp.group(1)
                        if sp not in peptides[seq]['species']:
                            peptides[seq]['proteins'][p_id]['species'] = sp
                            peptides[seq]['species'].append( sp )
                else:
                    sys.exit("ERROR: we don't find '{}' in the FASTA file!".format(p_id))

        return prot_ids

    def get_reports(self, df, incols):
        '''
        Create the report with the protein values
        '''
        peptides = {}
        proteins = {}
        # rename columns
        # if existe the last column of descripts
        df.rename(columns={
            df.columns[0]: "Sequence",
            df.columns[1]: "Hit",
            df.columns[2]: "Redundances",
            '[Tags]': 'Tags'
        }, inplace=True)
        if len(df.columns) >= 3:
            df.rename(columns={
                df.columns[3]: "Descriptions"
            }, inplace=True)
        # extract the peptide and proteins info for each line
        for row in df.itertuples():
            if ( isinstance(row.Sequence, str) and isinstance(row.Hit, str) and isinstance(row.Redundances, str) ):
                # get rows
                # if exists, get the descriptions row
                pep_lpp = 1 # HARD CORE!!! row.LPP 
                pep_seq = row.Sequence.replace(" ", "")
                pep_p_dsc = []
                pep_p_dsc.append(row.Hit)
                pep_p_dsc.append(row.Redundances)                
                if 'Descriptions' in df.columns:
                    pep_p_dsc.append(row.Descriptions)
                pep_tags = None
                if 'Tags' in df.columns:
                    pep_tags = row.Tags

                # init variables
                if pep_seq not in  peptides:
                    peptides[pep_seq] = {
                        'proteins': {},
                        'tags':     {},
                        'species':  []
                    }
                # add the proteins to the peptide and return the list of protein
                # increase the number of scan for the peptides
                pep_prots = self._extract_proteins_species(pep_p_dsc, pep_seq, peptides)
                # save the proteins from peptide.
                # the peptide should be unique
                for pid, pep_prot in pep_prots.items():
                    pdsc = pep_prot['dsc']
                    if pid not in proteins:
                        # init LPQ with the first LPP
                        # with the first peptide
                        proteins[pid] = { 'LPQ': pep_lpp, 'desc': pdsc, 'pep': {pep_seq: 1} }
                        if 'db' in pep_prot:
                            proteins[pid]['db'] = pep_prot['db']
                        if 'len' in pep_prot:
                            proteins[pid]['len'] = pep_prot['len']
                    else:
                        # check if the peptide is unique
                        # LPQ: Sum of LPP's peptides
                        if pep_seq not in proteins[pid]['pep']:
                            proteins[pid]['pep'][pep_seq] = 1
                            proteins[pid]['LPQ'] += pep_lpp
                        else:
                            proteins[pid]['pep'][pep_seq] += 1
        return [peptides, proteins]

    def _unique_protein_decision(self, prots):
        '''
        Take an unique protein based on
        '''
        decision = 0
        hprot = None
        # 1. the preferenced text, if apply
        if self.pretxt is not None:
            # know how many proteins match to the list of regexp
            for pretxt in self.pretxt:
                if pretxt == 'sp' or pretxt == 'tr': # get proteins in SwissProt or TrEMBL
                    pmat = list( filter( lambda x: 'db' in x and x['db'] == pretxt, prots) )
                    print( pmat )
                else: # another kind of regular expression
                    pmat = list( filter( lambda x: re.match(r'.*'+pretxt+'.*', x['dsc'], re.I | re.M), prots) )
                # keep the matches                
                if pmat is not None and len(pmat) > 0 :
                    prots = pmat
                    # if there is only one protein, we found
                    if len(pmat) == 1:
                        hprot = pmat[0]
                        decision = 1
        
        # 2. Take the sorted sequence, if apply
        if (decision == 0) and (self.indb is not None):
            # extract the proteins that are in the fasta index
            pmat = list( filter( lambda x: 'len' in x, prots) )
            # sort by length
            pmat.sort(key=lambda x: x['len'])
            # extract the sorted sequence, if it is unique
            if pmat is not None:
                if len(pmat) == 1:
                    hprot = pmat[0]
                    decision = 2
                elif len(pmat) > 1 and pmat[0]['len'] < pmat[1]['len']:
                    hprot = pmat[0]
                    decision = 2                
        
        # 3. Alphabetic order (reverse)
        if decision == 0:
            # sort the proteins
            pmat = sorted(prots, key=lambda x: x['dsc'], reverse=True)
            if pmat is not None:
                hprot = pmat[0]
                decision = 3
        
        return hprot,decision

    def _unique_protein(self, pep_seq, pep_prots):
        scores = {}
        rst = []
        for pid,pep_prot in pep_prots.items():
            pdsc = pep_prot['dsc']
            if self.proteins[pid] and self.proteins[pid]['LPQ']:
                q = self.proteins[pid]
                r = { 'id': pid, 'dsc': pdsc }
                if 'db' in q:
                    r['db'] = q['db']
                if 'len' in q:
                    r['len'] = q['len']
                s = q['LPQ']
                if s not in scores:
                    scores[s] = [r]
                else:
                    scores[s].append(r)
        if scores:
            # get the highest score
            hsc = sorted(scores, reverse=True)[0]
            hprot = scores[hsc]
            hdeci = None
            # if there are more than one protein, we have to make a decision
            if len(hprot) == 1:
                hprot = hprot[0]
                hdeci = -1
            elif len(hprot) > 1:
                hprot,hdeci = self._unique_protein_decision(hprot)
            # create list with the peptide solution
            rst = hprot['dsc']

        return rst,hdeci

    def get_unique_protein(self):
        '''
        Calculate the unique protein from the list of peptides
        '''
        results = []
        results_sprest = []
        # extract the LPQ scores for each protein based on the peptide list
        for pep_seq,pep in sorted( self.peptides.items() ):
            pep_prots = pep['proteins']
            pep_species = pep['species']
            pep_tags = pep['tags']
            # divide the results by species if apply
            hprot = None
            hdeci = None
            hprot_sprest = None
            if (self.species is not None):
                if ( (self.species in pep_species) and (len(pep_species) == 1) ):
                    hprot,hdeci = self._unique_protein(pep_seq, pep_prots)
                else:
                    hprot_sprest,hdeci = self._unique_protein(pep_seq, pep_prots)
            else:
                hprot,hdeci = self._unique_protein(pep_seq, pep_prots)
            if hprot:
                # results.append([pep_seq, hprot, pep_tags])
                results.append([pep_seq, hprot, hdeci])
            if hprot_sprest:
                # results_sprest.append([pep_seq, hprot_sprest, pep_tags])
                results_sprest.append([pep_seq, hprot_sprest, hdeci])
        # create dataframe with the peptide solution        
        self.rst = pandas.DataFrame(results, columns=['SequenceMod', 'MasterQ', 'MasterQ_Tag']) # with the given species
        self.rst_sprest = pandas.DataFrame(results_sprest) # witht the rest of species


    def merge_w_indat(self):
        '''
        Merge with the input data file
        '''
        # merge the dataframes
        if self.rst is not None and not self.rst.empty:
            self.outdat = pandas.merge(self.indat, self.rst, how='outer', on=['SequenceMod'])
        if self.rst_sprest is not None and not self.rst_sprest.empty:
            print( self.rst_sprest )
        # fill with tbe unique proteins
        self.outdat['MasterQ'].fillna(self.outdat['Protein'], inplace=True)
        self.outdat['MasterQ_Tag'].fillna(0, inplace=True)

    def to_csv(self,outfile):
        '''
        Print to file... in principle, in TSV
        '''
        if self.outdat is not None and not self.outdat.empty:
            self.outdat.to_csv(outfile, sep="\t", index=False)






# -------
def add_descriptions(df, indb, tagDecoy):
    '''
    Add the description for the proteins. Extract the genes (with redundances) and species discarding DECOY proteins
    '''
    # local functions
    def get_fasta_desc(qs):
        def _get_desc(q):
            if q in indb:
                return ">"+indb[q].description
            else:
                return q
        b = list(map(_get_desc, qs))
        return b
    def get_protein_len(qs):
        def _get_len(q):
            if q in indb:
                return str(len(indb[q].seq))
            else:
                return '-1'
        b = list(map(_get_len, qs))
        return b
    def _pattern_gene(i):
        m = re.search('GN=([^\s]*)', i)
        r = "'"+m.group(1) if m else '' # Stop automatically changing numbers to dates in Excel
        return r
    def _pattern_species(i):
        m = re.search('OS=([^\s]+\s+[^\s]+)', i)
        r = m.group(1) if m else ''
        return r
    # create a list of tuples with the (ProteinID,ProteinDescription,ProteinLength)
    a = list(df["Protein Accessions"].fillna("").str.split("\s*;\s*"))
    d = list(map(get_fasta_desc, a))
    l = list(map(get_protein_len, a))
    da = [ list(itertools.chain(list(itertools.zip_longest(i,j,k,fillvalue='')))) for i,j,k in list(zip(d,a,l)) ]    
    # sort and discard the DECOY proteins and the proteins without description
    da = [ [i for i in sorted(s) if not (tagDecoy in i[0]) and all(i)] for s in da ]    
    # get a list with the tuple 1 (ProteinDescription)
    p = [ [i[0] for i in s] for s in da ]
    try:
        # from the list of protein description: the first element, and the rest (redundancy)
        pm = [ i[0] for i in p ]
        pr = [ "_||_".join(i[1:]) for i in p ]
        # get the list of protein length
        pl = [ [i[2] for i in s] for s in da ]
        pl = [ ";".join(i) for i in pl ]
        # get the gene from the main protein
        gm = [_pattern_gene(i) for i in pm]
        # get the gene from the protein redundances
        gr = [ [_pattern_gene(i) for i in j.split("_||_")] for j in pr]
        # unique and without empty
        gr = [ list(filter(None, list(set(i)) )) for i in gr]
        gr = [ ";".join(set(i)) for i in gr ]
        # get the list of unique species
        s = [ [_pattern_species(i) for i in j] for j in p ]
        s = [ ";".join(set(i)) for i in s ]
    except Exception as ex:
        sys.exit("ERROR!! The FASTA file does not contain all protein hits: "+str(ex) )
    # return
    return pm,pr,pl,gm,gr,s

def get_num_peptides(df):
    '''
    Create the report with the protein values
    '''
    # create a list with the concatenate of Protein + ProteinRedundancy    
    x = df["Protein"] + "_||_"+ df["Protein_Redundancy"]
    x = x.str.replace(r'\_\|\|\_$', "")
    x = list(x.str.split(r'\_\|\|\_'))
    # create a list with the length of proteins (Protein + ProteinRedundancy)
    y = list(df["Protein_Length"].str.split(";"))
    # create a list of tuples with the (Proteins-all- + ProteinLength-all-
    df.loc[:,'proteins_plus_lengths'] = [ list(map(lambda a,b: str(a)+"_||_"+str(b), i, j)) for i,j in list(zip(x,y)) ]
    # create df with the list of peptides and proteins by row
    lst_cols = 'proteins_plus_lengths'
    df2 = pandas.DataFrame({
            col:np.repeat(df[col].values, df[lst_cols].str.len()) for col in df.columns.drop(lst_cols)
            }).assign(**{lst_cols:np.concatenate(df[lst_cols].values)})
    # group by protein and sum the number of peptides
    df2 = df2.groupby('proteins_plus_lengths')['SequenceMod'].count().reset_index()
    # extract the length
    df2[['Proteins','Lengths']] = df2['proteins_plus_lengths'].str.split("\_\|\|\_" , expand=True)
    # rename and drop
    df2.rename(columns={'SequenceMod': 'num_peptides'}, inplace=True)
    df2.drop(columns=['proteins_plus_lengths'], inplace=True)
#    df2['Lengths'] = df2['Lengths'].astype('int')
    df2['Lengths'] = pandas.to_numeric(df2['Lengths'], errors='coerce')
    # return
    return df2


def _master_decision(prots, pretxt):
    '''
    Take an unique protein based on
    '''
    hprot = None
    decision = 0
    # 1. the preferenced text, if apply
    # How many proteins match to the list of regexp
    # Here we can apply features as Species, type of database (Sw or Tr), etc.
    # If there is only one protein, we found
    # It works in order. Selective
    if pretxt is not None:
        for rtxt in pretxt.split(","):            
            pmat = prots.loc[prots['Proteins'].str.match(r'.*'+rtxt+'.*'),:]            
            if pmat is not None and len(pmat.index) == 1:
                hprot = pmat.iloc[0]['Proteins']
                decision = 1
            elif pmat is not None and len(pmat.index) > 1:
                prots = pmat
    # 2. Take the sorted sequence, if apply
    # Extract the proteins with the minimum lenght of aminoacids
    # If there is only one protein, we found
    # It works in order. Selective
    if hprot is None and decision == 0:
        pmat = prots[prots['Lengths']==prots['Lengths'].min()].dropna(axis=1, thresh=1).dropna()
        if prots is not None and len(prots.index) == 1:
            hprot = prots.iloc[0]['Proteins']
            decision = 2
        elif pmat is not None and len(pmat.index) > 1:
            prots = pmat
    # 3. Alphabetic order
    # Extract the first protein
    if hprot is None and decision == 0:
        prots = prots.sort_values('Proteins')
        prots = prots.iloc[0]
        hprot = prots['Proteins']
        decision = 3
    # return
    return hprot,decision
def _master_protein(prots, proteins, pretxt):
    '''
    Calculate the master protein for one PSM
    '''
    # get the proteins for the peptide
    x = proteins.loc[proteins['Proteins'].isin(prots)]
    # get the proteins with the maximum num of peptides
    y = x[x['num_peptides']==x['num_peptides'].max()].dropna(axis=1, thresh=1).dropna()
    # if there is only one protein, we get it
    # otherwise, we need a decision
    if len(y.index) == 1:
        mq = y['Proteins'].iloc[0]
        mq_t = -1    
    else:
        mq,mq_t = _master_decision(y, pretxt)
    # return
    return mq,mq_t
def get_master_protein(df, proteins, pretxt):
    '''
    Calculate the master protein for each PSM
    '''  
    # create a list with the concate of Protein + ProteinRedundancy
    x = df["Protein"] + "_||_"+ df["Protein_Redundancy"]
    x = x.str.replace(r'\_\|\|\_$', "")
    a = list(x.str.split(r'\_\|\|\_'))
    # calculate the master protein for each PSM
    m,t = zip(*[ _master_protein(i, proteins, pretxt) for i in a ])
    # return
    return m,t


def get_fasta_report(file):
    '''
    Create the FASTA report
    '''
    def _create_key_id(rec):
        if (rec.startswith("sp") or rec.startswith("tr")) and "|" in rec:
            return rec.split("|")[1]
        else:
            return rec
    indb = SeqIO.index(file, "fasta", key_function=_create_key_id)
    return indb

def main(args):
    '''
    Main function
    '''    
    # get the index of proteins: for UniProt case!! (key_function)
    logging.info('create a UniProt report')
    indb = get_fasta_report(args.indb)
    
    logging.info('read infile')
    indat = pandas.read_csv(args.infile, sep="\t", na_values=['NA'], low_memory=False)

    # add the description for the proteins.
    # extract the genes (with redundances) and species.
    # discarding DECOY proteins
    logging.info('create a report with the proteins info')
    indat["Protein"],indat["Protein_Redundancy"],indat["Protein_Length"],indat["Gene"],indat["Gene_Redundancy"],indat["Species"] = add_descriptions(indat, indb, args.lab_decoy)

# TODO!!!
# IMPROVE THE MASTERQ METHOD!! FASTER!!!
# IDEA:
# CREATE A COLUMN WITH THE NUMBER OF PSM's AND PEPTIDIES FOR EACH PROTEIN USING DATAFRAME GROUPBY
    
    # logging.info('create the report with the peptides and proteins')
    # proteins = get_num_peptides( indat[['SequenceMod','Protein','Protein_Redundancy','Protein_Length']] )

    # logging.info('calculate the masterQ')
    # indat["MasterQ"],indat["MasterQ_Tag"] = get_master_protein(indat, proteins, args.pretxt)

    logging.info('print output')
    indat.to_csv(args.outfile, sep="\t", index=False)






    # -----
    # DEPRECATED 
    # ------
    # logging.info('create corrector object')
    # co = corrector(args.infile, args.species, args.pretxt, args.indb, args.columns)

    # logging.info('add the fasta description for each protein')
    # co.add_prot_gen_description()

    # logging.info('calculate the unique protein')
    # co.get_unique_protein()

    # logging.info('merge with the input data file')
    # co.merge_w_indat()

    # logging.info('print output')
    # co.to_csv(args.outfile)
    # -----
    # DEPRECATED 
    # ------


if __name__ == "__main__":
    # parse arguments
    parser = argparse.ArgumentParser(
        description='Create the relationship table for peptide2protein method (get unique protein)',
        epilog='''Examples:
        python  src/SanXoT/rels2pq_unique.py
          -i ID-q.tsv
          -d Human_jul14.curated.fasta
          -l "_INV_"
          -p "Homo sapiens,sp"
          -o ID-mq.tsv
        ''',
        formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('-i',  '--infile',  required=True, help='ID-q input file')
    parser.add_argument('-d',  '--indb',    help='in the case of a tie, we apply the sorted protein sequence using the given FASTA file')
    parser.add_argument('-l',  '--lab_decoy', required=True, help='Label of decoy sequences in the db file')
    parser.add_argument('-p',  '--pretxt',  type=str, help='in the case of a tie, we apply teh preferenced text checked in the comment line of a protein. Eg. Organism, etc.')
    parser.add_argument('-o',  '--outfile', required=True, help='Output file with the masterQ column')
    parser.add_argument('-v', dest='verbose', action='store_true', help="Increase output verbosity")
    args = parser.parse_args()

    # logging debug level. By default, info level
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG,
                            format='%(asctime)s - %(levelname)s - %(message)s',
                            datefmt='%m/%d/%Y %I:%M:%S %p')
    else:
        logging.basicConfig(level=logging.INFO,
                            format='%(asctime)s - %(levelname)s - %(message)s',
                            datefmt='%m/%d/%Y %I:%M:%S %p')

    # start main function
    logging.info('start script: '+"{0}".format(" ".join([x for x in sys.argv])))
    main(args)
    logging.info('end script')
