#!/usr/bin/python

# Module metadata variables
__author__ = ["Jose Rodriguez"]
__credits__ = ["Ricardo Magni", "Jesus Vazquez", "Jose Rodriguez"]
__license__ = "Creative Commons Attribution-NonCommercial-NoDerivs 4.0 Unported License https://creativecommons.org/licenses/by-nc-nd/4.0/"
__version__ = "1.0.1"
__maintainer__ = "Jose Rodriguez"
__email__ = "jmrodriguezc@cnic.es"
__status__ = "Development"

# import global modules
import os
import sys
import argparse
import logging
import pandas as pd


###################
# Local functions #
###################


def main(args):
    '''
    Main function
    '''
    logging.info("reading input file...")
    indat = pd.read_csv(args.infile, sep="\t", na_values=['NA'], low_memory=False)


    logging.info("getting the number of scans per peptide")
    N_s2p = indat.groupby(['Pep_Id']).agg({
        'Scan_Id': 'nunique',
    })
    N_s2p.reset_index(inplace=True)
    N_s2p.rename(columns={'Scan_Id': 'N_s2p'}, inplace=True)
    
    
    logging.info("getting the number of peptides per protein")
    N_p2q = indat.groupby(['Protein_MPP']).agg({
        'Pep_Id': 'nunique',
    })
    N_p2q.reset_index(inplace=True)
    N_p2q.rename(columns={'Pep_Id': 'N_p2q'}, inplace=True)
    
    
    logging.info("getting the relationship between peptides and proteins")
    rel_p2q = indat[['Pep_Id', 'Protein_MPP']]
    

    logging.info("merging the statistics")
    outdat = pd.merge(rel_p2q, N_s2p, on=['Pep_Id'])
    outdat = pd.merge(outdat, N_p2q, on=['Protein_MPP'])
    outdat.rename(columns={'Protein_MPP': 'Protein'}, inplace=True)


    logging.info("removing duplicates")
    outdat.drop_duplicates(inplace=True)

    # if protein-to-category file exists
    if args.catfile:
        logging.info("reading protein2category file...")
        catdat = pd.read_csv(args.catfile, sep="\t", na_values=['NA'], low_memory=False)
        catdat.rename(columns={'cat_*': 'Categories'}, inplace=True)

        logging.info("merging the categories per protein")
        outdat = pd.merge(outdat, catdat, on=['Protein'], how='left')
        
        logging.info("getting the number of peptides per protein")
        N_q2c = outdat.groupby(['Categories']).agg({
            'Protein': 'nunique',
        })
        N_q2c.reset_index(inplace=True)
        N_q2c.rename(columns={'Protein': 'N_q2c'}, inplace=True)

        logging.info("merging the statistics")
        outdat = pd.merge(outdat, N_q2c, on=['Categories'], how='left')
        
        logging.info("reorder columns")
        outdat = outdat[['Pep_Id', 'Protein', 'Categories', 'N_s2p', 'N_p2q', 'N_q2c']]
        
    # if protein-to-description file exists
    if args.dscfile:
        logging.info("reading protein2description file...")
        dscdat = pd.read_csv(args.dscfile, sep="\t", na_values=['NA'], low_memory=False)
        dscdat = dscdat[['Protein', 'Description']]

        logging.info("merging the statistics")
        outdat = pd.merge(outdat, dscdat, on=['Protein'], how='left')
        
        logging.info("removing duplicates")
        outdat.drop_duplicates(inplace=True)

    
    logging.info("printing the output")
    outdat.to_csv(args.outfile, sep="\t", index=False)


if __name__ == '__main__':
    # parse arguments
    parser = argparse.ArgumentParser(
        description='Create the statistics from ID file',
        epilog='''
        Example:
            python getIDstatsLabelFree.py
                -i "S:/U_Proteomica/UNIDAD/DatosCrudos/___JAL/GloFJD_Oct2022/microPeptidosOrina/exps/ID-q.tsv" /
                -o "S:/U_Proteomica/UNIDAD/DatosCrudos/___JAL/GloFJD_Oct2022/microPeptidosOrina/stats/ID-q.stats.tsv" /
                -c "S:/U_Proteomica/UNIDAD/iSanXoT_DBs/202206/human_202206.pid2cat.tsv" -d "S:/U_Proteomica/UNIDAD/iSanXoT_DBs/202206/human_202206.categories.tsv"

        ''')
    parser.add_argument('-i',  '--infile', required=True, help='Input file: ID.tsv')
    parser.add_argument('-c',  '--catfile', help='protein-to-category Relationship file')
    parser.add_argument('-d',  '--dscfile', help='protein-to-description Relationship file')
    parser.add_argument('-o',  '--outfile',   required=True, help='Output file')
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