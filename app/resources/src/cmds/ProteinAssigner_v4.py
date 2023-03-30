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
from itertools import repeat, groupby
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
        if iso_leucine: seq_o = seq_o.replace(i, iso_leucine)
    
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

def get_q2len(target_q, decoy_q):
    q2len = dict(
        zip(
            target_q['acc'],
            [len(i) for i in target_q['seq']],
        )
    )

    q2len.update(
        dict(
            zip(
                decoy_q['acc'],
                [len(i) for i in decoy_q['seq']],
            )
        )
    )
    return q2len

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
    
    sub_seqs = add_flatten_lists(sub_seqs)

    return sub_seqs


def split(a, n):
    k, m = divmod(len(a), n)
    return (a[i*k+min(i, m):(i+1)*k+min(i+1, m)] for i in range(n))


def pp_set_in_prot(pp_set, seq_list):
    return [[n for n,j in enumerate(seq_list) if i in j] for i in pp_set]


def pp_seq_in_acc_d(sub_seqs, acc_list, d_list):
    return [list(zip(*[[acc_list[j], d_list[j]] for j in i])) for i in sub_seqs]


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
    
def _getMPPindex(l, df, q2len, paramsDict):
    
    pp = paramsDict['seq_column']
    ac = paramsDict['column_params']['candidate_a']
    dc = paramsDict['column_params']['candidate_d']
    sc = paramsDict['column_params']['sep_char']
    
    l = [
     (
      p,
      n[0],
      np.argwhere(n[1]==np.amax(n[1])).flatten().tolist(),
      np.array(n[2]),
      np.arange(len(n[2]))
      ) 
     for p, n in l
     ]
    
    # Filter sn based on maximum pn index
    l = [
     (
      p,
      acc,
      ix[bo][sn[bo] == np.amax(sn[bo])].tolist()
      )
     for p, acc, bo, sn, ix in l
     ]
    
    l = [
     (p, [acc[i] for i in ix], ix)
     for p, acc, ix in l
     ]
    
    
    # if candidate description
    if dc:
    
        # get q description
        qd = df.loc[
               ~df[pp].duplicated(), [pp, dc]
               ].set_index(pp).loc[
                   [i[0] for i in l],:
                       ][dc].str.split(sc).tolist()
        
        
        l = [(*p, [q[i] for i in p[2]]) for p, q in zip(l, qd)]
        
        
        # filter by regex
        regex =  [re.compile('')] + paramsDict['regex']
        
        l = [
         (
          p,
          acc,
          ix,
          [[bool(ri.search(qdi)) for ri in regex] for qdi in qd]
          )
         for p, acc, ix, qd in l
         ]
        
        
        l = [
         (
          p, np.array(acc), np.array(ix), [np.sum(np.cumsum(i) == np.arange(1,len(i)+1)) for i in bo]
          )
         for p, acc, ix, bo in l
         ]
        
        l = [
         (p, acc, ix, np.argwhere(bo==np.amax(bo)).flatten().tolist())
         for p, acc, ix, bo in l
         ]
        
        l = [
         (p, acc[bo].tolist(), ix[bo].tolist())
         for p, acc, ix, bo in l
         ]
        
        
        # filter by seq length
        if paramsDict['mode'] == 'fasta' and paramsDict['len_seq'] in [-1,1]:
            l = [
             (p, np.array(acc), np.array(ix), [q2len[acci] for acci in acc])
             for p, acc, ix in l
             ]
            
            if paramsDict['len_seq']==-1:
                l = [
                 (p, acc, ix, np.argwhere(le == np.amin(le)).flatten().tolist())
                 for p, acc, ix, le in l
                 ]
            elif paramsDict['len_seq']==1:
                l = [
                 (p, acc, ix, np.argwhere(le == np.amax(le)).flatten().tolist())
                 for p, acc, ix, le in l
                 ]
                
            l = [
             (p, acc[leix].tolist(), ix[leix].tolist())
             for p, acc, ix, leix in l
             ]
    
    
    # filter by alphanumeric order
    l = [
     (p, *zip(*sorted(zip(acc, ix))))
     for p, acc, ix in l
     ]
    
    
    l = [
     (p, acc[0], ix[0])
     for p, acc, ix in l
     ]
    
    p2mpp = pd.DataFrame([i[:2] for i in l], columns=[pp, paramsDict['mpp_a']])
    
    if dc:
        p2mpp[paramsDict['mpp_d']] = [q[p[2]] for p, q in zip(l, qd)]
    
    return p2mpp

def getMostProbableProtein(df, paramsDict, q2len={}):
    '''
    
    '''
    pp = paramsDict['seq_column']
    ac = paramsDict['column_params']['candidate_a']
    dc = paramsDict['column_params']['candidate_d']
    sc = paramsDict['column_params']['sep_char']
    
    
    # Slice removing na
    dfw = df.loc[:, [pp, ac]].dropna()
    
    # Split accessions
    dfw[ac] = dfw[ac].str.split(sc)
    
    # Get dict relating q to scan number
    q2sn = dfw[ac].explode().value_counts().to_frame(name='sn')
    
    # Remove duplicated peptides
    dfw = dfw.loc[~dfw[pp].duplicated(), :]
    
    # Get dict relating q to peptide number
    q2pn = dfw[ac].explode().value_counts().to_frame(name='pn')
    
    # Get df relating q to scan and peptide number
    q2n = q2pn.join(q2sn).reset_index().rename(columns={'index':ac})
    
    del q2pn; del q2sn
    
    # Explode by candidate accession and add their pn and sn
    dfw = pd.merge(
        dfw.explode(ac),
        q2n,
        how='left',
        on=ac
        )
    
    # Get df in list structure and groupby plain peptide
    l = list(zip(*[j for i,j in dfw.to_dict('list').items()]))
    
    # sort only by plain peptide (not the rest of fields)
    l = [(i, list(zip(*[k[1:] for k in j]))) for i,j in groupby(sorted(l, key=lambda x: x[0]), lambda x: x[0])]
    
    
    # p2mpp = _getMPPindex(l, df, q2len, paramsDict)
    with concurrent.futures.ProcessPoolExecutor(max_workers=int(paramsDict['n_cores'])) as executor:
        p2mpp = list(executor.map(_getMPPindex, split(l, int(paramsDict['n_cores'])), repeat(df), repeat(q2len), repeat(paramsDict)))
        p2mpp = pd.concat(p2mpp)
    
    
    df = pd.merge(
        df,
        p2mpp,
        on=pp,
        how='left'
        )
    
    if paramsDict['mode']=='fasta':
        df[ac] = df[ac].str.replace(' // ', ';')
        df[dc] = df[dc].str.replace(' // ', ';')
    
    # Generate columns with pn and sn to check
    df = pd.merge(
        df,
        dfw.loc[:, [pp, 'pn', 'sn']].groupby(pp).agg(list),
        how='left',
        on=pp
        )

    return df


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
    q2len = {} # used when calculating MPP in fasta mode
    if paramsDict['mode'].lower() == 'fasta':

        # read fasta
        t=time()
        try:
            target_q, decoy_q = fastaReader(paramsDict)
            q2len = get_q2len(target_q, decoy_q)
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
        d_colName, acc_colName = paramsDict['fasta_params']['candidate_d'], paramsDict['fasta_params']['candidate_a']

        # add these new columns
        df[acc_colName] = acc_column
        df[d_colName] = d_column
        
        logging.info(f"{d_colName} and {acc_colName} columns with candidate proteins were created")

        # If column params section is note created, add it (it is used in MPP calculation)
        if "column_params" not in paramsDict.keys(): 
            paramsDict["column_params"] = {}

        
        paramsDict["column_params"]['candidate_d'] = d_colName
        paramsDict["column_params"]['candidate_a'] = acc_colName
        paramsDict["column_params"]['sep_char'] = " // "
        
        #paramsDict['_additional_column'] = [d_colName] # another from which extract information of most probable protein
        #paramsDict['_replace_delim'] = True # Protein delimiter is " // ". We want to change it to ; in the end (but only in fasta mode)


    #
    # Calculate most probable protein
    #
    logging.info(f'Calculating most probable protein...')
    if paramsDict["column_params"]['candidate_a'] not in df.columns:
    # if np.any([i not in df.columns for i in paramsDict["column_params"]['prot_column']]):
        logging.error(f'{paramsDict["column_params"]["candidate_a"]} column not found and MPP cannot be calculated')
        sys.exit(-4)


    t = time()
    df = getMostProbableProtein(df, paramsDict, q2len)
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
    FROM CONFIG:
        {script_name} -c "path to YAML config file"
    
    FROM COMMAND LINE (iSanXoT):
        Column mode:
        {script_name} -i "Path\To\Input.File" -o "Path\To\Output.File" -s "Sequence" -q "Protein_Accession_Candidate" -qm "Protein_Accessions_MPP" -w 4
    
        Fasta mode:
        {script_name} -i "Path\To\Input.File" -o "Path\To\Output.File" -s "Sequence" -f "Path\To\Fasta.fa" -cd "Protein_Description_Candidate" -ca "Protein_Accession_Candidate" -qm "Protein_Accessions_MPP" -md "Protein_Descriptions_MPP" -w 4
''')


    # Parse command-line arguments (config)
    parser.add_argument('-c', '--config', dest='config', metavar='FILE', type=str,
        help='Path to YAML file containing parameters')
    

    # Parse command-line arguments (non-config)
    parser.add_argument('-i','--infile', nargs="+", help='Path to files containing PSM table')
    parser.add_argument('-o','--outfile', nargs="+", help='Path to ouput file')
    parser.add_argument('-s',  '--plainseq', type=str, help='Name of the column containing peptide sequence')
    parser.add_argument('-md',  '--mdesc', type=str, default="Protein_Description_MPP", help='Name of the output column with most probable descriptions')
    parser.add_argument('-qm',  '--macc', type=str, default="Protein_Accession_MPP", help='Name of the output column with most probable accessions')
    parser.add_argument('-rx',  '--regex', type=str, default="", help='Regex applied in case of ties (/regex1/regex2/regex3/.../')
    parser.add_argument('-lx',  '--len', type=int, default=0, help='Consider sequence length in prioritization')
    parser.add_argument('-m',  '--mode', type=str, default="column", help='Select mode of execution: fasta/column')

    parser.add_argument('-f',  '--fasta', type=str, help='Path to fasta file used to identify candidate proteins')
    parser.add_argument('-dy',  '--decoy', type=str, default="DECOY_", help='decoy prefix in fasta')
    parser.add_argument('-ile',  '--isoleu', type=str, default="L", help='Convert L, I and J to the selected letter')
    
    parser.add_argument('-cd',  '--cdesc', type=str, default="Protein_Description_Candidate", help='Name of the output (fasta mode) column with candidate descriptions')
    parser.add_argument('-ca',  '--cacc', type=str, default="Protein_Accessions_Candidate", help='Name of the output (fasta mode) column with candidate accessions')
    
    parser.add_argument('-pcd',  '--pcdesc', type=str, default="", help='Name of the input (column mode) column with candidate descriptions')
    parser.add_argument('-q',  '--pcacc', type=str, default="", help='Name of the input (column mode) column with candidate accessions')


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

            "mpp_d": args.mdesc,
            "mpp_a": args.macc,
            "regex": args.regex,
            "len_seq": args.len,
            "mode": args.mode,
            
            "fasta_params": {
                "fasta": args.fasta,
                "decoy_prefix": args.decoy,
                "iso_leucine": args.isoleu,
                "candidate_d": args.cdesc,
                "candidate_a": args.cacc,
            },

            "column_params": {
                "candidate_d": args.pcdesc,
                "candidate_a": args.pcacc,
                "sep_char": args.sep
            },
            
            "n_cores": args.n_workers,
        }
    
    paramsDict['regex'] = [re.compile(i, re.IGNORECASE) for i in re.split(r'(?<!\\)/', paramsDict['regex'].strip('/ '))]
        

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
