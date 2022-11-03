#!/usr/bin/python

# -*- coding: utf-8 -*-

# Module metadata variables
__author__ = "Rafael Barrero Rodriguez"
__credits__ = ["Rafael Barrero Rodriguez", "Jose Rodriguez", "Jesus Vazquez"]
__license__ = "Creative Commons Attribution-NonCommercial-NoDerivs 4.0 Unported License https://creativecommons.org/licenses/by-nc-nd/4.0/"
__version__ = "0.0.1"
__email__ = "rbarreror@cnic.es;jmrodriguezc@cnic.es"
__status__ = "Development"

# Primary libraries
import argparse
import multiprocessing
import logging
import os
import pdb
import sys
import yaml
import concurrent.futures
import itertools
from itertools import repeat
import numpy as np
import pandas as pd
import re
import sys
from time import time


#
# Functions and Classes
#
def readDF(filePath):
    '''
    '''
    df_tmp = pd.read_csv(filePath, sep='\t', float_precision='high', low_memory=False)
    df_tmp['_filePaths'] = filePath
    return df_tmp

def readIDQ(paramsDict):
    '''
    '''
    with concurrent.futures.ProcessPoolExecutor(max_workers=int(paramsDict['n_cores'])) as executor:
        df_list = executor.map(readDF, paramsDict['infile'])
   
    df = pd.concat(df_list, axis=0).reset_index(drop=True)
    return df

def getAccession(line, decoyPrefix):
    '''
    '''
    isTarget = True

    try:
        pre_acc_RE = re.search(r'^>([^|]*)\|([^|]+)\|', line)
        if pre_acc_RE != None:
            preffix, accession = pre_acc_RE.groups()
        else:
            if re.search(r'^>'+re.escape(decoyPrefix), line) and decoyPrefix!="":
                return line[1:], False
            else:
                return line[1:], True

    except:
        logging.exception(f'Error when extracting accession from fasta:\n{line}')

    # if accession comes from decoy protein, add decoy to the accession (not to confuse with real protein)
    if re.search(r'^'+re.escape(decoyPrefix), preffix) and decoyPrefix!="":
        isTarget = False
        accession = decoyPrefix + accession
    
    return accession, isTarget
    

def replaceLeu(seq_i, iso_leucine):
    '''
    '''
    seq_o = seq_i

    for i in ['L', 'I', 'J']:
        if i == iso_leucine: continue
        if iso_leucine != "": seq_o = seq_o.replace(i, iso_leucine)
    
    return seq_o


def fastaReader(paramsDict):
    '''
    '''
    acc_list = []
    desc_list = []
    seq_list = []
    isTarget_list = []

    with open(paramsDict["fasta_params"]['fasta'], 'r') as f:

        seq_i = ""
        for line in f:

            if '>' in line[0]:

                if seq_i != '':
                    seq_list.append(seq_i)
                    seq_i = ''
                
                desc_list.append(line.strip()[1:])
                accession, isTarget = getAccession(line.strip(), paramsDict["fasta_params"]['decoy_prefix'])
                acc_list.append(accession)
                isTarget_list.append(isTarget)
            
            else:
                seq_i += line.strip()
        
        seq_list.append(seq_i)
        
        seq_list = [replaceLeu(i, paramsDict["fasta_params"]['iso_leucine']) for i in seq_list]
    
    acc_desc_seq = list(zip(desc_list, acc_list, seq_list, isTarget_list))
    target_desc_acc_seq = [(i,j,k) for i,j,k,l in acc_desc_seq if l]
    target_desc_acc_seq = {
        'd':[i for i,j,k in target_desc_acc_seq], 
        'acc':[j for i,j,k in target_desc_acc_seq], 
        'seq':[k for i,j,k in target_desc_acc_seq]
    }

    decoy_desc_acc_seq = [(i,j,k) for i,j,k,l in acc_desc_seq if not l]
    decoy_desc_acc_seq = {
        'd':[i for i,j,k in decoy_desc_acc_seq], 
        'acc':[j for i,j,k in decoy_desc_acc_seq], 
        'seq':[k for i,j,k in decoy_desc_acc_seq]
    }

    #return acc_desc_seq
    #return acc_list, desc_list, seq_list
    return target_desc_acc_seq, decoy_desc_acc_seq


def getCandidateProteins_in(q, pp_set, paramsDict):
    '''
    '''

    # Split pp_set in chunks
    #pp_set_chunks = split(pp_set, int(paramsDict['n_cores']))
    
    q_seq_chunks = split(q['seq'], int(paramsDict['n_cores']))
    acc_seq_chunks = split(q['acc'], int(paramsDict['n_cores']))
    d_seq_chunks = split(q['d'], int(paramsDict['n_cores']))

    with concurrent.futures.ProcessPoolExecutor(max_workers=int(paramsDict['n_cores'])) as executor:
        sub_seqs = list(executor.map(pp_set_in_prot, repeat(pp_set), q_seq_chunks))
        sub_seqs = list(executor.map(pp_seq_in_acc_d, sub_seqs, acc_seq_chunks, d_seq_chunks)) 

        #sub_seqs = list(executor.map(pp_set_in_prot, pp_set_chunks, repeat(q['seq'])))
        #sub_seqs = list(executor.map(pp_seq_in_acc_d, sub_seqs, repeat(q['acc']), repeat(q['d']))) 
    
    
    sub_seqs = add_flatten_lists(sub_seqs)

    return sub_seqs


def split(a, n):
    k, m = divmod(len(a), n)
    return (a[i*k+min(i, m):(i+1)*k+min(i+1, m)] for i in range(n))


def pp_set_in_prot(pp_set, seq_list):
    return [[i in j for j in seq_list] for i in pp_set]


def pp_seq_in_acc_d(sub_seqs, acc_list, d_list):
    return [list(zip(*filter(lambda x: x[0], zip(i, acc_list, d_list))))[1:] for i in sub_seqs]
    #return [[' // '.join(j) for j in list(zip(*filter(lambda x: x[0], zip(i, acc_list, d_list))))[1:]] for i in sub_seqs]


def add_flatten_lists(the_lists):
    
    # the_lists = [[], [], ..., []k], where k is the number of chunks.
    # the_lists[i] = [[], [], ... []n], where n is the number of plain peptides
    # the_lists[i][j] = [(acc), (d)], where (acc) and (d) are tuples with candidate proteins

    # Some elements the_lists[i][j] are equal to [], so we "repair" them to [(''), ('')]
    sub_seqs_repaired = [[[('',), ('',)] if len(j)==0 else j for j in i] for i in the_lists]

    # Group plain peptides of different chunks
    tmp = list(zip(*sub_seqs_repaired))

    # Group acc and d of plain peptides from different chunks
    tmp2= [list(zip(*i)) for i in tmp]

    # Flatten acc and d (they are a list of tuples...)
    tmp3 = [[[iii for ii in i for iii in ii if iii!=''],[jjj for jj in j for jjj in jj if jjj!='']] for i,j in tmp2]

    # Join list of acc and d as a string
    result = [[' // '.join(i), ' // '.join(j)] for i,j in tmp3]
    
    """
    result = []
    for _list in the_lists:
        result += _list
    """
    return result
    


def getMostProbableProtein(dffile, paramsDict):
    '''
    
    '''
    # Sort alphabetically candidate proteins using paramsDict["column_params"]['prot_column'][0] as reference
    tmp = [dffile[i].to_list() for i in paramsDict["column_params"]['prot_column']]
    tmp = [[[elem.strip() for elem in row.split(paramsDict["column_params"]['sep_char'])] for row in col] for col in tmp]
    tmp = [list(zip(*zipped_row)) for zipped_row in zip(*tmp)]
    tmp = [sorted(row, key=lambda x: x[0]) for row in tmp]
    tmp = list(zip(*[[paramsDict["column_params"]['sep_char'].join(col) for col in list(zip(*row))] for row in tmp]))

    workingColumns = []
    for i,j in zip(paramsDict["column_params"]['prot_column'], tmp):
        k = "_mpp_"+i
        workingColumns.append(k)
        dffile[k] = j


    # Columns containing information from multiple protein separated by ";". Name of columns got from "col" variable in main
    #semicolon_col_list = paramsDict['_additional_column'] #["ProteinsLength","NpMiss","NpTotal","PeptidePos","PrevNextaa"]

    # Name of the column with protein information (it can be UniProtIDs or Proteins)
    sc_prot_col = workingColumns[0]

    # Get indexes of dffile
    df_index = dffile.index.to_list()

    # This array will contain the position of the most probable protein in each row
    df_index_result_pos = np.ones_like(df_index)*(-1)

    # Get boolean with non decoy PSMs (has no real protein assigned)
    non_decoy_bool = ~dffile[sc_prot_col].isnull()

    # Extract sc_prot_col from dffile. Generate List of Lists [ [p1, p2...], [p1, p2..] ... ]
    if paramsDict['mode'] == 'column':
        # JUAN ANTONIO inputs contain DECOY_sp and DECOY_tr. They have advantage...
        # remove blank elements of the split
        sc_prot_list = [list([j.strip() for j in i.split(paramsDict["column_params"]['sep_char']) if j.strip()!='']) for i in dffile.loc[non_decoy_bool, sc_prot_col].to_list()]
        
        # sc_prot_list contains a list with sets of (valid) candidate proteins. 
        # sc_prot_list_index contains a list with sets of index of these valid candidate proteins (excluding "" and decoys)
        
        # if only contain decoy it will be []
        sc_prot_list_index_pair = [list(zip(*[[j,n] for n,j in enumerate(i) if 'decoy' not in j.lower()])) for i in sc_prot_list]
        # replace [] by [(decoy,), (0,)]
        sc_prot_list_index = [i if i != [] else [("DECOY_",), (0,)] for i in sc_prot_list_index_pair]
        sc_prot_list, sc_prot_list_index = list(zip(*sc_prot_list_index))
        #sc_prot_list, sc_prot_list_index = list(zip(*[zip(*[[j,n] for n,j in enumerate(i) if 'decoy' not in j.lower()]) for i in sc_prot_list]))

        # in this cool way we generate a list with size of the initial table, with sc_prot_list_index in the right position
        c = itertools.count(0)
        all_prot_list_index = [sc_prot_list_index[next(c)] if i else [] for i in non_decoy_bool]   

    else:
        sc_prot_list = [tuple([j.strip() for j in i.split(paramsDict["column_params"]['sep_char']) if j.strip()!='']) for i in dffile.loc[non_decoy_bool, sc_prot_col].to_list()]

    # Extract peptide sequence of each scan: pepcolumn of dffile
    p_seq_list = dffile.loc[non_decoy_bool, paramsDict['seq_column']].to_list()

    # Get set of pairs (peptide sequence, [protein list]). Do not repeat peptide sequence!
    pseq_prot_pair_list = list(set(list(zip(p_seq_list, sc_prot_list))))
    
    # Get flat list with all proteins contributed by each peptide sequence to get number of peptides per protein
    protein_from_pseq = sorted([j for i in pseq_prot_pair_list for j in i[1]])
    protein2npep = {k : len(list(g)) for k, g in itertools.groupby(protein_from_pseq)}

    # Get flat list with all proteins contributed by each scan to get number of scans per protein
    protein_from_scan = sorted([j for i in sc_prot_list for j in i])
    protein2nscan = {k : len(list(g)) for k, g in itertools.groupby(protein_from_scan)}

    # import pickle
    # with open("q2p.obj", 'wb') as f: pickle.dump(protein2npep, f)
    # with open("q2s.obj", 'wb') as f: pickle.dump(protein2nscan, f)

    # Extract elements of sc_prot_list with more than one protein
    sc_prot_list_number = np.array([len(i) for i in sc_prot_list])
    sc_prot_gt1_bool_arr = sc_prot_list_number > 1
    sc_prot_gt1_list = [i for i,j in zip(sc_prot_list, sc_prot_gt1_bool_arr.tolist()) if j]
    
    # Resolve elements with one protein only: From full index, get non-decoy. And from them, get those with one protein
    # aux_arr is analogous to non-decoy elements. We first index those with one protein only.
    # aux_arr is subset of df_index_result_pos --> aux_arr = df_index_result_pos[non_decoy_bool]
    
    aux_arr = np.ones_like(np.arange(0, len(sc_prot_list)))*(-1)
    aux_arr[~sc_prot_gt1_bool_arr] = 0 # protein in position 0 for elements with 0 or 1 proteins
    aux_arr[sc_prot_list_number==0] = -1 # -1 for elements with 0 protein (case of all decoys)
    
    # aux_arr2 is analogous to elements with more than one protein. We first index those with only one maximum
    # aux_arr2 is a subset of aux_arr --> aux_arr2 = aux_arr[sc_prot_gt1_bool_arr]
    aux_arr2 = np.ones_like(np.arange(0, len(sc_prot_gt1_list)))*(-1)
    
    # Replace protein by its number of peptides
    sc_prot_npep_gt1_list = [[protein2npep[j] for j in i] for i in sc_prot_gt1_list]

    # Get List of pairs (index of elem, position of maximum protein)
    sc_prot_npep_gt1_1max = [[n, np.argmax(i)] for n, i in enumerate(sc_prot_npep_gt1_list) if np.sum(np.max(i) == np.array(i)) == 1]
    sc_prot_npep_gt1_1max_index = [i for i,j in sc_prot_npep_gt1_1max]
    sc_prot_npep_gt1_1max_position = [j for i,j in sc_prot_npep_gt1_1max]

    # This array will contain partition coefficient calculated using peptides
    df_part_coef_pep = np.zeros_like(df_index, dtype=np.float64)
    df_part_coef_pep[non_decoy_bool] = 1
    tmp = [np.max(i)/np.sum(i) for i in sc_prot_npep_gt1_list]
    df_part_coef_pep[dffile.loc[non_decoy_bool, :].index.to_numpy()[sc_prot_gt1_bool_arr]] = np.array(tmp)


    df_part_theor_coef_pep = np.zeros_like(df_index, dtype=np.float64)
    df_part_theor_coef_pep[non_decoy_bool] = 1
    tmp = [1/len(i) for i in sc_prot_npep_gt1_list]
    df_part_theor_coef_pep[dffile.loc[non_decoy_bool, :].index.to_numpy()[sc_prot_gt1_bool_arr]] = np.array(tmp)

    # Add solved position to aux_arr2
    aux_arr2[sc_prot_npep_gt1_1max_index] = sc_prot_npep_gt1_1max_position

    # Resolve element with more than one maximum. We now use number of scans instead of number of peptides
    sc_prot_npep_gt1_gt1max_index = np.arange(0, len(sc_prot_gt1_list))
    sc_prot_npep_gt1_gt1max_index[sc_prot_npep_gt1_1max_index] = -1
    sc_prot_npep_gt1_gt1max_index = sc_prot_npep_gt1_gt1max_index[sc_prot_npep_gt1_gt1max_index != -1].tolist()

    sc_prot_nscan_gt1_list = \
        [[protein2nscan[j] for j in sc_prot_gt1_list[i]] for i in sc_prot_npep_gt1_gt1max_index]

    sc_prot_nscan_gt1_1max = [np.argmax(i) for i in sc_prot_nscan_gt1_list] #if np.sum(np.max(i) == np.array(i)) == 1]

    # Add to aux_arr2, the position of elements resolved using PSMs (or arbitrary position)
    aux_arr2[sc_prot_npep_gt1_gt1max_index] = sc_prot_nscan_gt1_1max

    # Incorporate to aux_arr its subset aux_arr2
    aux_arr[sc_prot_gt1_bool_arr] = aux_arr2

    # Incorporate to df_index_result_pos its subset aux_arr
    df_index_result_pos[non_decoy_bool] = aux_arr
    df_part_coef_pep[df_index_result_pos==-1] = 0
    df_part_theor_coef_pep[df_index_result_pos==-1] = 0

    # Generate new columns
    # mppSuffix = "_MPP"
    
    #workingColumns = paramsDict["column_params"]["prot_column"] #paramsDict['_additional_column']+[paramsDict['prot_column']]
    if paramsDict['mode']=='column':
        # JUAN ANTONIO case...
        new_columns_list = [
            [l.strip() for l in j.split(paramsDict["column_params"]['sep_char']) if l.strip()!='' and 'decoy' not in l.strip().lower()] \
                for j in dffile[sc_prot_col].to_list()
            ]

        new_columns_list = [i if i !=[] else ["DECOY_"] for i in new_columns_list]

        new_columns_list = [
            [[l for l in j][k] if k!=-1 else "" for j,k in zip(new_columns_list, df_index_result_pos)]
            ]

        #new_columns_list = [
        #    [[l.strip() for l in j.split(paramsDict["column_params"]['sep_char']) if l.strip()!='' and 'decoy' not in l.strip().lower()][k] if k!=-1 else "" \
        #        for j,k in zip(dffile[sc_prot_col].to_list(), df_index_result_pos)]
        #    ]
        
        if len(workingColumns) > 1:
            # split candidate proteins removing blank space
            new_columns_list_2 = [[[l.strip() for l in j.split(paramsDict["column_params"]['sep_char']) if l.strip()!=''] for j in dffile[i].to_list()] \
                for i in workingColumns[1:]]

            # extract non decoys 
            new_columns_list_2 = [[np.array(j1)[list(j2)].tolist() if j2!=[] else j1 for j1,j2 in zip(i,all_prot_list_index)] 
                for i in new_columns_list_2]

            # extract MPP
            new_columns_list_2 = [[j[k] if k!=-1 else "" for j,k in zip(i, df_index_result_pos)] for i in new_columns_list_2]

            new_columns_list_3 = []
            for i in new_columns_list_2:
                j = np.array(i)
                j[np.array(new_columns_list[0])=="DECOY_"] = "DECOY_"
                new_columns_list_3.append(j.tolist())
            
            new_columns_list += new_columns_list_3

    else:
        new_columns_list = [[[l.strip() for l in j.split(paramsDict["column_params"]['sep_char']) if l.strip()!=''][k] if k!=-1 else "" for j,k in zip(dffile[i].to_list(), df_index_result_pos)] \
            for i in workingColumns]

    new_columns_df = pd.DataFrame({i: j for i,j in zip(paramsDict["column_params"]['prot_column_mpp'], new_columns_list)})
    
    # Remove > from the first character in protein column
    #if semicolon_col_protein_list[0]+mppSuffix in new_columns_df.columns:
    #    new_columns_df[semicolon_col_protein_list[0]+mppSuffix] = new_columns_df[semicolon_col_protein_list[0]+mppSuffix].str.replace('^>', '', regex=True)
    
    
    # Generate final dataframe
    dffile_MPP = pd.concat([dffile.reset_index(drop=True), new_columns_df.reset_index(drop=True)], axis=1)
    dffile_MPP[paramsDict["column_params"]['prot_column'][0]+"_coef"] = df_part_coef_pep
    dffile_MPP[paramsDict["column_params"]['prot_column'][0]+"_coef_min"] = df_part_theor_coef_pep
    dffile_MPP.drop(columns=workingColumns, inplace=True)

    # Replace " // " for ";"
    if paramsDict["mode"].lower()=="fasta":
        for i in paramsDict["column_params"]['prot_column']:
            dffile_MPP[i] = dffile_MPP[i].str.replace(paramsDict["column_params"]['sep_char'], ';')

    return dffile_MPP


def writeDF(filePath, outFilePath, df):
    df_i = df.loc[df['_filePaths'] == filePath, :].copy()
    df_i.dropna(axis=1, how='all', inplace=True)
    df_i.drop(labels='_filePaths', axis=1, inplace=True)
    #outFilePath = f"{os.path.splitext(filePath)[0]}_{suffixScript}{os.path.splitext(filePath)[1]}"
    df_i.to_csv(outFilePath, sep="\t", index=False)

def writeIDQ(df, paramsDict):
    '''
    '''
    
    if not paramsDict['outfile']:
        paramsDict['outfile'] = [f"{os.path.splitext(i)[0]}_{suffixScript}{os.path.splitext(i)[1]}"
            for i in paramsDict['infile']]
    
    with concurrent.futures.ProcessPoolExecutor(max_workers=int(paramsDict['n_cores'])) as executor:
        executor.map(writeDF, paramsDict['infile'], paramsDict['outfile'], repeat(df))


#
# Main
#
def main(paramsDict):
    '''
    '''

    #
    # Read ID Table
    #
    t = time()
    try:
        df = readIDQ(paramsDict)    
        logging.info(f'ID tables were read in {str(round(time()-t, 2))}s')
    except:
        logging.exception(f'Error reading input files: {paramsDict["infile"]}')
        sys.exit(-1)

    if not paramsDict['seq_column'] in df.columns:
        logging.error(f'{paramsDict["seq_column"]} column with plain peptides not found')
        sys.exit(-3)

    
    #
    # Create column with candidate proteins
    #
    if paramsDict['mode'].lower() == 'fasta':

        # read fasta
        t=time()
        try:
            target_q, decoy_q = fastaReader(paramsDict)
            logging.info(f'Fasta was read in {str(round(time()-t, 2))}s: {paramsDict["fasta_params"]["fasta"]}')
        except:
            logging.exception(f'Error reading fasta file: {paramsDict["fasta_params"]["fasta"]}')
            sys.exit(-2)
        

        # Identify candidate proteins
        logging.info(f'Identifying candidate proteins...')

        # Extract plain peptides (pp) from psm table
        pp_psm = df[paramsDict['seq_column']].to_list() # list of pp of each psm
        pp_psm_index = sorted(list(zip(pp_psm, list(range(len(pp_psm)))))) # list of pp_psm with its index
        pp_indexes = [(i, tuple([l for k,l in j])) for i,j in itertools.groupby(pp_psm_index, lambda x: x[0])] # pp_set with all their indexes
        pp_set = sorted(list(set(pp_psm))) # pp_set

        # Find plain peptides in target
        t = time()
        pp_acc_d = getCandidateProteins_in(target_q, pp_set, paramsDict)
        logging.info(f'Plain peptides were searched in target proteins {str(round(time()-t, 2))}s')

        # Find the rest of the plain peptides in decoy
        pp_decoy_index = list(zip(*[[i,k] for i,j,k in zip(pp_set, pp_acc_d, range(len(pp_set))) if j==['','']]))
        if pp_decoy_index != []:
            t = time()
            pp_decoy, pp_decoy_index = pp_decoy_index
            pp_decoy_acc_d = getCandidateProteins_in(decoy_q, pp_decoy, paramsDict)
        
            for i,j in zip(pp_decoy_acc_d, pp_decoy_index): 
                pp_acc_d[j] = i # if i!=[] else ['','']
        
            logging.info(f'Remaining plain peptides were searched in decoy proteins {str(round(time()-t, 2))}s')


        # Add to df the columns with accession and description of candidate proteins (!!! Do not overwrite columns)
        pp_indexes_acc, pp_indexes_d = zip(*[[(i[1], (j[0],)), (i[1], (j[1],))] for i,j in zip(pp_indexes, pp_acc_d)])        
        acc_column = list(zip(*sorted([j for i in pp_indexes_acc for j in itertools.product(*i)])))[1]
        d_column = list(zip(*sorted([j for i in pp_indexes_d for j in itertools.product(*i)])))[1]

        # GET COLUMN NAMES FROM USER PARAMS!!!
        # d_colName, acc_colName = suffixScript+'_description', suffixScript+'_accession'
        d_colName, acc_colName = paramsDict['fasta_params']['column_names']['candidate_d'], paramsDict['fasta_params']['column_names']['candidate_a']

        # add these new columns
        df[acc_colName] = acc_column
        df[d_colName] = d_column
        
        logging.info(f"{d_colName} and {acc_colName} columns with candidate proteins were created")

        # If column params section is note created, add it (it is used in MPP calculation)
        if "column_params" not in paramsDict.keys(): 
            paramsDict["column_params"] = {}

        paramsDict["column_params"]['prot_column'] = [acc_colName, d_colName] # column used to calculate most probable protein
        paramsDict["column_params"]['prot_column_mpp'] = [
            paramsDict["fasta_params"]['column_names']['mpp_a'],
            paramsDict["fasta_params"]['column_names']['mpp_d']
        ]
        #paramsDict['_additional_column'] = [d_colName] # another from which extract information of most probable protein
        paramsDict['_replace_delim'] = True # Protein delimiter is " // ". We want to change it to ; in the end (but only in fasta mode)
        paramsDict["column_params"]['sep_char'] = " // "


    #
    # Calculate most probable protein
    #
    logging.info(f'Calculating most probable protein...')
    if np.any([i not in df.columns for i in paramsDict["column_params"]['prot_column']]):
        logging.error(f'{paramsDict["column_params"]["prot_column"]} columns not found')
        sys.exit(-4)

    t = time()
    df = getMostProbableProtein(df, paramsDict)
    logging.info(f'Most probable protein was calculated in {str(round(time()-t, 2))}s')

    #
    # Write ID table
    #
    t = time()
    logging.info("Writing output tables...")
    writeIDQ(df, paramsDict)
    logging.info(f'Output tables were written in {str(round(time()-t, 2))}s')

    return 0


if __name__ == '__main__':

    multiprocessing.freeze_support()
    
    # get the name of script
    script_name = os.path.basename(__file__)
    suffixScript = 'PA'

    # Parse arguments
    parser = argparse.ArgumentParser(
            description='Calculate most probable protein assigned to each PSM ',
            formatter_class=argparse.RawTextHelpFormatter,
            epilog=f'''\
Created 2021-11-24, Rafael Barrero Rodriguez

Usage:
    {script_name} -c "path to YAML config file"
    {script_name} -i "Path\To\Input.File" -o "Path\To\Output.File" -s "Sequence" -q "Protein_Accessions" "Protein_Descriptions" -qm "Protein_Accessions_MPP" "Protein_Descriptions_MPP" -w 2
    {script_name} -i "Path\To\Input.File" -o "Path\To\Output.File" -s "Sequence" -f "Path\To\Fasta.fa" -cd "Protein_Description_Candidate" -ca "Protein_Accession_Candidate" -ma "Protein_Accessions_MPP" -md "Protein_Descriptions_MPP" -w 2
''')


    # Parse command-line arguments (config)
    parser.add_argument('-c', '--config', dest='config', metavar='FILE', type=str,
        help='Path to YAML file containing parameters')
    

    # Parse command-line arguments (non-config)
    parser.add_argument('-i','--infile', nargs="+", help='Path to files containing PSM table')
    parser.add_argument('-o','--outfile', nargs="+", help='Path to ouput file')
    parser.add_argument('-s',  '--plainseq', type=str, help='Name of the column containing peptide sequence')
    parser.add_argument('-m',  '--mode', type=str, default="column", help='Select mode of execution: fasta/column')

    parser.add_argument('-f',  '--fasta', type=str, help='Path to fasta file used to identify candidate proteins')
    parser.add_argument('-dy',  '--decoy', type=str, default="DECOY_", help='decoy prefix in fasta')
    parser.add_argument('-ile',  '--isoleu', type=str, default="L", help='Convert L, I and J to the selected letter')
    parser.add_argument('-cd',  '--cdesc', type=str, default="Protein_Description_Candidate", help='Name of the column with candidate descriptions')
    parser.add_argument('-ca',  '--cacc', type=str, default="Protein_Accessions_Candidate", help='Name of the column with candidate accessions')
    parser.add_argument('-md',  '--mdesc', type=str, default="Protein_Description_MPP", help='Name of the column with most probable descriptions')
    parser.add_argument('-ma',  '--macc', type=str, default="Protein_Accession_MPP", help='Name of the column with most probable accessions')

    
    parser.add_argument('-q','--qcol', nargs="+", help='Name of the column(s) containing information of the candidate proteins')
    parser.add_argument('-qm','--qmpp', nargs="+", help='Name of the output column(s) with the most probable protein')
    parser.add_argument('-d','--dcol', nargs="+", default=[], help='Name of the column(s) containing description information of the candidate proteins')
    parser.add_argument('-dm','--dmpp', nargs="+", default=[], help='Name of the output column(s) with the description of the most probable protein')

    parser.add_argument('-t',  '--sep', type=str, default=";", help='Character used as separator')

    parser.add_argument('-w',  '--n_workers', type=int, default=2, help='Number of threads/n_workers (default: %(default)s)')
    parser.add_argument('-v', dest='verbose', action='store_true', help="Increase output verbosity")

    args = parser.parse_args()
    
    # Read YAML
    if args.config:
        with open(args.config, 'r') as f:
            try:
                paramsDict = yaml.safe_load(f)
            except yaml.YAMLError as exc:
                print(exc)
                sys.exit(-1000)

    else:
        args.mode = "fasta" if args.fasta else "column" 

        paramsDict = {
            "infile": args.infile,
            "outfile": args.outfile,
            "seq_column": args.plainseq,
            "mode": args.mode,
            "n_cores": args.n_workers,

            "fasta_params": {
                "fasta": args.fasta,
                "decoy_prefix": args.decoy,
                "iso_leucine": args.isoleu,
                "column_names": {
                    "candidate_d": args.cdesc,
                    "candidate_a": args.cacc,
                    "mpp_d": args.mdesc,
                    "mpp_a": args.macc
                }
            },

            "column_params": {
                "prot_column": args.qcol + args.dcol,
                "prot_column_mpp": args.qmpp + args.dmpp,
                "sep_char": args.sep
            }
        }

    # logging debug level. By default, info level
    script_name = os.path.splitext(script_name)[0].upper()

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG,
                            format=script_name+' - '+str(os.getpid())+' - %(asctime)s - %(levelname)s - %(message)s',
                            datefmt='%m/%d/%Y %I:%M:%S %p')
    else:
        logging.basicConfig(level=logging.INFO,
                            format=script_name+' - '+str(os.getpid())+' - %(asctime)s - %(levelname)s - %(message)s',
                            datefmt='%m/%d/%Y %I:%M:%S %p')
    
    logging.info('Start script: '+"{0}".format(" ".join([x for x in sys.argv])))
    t0 = time()
    main(paramsDict)
    m, s = divmod(time()-t0,60)
    logging.info(f'End script: {int(m)}m and {round(s,2)}s') 
