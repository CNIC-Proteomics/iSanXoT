#!/usr/bin/python

# import global modules
import os
import sys
import argparse
import logging
import pandas
import numpy as np
import concurrent.futures
import pandas as pd
# from Bio import SeqIO



# Module metadata variables
__author__ = "Jose Rodriguez"
__credits__ = ["Jose Rodriguez", "Jesus Vazquez"]
__license__ = "Creative Commons Attribution-NonCommercial-NoDerivs 4.0 Unported License https://creativecommons.org/licenses/by-nc-nd/4.0/"
__version__ = "1.0.1"
__maintainer__ = "Jose Rodriguez"
__email__ = "jmrodriguezc@cnic.es"
__status__ = "Development"




# -------

# def extract_proteins(df, tagDecoy, indb):
#     '''
#     Extract the proteins list discarding DECOY proteins
#     '''
#     # local functions
#     def get_fasta_desc(q):
#         if indb is not None and q in indb:
#             return ">"+indb[q].description
#         else:
#             return ''
#     # create a list for both lists
#     ps = list(df.fillna("").str.split("\s*;\s*"))
#     # remove DECOY
#     da = [ [i for i in s if i and not (tagDecoy in i)] for s in ps ]
#     # get the first protein
#     pm = [ s[0] for s in da ]
#     # create the list of proteins discarding DECOY
#     pr = [ ";".join([i for i in s[1:] if i]) for s in da ]
#     # get the description if apply
#     dm = list(map(get_fasta_desc, pm))
#     return pm,pr,dm

def extract_proteins2(df, tagDecoy):
    '''
    Extract the proteins list discarding DECOY proteins
    '''
    # fill na
    df = df.fillna("")
    # create a list for both lists
    ps = list(df['Protein_Accessions'].str.split("\s*;\s*"))
    ds = list(df['Protein_Descriptions'].str.split("\s*;\s*"))
    # remove DECOY from the list of tuples (protein,description)
    da = [ [(i,j) for i,j in zip(p,d) if i and not (tagDecoy in i)] for p,d in zip(ps,ds) ]
    # get the first (protein,description)
    pm,dm = zip(*[ s[0] for s in da ])
    # create the list of proteins of redundancy (the rest of proteins)
    pr = [ ";".join([i[0] for i in s[1:] if i[0]]) for s in da ]
    return pm,pr,dm

# def sort_proteins(df, tagDecoy):
#     '''
#     Sort the list of proteins and retrieve the first and the rest (discarding DECOY proteins)
#     '''
#     # create a list of tuples with the (ProteinID,ProteinDescription,ProteinLength)
#     a = list(df.fillna("").str.split("\s*;\s*"))
#     # sort and discard the DECOY proteins
#     da = [ [i for i in sorted(s) if not (tagDecoy in i[0]) and all(i)] for s in a ]
#     # from the list of protein: the first element, and the rest (redundancy)
#     pm = [ i[0] for i in da ]
#     pr = [ ";".join(i[1:]) for i in da ]
#     # return
#     return pm,pr

def get_num_peptides(df):
    '''
    Create the report with the protein values
    '''
    # convert string to list
    df1 = df['Protein_Accessions'].str.split(r'\s*;\s*')
    # get unique values of proteins
    df1 = df1.apply(lambda x: np.unique(x))
    # concat with sequnce
    df2 = pd.concat([df['Peptide'], df1], axis=1, sort=False)
    # explode the list
    df2 = df2.explode('Protein_Accessions')
    # group by protein and sum the number of peptides
    df2 = df2.groupby('Protein_Accessions')['Peptide'].count().reset_index()
    # rename and drop
    df2.rename(columns={'Peptide': 'num_peptides', 'Protein_Accessions': 'Proteins'}, inplace=True)
    # return
    return df2

def _master_protein(prots, npeptides):
    '''
    Calculate the master protein for one PSM
    '''
    # get the proteins for the peptide
    x = npeptides.loc[npeptides['Proteins'].isin(prots)]
    # sort by num. peptides and by alphabetic
    x = x.sort_values(by=['num_peptides', 'Proteins'], ascending=[False,True])
    # if there is only one protein, we get it
    # otherwise, we need a decision
    mq,mq_t = '',[]
    if len(x.index) == 1:
        mq = x['Proteins'].iloc[0]
        mq_t = []
    elif len(x.index) >= 1:
        mq = x['Proteins'].iloc[0]
        mq_t = x['Proteins'].iloc[1:].to_list()
    # return
    return mq,mq_t
def get_master_protein(df, npeptides):
    '''
    Calculate the master protein for each PSM
    '''  
    # create a list splitting
    ps = df.str.split(r'\s*;\s*').tolist()    
    # calculate the master protein for each PSM
    # get the unique values
    m,t = zip(*[ _master_protein(np.unique(i), npeptides) for i in ps ])
    # return
    return m,t

# def get_fasta_report(file):
#     '''
#     Create the FASTA report
#     '''
#     def _create_key_id(rec):
#         if (rec.startswith("sp") or rec.startswith("tr")) and "|" in rec:
#             return rec.split("|")[1]
#         else:
#             return rec
#     indb = SeqIO.index(file, "fasta", key_function=_create_key_id)
#     return indb

def read_infiles(file):
    indat = pandas.read_csv(file, sep="\t", na_values=['NA'], low_memory=False)
    return indat

def main(args):
    '''
    Main function
    '''
    logging.info("read files")
    with concurrent.futures.ProcessPoolExecutor(max_workers=args.n_workers) as executor:            
        indat = executor.map(read_infiles,args.infiles.split(";"))
    indat = pd.concat(indat)
    
    # # get the index of proteins: for UniProt case!! (key_function)
    # if args.indb is not None and os.path.isfile(args.indb):
    #     logging.info('create a UniProt report')
    #     indb = get_fasta_report(args.indb)
    # else:
    #     indb = None
    
    if not args.masterq:
        # retrieve the columns without any filter
        # extract the list of proteins discarding DECOY proteins
        # extract the descripton of proteins
        logging.info('create a report with the proteins info')
        # indat["Protein"],indat["Protein_Redundancy"],indat["Description"] = extract_proteins(indat['Protein_Accessions'], args.lab_decoy, indb)
        # if not indb: indat.drop("Description", axis=1, inplace=True)
        indat["Protein"],indat["Protein_Redundancy"],indat["Protein_Description"] = extract_proteins2(indat[['Protein_Accessions','Protein_Descriptions']], args.lab_decoy)
    else:
        # Sort the proteins by Num. Peptides and Alphanumeric

# TODO!!!
# IMPROVE THE MASTERQ METHOD!! FASTER!!!
# CONCURRENT FUTURE!!!
            
        logging.info('create the report with the peptides and proteins')
        npeptides = get_num_peptides( indat[['Peptide','Protein_Accessions']] )

        logging.info('calculate the masterQ')
        indat["Protein"],indat["Protein_Redundancy"] = get_master_protein(indat['Protein_Accessions'], npeptides)

    
    logging.info('print output')
    # print to tmp file
    f = f"{args.outfile}.tmp"
    indat.to_csv(f, sep="\t", index=False)
    # rename tmp file
    os.rename(f, os.path.splitext(f)[0])






if __name__ == "__main__":
    # parse arguments
    parser = argparse.ArgumentParser(
        description='Create the relationship table for peptide2protein method (get unique protein)',
        epilog='''Examples:
        python  src/SanXoT/rels2pq_unique.py
          -ii TMT1/ID-q.tsv;TMT2/ID-q.tsv
          -l "_INV_"
          -o ID-q.tsv
        ''',
        formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('-w',  '--n_workers', type=int, default=2, help='Number of threads/n_workers (default: %(default)s)')
    parser.add_argument('-ii',  '--infiles',  required=True, help='Multiple input files separated by comma')
    parser.add_argument('-l',  '--lab_decoy', help='Label of decoy sequences in the db file')
    parser.add_argument('-o',  '--outfile', required=True, help='Output file with the masterQ column')
    # parser.add_argument('-d',  '--indb',    help='in the case of a tie, we apply the sorted protein sequence using the given FASTA file')
    parser.add_argument('-m',  '--masterq', default=False, action='store_true', help="Flag to determines if we get the masterQ or not")
    parser.add_argument('-vv', dest='verbose', action='store_true', help="Increase output verbosity")
    args = parser.parse_args()

    # get the name of script
    script_name = os.path.splitext( os.path.basename(__file__) )[0].upper()

    # logging debug level. By default, info level
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG,
                            format=script_name+' - '+str(os.getpid())+' - %(asctime)s - %(levelname)s - %(message)s',
                            datefmt='%m/%d/%Y %I:%M:%S %p')
    else:
        logging.basicConfig(level=logging.INFO,
                            format=script_name+' - '+str(os.getpid())+' - %(asctime)s - %(levelname)s - %(message)s',
                            datefmt='%m/%d/%Y %I:%M:%S %p')

    # start main function
    logging.info('start script: '+"{0}".format(" ".join([x for x in sys.argv])))
    main(args)
    logging.info('end script')
