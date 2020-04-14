#!/usr/bin/python

# Module metadata variables
__author__ = "Jose Rodriguez"
__credits__ = ["Jose Rodriguez", "Jesus Vazquez"]
__license__ = "Creative Commons Attribution-NonCommercial-NoDerivs 4.0 Unported License https://creativecommons.org/licenses/by-nc-nd/4.0/"
__version__ = "0.0.1"
__maintainer__ = "Jose Rodriguez"
__email__ = "jmrodriguezc@cnic.es"
__status__ = "Development"

import os
import sys
import glob
import argparse
import logging
import copy
import re
import io
import json
import yaml
import shlex
import pandas as pd


####################
# Global variables #
####################
EXPERIMENTS = None # obtained from the CREATE_ID command
ISANXOT_SRC_HOME = f"{os.path.dirname(__file__)}/.."
ISANXOT_PYTHON_EXEC = sys.executable


###################
# Local functions #
###################
def read_command_table(ifiles):
    '''
    read the multiple input files to string and split by command
    create a list of tuples (command, dataframe with parameters)
    dropping empty rows and empty columns
    create a dictionary with the concatenation of dataframes for each command
    {command} = concat.dataframes
    '''
    indata = dict()
    idta = ''
    # read the multiple input files to string and split by command
    for f in ifiles:
        with open(f, "r") as file:
            idta += file.read()
    # create a list of tuples (command, dataframe with parameters)
    match = re.findall(r'\s*#([^\s]*)\s*([^#]*)', idta, re.I | re.M)
    idta = [(c,pd.read_csv(io.StringIO(l), sep='\t', dtype=str, skip_blank_lines=True).dropna(how="all").dropna(how="all", axis=1).astype('str')) for c,l in match]
    # create a dictionary with the concatenation of dataframes for each command
    for c, d in idta:
        # discard the rows when the first empty columns
        if not d.empty:
            l = list(d[d.iloc[:,0] == 'nan'].index)
            d = d.drop(l)
        if c in indata:
            indata[c] = pd.concat( [indata[c], d], sort=False)
        else:
            for c2 in c.split('-'):
                indata[c2] = d
    return indata

def check_command_parameters(indata):
    '''
    check the tasktable parameters for each command:
        1. check whether there are duplicates in the output directories
        2. check whether the values of '* Var(x)' are False or a float    
    '''
    # local functions
    def get_set_unique_list(list):
        uniq_set = set()
        uniq_list = []
        dup_list = []
        for item in list:
            if item not in uniq_set:
                uniq_list.append(item)
                uniq_set.add(item)
            else:
                dup_list.append(item)
        return [uniq_list, dup_list]

    # init variables
    outdirs = []
    # iterate over all commands
    for cmd,df in indata.items():
        # discard RATIOS command because the tasktable is duplicated with WSPP_SBT
        if cmd != 'RATIOS':
            # create a list with all output directories for each command
            if 'name' in df.columns:
                outdirs.extend(df['name'].values)
            elif 'output' in df.columns:
                outdirs.extend(df['output'].values)

    # check if there are duplicates in the output directories
    if outdirs:
        if len(outdirs) != len(set(outdirs)):
            uniq_list, dup_list = get_set_unique_list(outdirs)
            sms = "ERROR!! There are dupplicated outdirs: {}".format(dup_list)
            print(sms) # message to stdout with logging output
            sys.exit(sms)
    
def replace_val_rec(data, repl):
    '''
    Replace substring from the list of dictionary, recursively
    '''
    if isinstance(data, dict):
        return {k: replace_val_rec(v, repl) for k, v in data.items()}
    elif isinstance(data, list):
        return [replace_val_rec(i, repl) for i in data]
    elif isinstance(data, str):
        pattern = re.compile("|".join(repl.keys()))
        return pattern.sub(lambda m: repl[re.escape(m.group(0))], str(data))
    else:
        return data

def check_val_in_dict(data, stxt):
    '''
    Check if string is within the dictionary (two levels)
    '''
    if stxt in data:
        return True
    else:
        False
    return False
      
def add_values(df, tpl):
    '''
    Add the parameters into dictionary
    '''
    l = [tuple(r) for r in df.values]
    for k,v in l:
        tpl[k] = v

def _add_more_params(name, params):
    '''
    Add the more_params to the specific rule
    '''
    out = ''
    if params != 'nan':
        try:
            jparams = json.loads(params)
            for k,pr in jparams.items():
                if k in name:
                    out += pr
        except:
            out = params
        return out
    else:
        return out

def _add_datparams_params(p, trule, dat):
    d = trule['parameters'][p]
    fk = list(d.keys())
    if fk:
        k = str(fk[0])
        # Exceptions in the 'Variance' parameters:
        # If the value is not false, apply the new variance
        # Otherwise, by default
        if p.endswith('Var(x)'):
            if dat.upper() != 'FALSE':
                del trule['infiles']['-V'] # delete the infile with the variance (by default)
                trule['parameters'][p][k] = dat
            else:
                del trule['parameters'][p] # delete the optional parameter of variance
        # Exceptions in the 'Tag' parameters:
        # Update the template values (not overwrite from the given data)
        elif p.endswith('Tag'):
            trule['parameters'][p][k] += ' & '+ dat
        # The rest of kind of parameters
        else:
            trule['parameters'][p][k] = dat

def _add_datparams_moreparams(p, trule, dat):
    trule['more_params'] = _add_more_params(trule['name'], str(dat))

def _replace_datparams(dat, trule, label):
    dat = dat.replace(" ", "")
    for k,tr in trule.items():
        if label in tr:
            l = []
            for d in dat.split(','):
                l.append( tr.replace(label, d) )
            trule[k] = ";".join(l)

def _replace_datparams_params(dat, trule, label):
    dat = dat.replace(" ", "")
    for k,tr in trule.items():
        if label in tr:
            trule[k] = tr.replace(label, dat)

def add_datparams(p, trule, ival):
    # Substitute '*' by the global experiments (coming from the CREATE_ID command)
    if '*' in ival:
        val = ''
        for exp in EXPERIMENTS.split(','):
            if val == '':
                val += ival.replace('*', exp)
            else:
                val += ','+ival.replace('*', exp)
    else:
        val = ival
        
    # Replace the label for the value for each section: infiles, outfiles, and parameters
    if p == 'experiment':        
        l = '__WF_'+p.upper()+'__'
        _replace_datparams(val, trule['infiles'],  l)
        _replace_datparams(val, trule['outfiles'], l)
        trule['parameters'] = replace_val_rec(trule['parameters'], {l: val})
        
    elif p == 'name':
        l = '__WF_'+p.upper()+'__'
        _replace_datparams(val, trule['infiles'],  l)
        _replace_datparams(val, trule['outfiles'], l)
        trule['parameters'] = replace_val_rec(trule['parameters'], {l: val})
        
    elif p == 'input':
        l = '__WF_'+p.upper()+'__'
        _replace_datparams(val, trule['infiles'],  l)
        _replace_datparams(val, trule['outfiles'], l)
        trule['parameters'] = replace_val_rec(trule['parameters'], {l: val})

    elif p == 'output':
        l = '__WF_'+p.upper()+'__'
        _replace_datparams(val, trule['infiles'],  l)
        _replace_datparams(val, trule['outfiles'], l)
        trule['parameters'] = replace_val_rec(trule['parameters'], {l: val})

    elif p == 'level':
        l = '__WF_'+p.upper()+'__'
        _replace_datparams(val, trule['infiles'],  l)
        _replace_datparams(val, trule['outfiles'], l)
        trule['parameters'] = replace_val_rec(trule['parameters'], {l: val})

    elif p == 'inf_level':
        l = '__WF_'+p.upper()+'__'
        _replace_datparams(val, trule['infiles'],  l)
        _replace_datparams(val, trule['outfiles'], l)
        trule['parameters'] = replace_val_rec(trule['parameters'], {l: val})
        
    elif p == 'sup_level':
        l = '__WF_'+p.upper()+'__'
        _replace_datparams(val, trule['infiles'],  l)
        _replace_datparams(val, trule['outfiles'], l)
        trule['parameters'] = replace_val_rec(trule['parameters'], {l: val})
        
    elif p == 'rel_table':
        l = '__WF_'+p.upper()+'__'
        _replace_datparams(val, trule['infiles'],  l)
        _replace_datparams(val, trule['outfiles'], l)
        trule['parameters'] = replace_val_rec(trule['parameters'], {l: val})
        
    elif p == 'ratio_numerator':
        if trule['parameters'] is not None and 'tags' in trule['parameters']:
            r = val.replace(",","-")
            _replace_datparams_params(r, trule['parameters']['tags'], '__WF_RATIO_NUM__')
            
    elif p == 'ratio_denominator':
        if trule['parameters'] is not None and 'tags' in trule['parameters']:
            r = val.replace(",","-")
            _replace_datparams_params(r, trule['parameters']['tags'], '__WF_RATIO_DEN__')
            
    elif p == 'more_params':
        _add_datparams_moreparams(p, trule, val)

    if trule['parameters'] is not None and p in trule['parameters']:
        _add_datparams_params(p, trule, val)



def _add_corrected_files(trule):
    '''
    add the correct files if '*' asterisk is in the path
    '''
    for k,files in trule.items():
        if '*' in files:
            l = []
            for file in files.split(";"):
                l += [f for f in glob.glob(file, recursive=True)]
            if len(l) > 0:
                trule[k] = ";".join(l)
    return trule

def add_corrected_files_intrinsic(trule, outfiles):
    '''
    add the correct files if '*' asterisk is in the path from the given list of outputs
    '''
    for k,files in trule.items():
        if '*' in files:
            l = []
            for file in files.split(";"):
                sf = re.split(r'/\*+/', file)
                if len(sf) > 1:
                    b = sf[0]
                    e = sf[1]
                    for outfile in outfiles:
                        if outfile.startswith(b) and outfile.endswith(e):
                            l += [outfile]
            if len(l) > 0:
                trule[k] = ";".join(l)
    return trule
    
def add_rules(row, *trules):
    '''
    Create rule list for each command
    '''
    r = list(copy.deepcopy(trules))
    data_params = list(row.index.values)
    for i in range(len(r)):
        trule = r[i]
        for p in data_params:
            # add data parameters in the infiles/outfiles
            # add data_parameters into the parameters section for each rule
            add_datparams(p, trule, row.loc[p])
        # add the correct files if '*' asterisk is in the path
        # at the moment, only for 'infiles'
        trule['infiles'] = _add_corrected_files(trule['infiles'])
    return r

def add_rules_createID(df, trules, val):
    '''
    Create rule list for each command
    '''
    r = list(copy.deepcopy(trules))
    for i in range(len(r)):
        trule = r[i]
        # add data parameters in the infiles/outfiles
        # add data_parameters into the parameters section for each rule
        add_datparams('experiment', trule, val)
    return [r]
    
def _param_str_to_dict(s):
    cprs = shlex.split(s)
    d = {}
    i = 0
    while i < len(cprs):
        cpr = cprs[i]
        if cpr.startswith('-'):
            if len(cprs) > i+1 and not cprs[i+1].startswith('-'):
                d[cpr] = cprs[i+1]
                i = i + 2
            else:
                d[cpr] = ''
                i = i + 1
    return d

def _str_cline(k,v):
    c = ''
    if k.startswith("--"):
        c = '{}="{}" '.format(k,str(v)) if str(v) != '' else ''
    else:
        c = '{} "{}" '.format(k,str(v)) if str(v) != '' else ''    
    return c
    
def add_params_cline(rules):
    '''
    Add the whole parametes (infiles, outfiles, params) to command line    
    '''
    # For each rules, create string for the command line with the infiles, outfiles and parameters
    for r in rules:
        r = [r] if isinstance(r,dict) else r
        for i in range(len(r)):
            trule = r[i]
            cparams = ''
            # Create command line with the input, output files and the parameters
            for p in ['infiles','outfiles','parameters']:
                if trule[p] is not None:
                    for k,v in trule[p].items():
                        if isinstance(v,dict):
                            for kv,vv in v.items():
                                cparams += _str_cline(kv,vv)
                        elif isinstance(v,list) and len(v) > 0:
                            cparams += _str_cline(k,'" "'.join(v))
                        elif isinstance(v,str):
                            cparams += _str_cline(k,v)
            # Now in the case we have 'more_params'
            # we create dict with the actual parameters (from the command line as str) and the more_params
            # add or replace the more_params with the actual parameters
            if trule['more_params'] is not None and trule['more_params'] != '':
                v = str(trule['more_params'])
                ccprs = _param_str_to_dict(cparams) # get dict from old params
                ncprs = _param_str_to_dict(v) # get dict from new more_params
                for nk,cpr in ncprs.items():
                    ccprs[nk] = cpr
                # create again the cparams
                cparams = ''
                for kv,vv in ccprs.items():
                    cparams += '{} "{}" '.format(kv,str(vv)) if str(vv) != '' else ''
            # add the command line
            trule['cline'] += " "+cparams
        
    
#################
# Main function #
#################
def main(args):
    '''
    Main function
    '''
    # read the multiple input files (TSV) from the input dir to string
    # split by command
    # create a list of tuples (command, dataframe with parameters)
    # dropping empty rows and empty columns
    # create a dictionary with the concatenation of dataframes for each command
    # {command} = concat.dataframes
    logging.info("read the multiple input files with the commands")
    infiles = glob.glob( os.path.join(args.indir,"*.tsv"), recursive=True )    
    indata = read_command_table(infiles)
    
    
    # TODO CHECK THE INPUT TABLE!!!!!
    # COMPRUEBA QUE:
    # 1. La columna de 'names' es unica
    # 2. Que para las columnas de '* Var(x)' los valores o es False o un float
    logging.info("check the tasktable parameters for each command")
    check_command_parameters(indata)
    
    
    # init the output file with the given attributes of workflow
    logging.info("init the output file with the attributes of given workflow")
    with open(args.attfile, 'r') as stream:
        try:
            tpl = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            sms = "ERROR!! Reading the attributes file of workflow: {}".format(exc)
            print(sms) # message to stdout with logging output
            sys.exit(sms)
    # remove the date_id folder from the data files
    tpl['datfiles'] = replace_val_rec(tpl['datfiles'], {(tpl['date']+'\/'): ''})

    

    # read the templates of commands
    logging.info("read the template of commands")
    with open(args.intpl, 'r') as stream:
        try:
            tpl_cmds = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            sms = "ERROR!! Reading the template of commands: {}".format(exc)
            print(sms) # message to stdout with logging output
            sys.exit(sms)

    
    # get the unique commands from the input table
    logging.info("get the unique commands from the input table")
    cmds = list(indata.keys())
    dels = [i for i in tpl_cmds['commands'] if not (i['name'] in cmds)]
    for c in dels:
        del tpl_cmds['commands'][ tpl_cmds['commands'].index(c) ]

    
    # merge the workflow attributes with the templates of commands
    tpl.update(tpl_cmds)

               
    # replace the constants for the command templates
    logging.info("replace the constants for the command templates")
    repl = {        
            '__ISANXOT_SRC_HOME__':         ISANXOT_SRC_HOME,
            '__ISANXOT_PYTHON_EXEC__':      ISANXOT_PYTHON_EXEC,
            '__NCPU__':                     str(tpl['ncpu']),
            '__WF_VERBOSE__':               str(tpl['verbose']),
            '__MAIN_INPUTS_EXPDIR__':       tpl['prj_workspace']['expdir'],
            '__MAIN_INPUTS_TMPDIR__':       tpl['prj_workspace']['tmpdir'],
            '__MAIN_INPUTS_RELDIR__':       tpl['prj_workspace']['reldir'],
            '__MAIN_INPUTS_RSTDIR__':       tpl['prj_workspace']['rstdir'],
            '__MAIN_INPUTS_LOGDIR__':       tpl['prj_workspace']['logdir'],
            '__MAIN_INPUTS_DBFILE__':       tpl['main_inputs']['dbfile'],
            '__MAIN_INPUTS_CATFILE__':      tpl['main_inputs']['catfile'],
            '__MAIN_INPUTS_INDIR__':        tpl['main_inputs']['indir'],
    }
    # add the replacements for the data files of tasktable commands
    for datfile in tpl['datfiles']:
        l = "__MAIN_INPUTS_DATFILE_{}__".format(datfile['type'].upper())
        repl[l] = datfile['file']    
    tpl = replace_val_rec(tpl, repl)
    

    # mandatory: work with the CREATE_ID command
    cmd = 'CREATE_ID'
    if cmd in indata:
        df = indata['CREATE_ID']
        icmd = [i for i,c in enumerate(tpl['commands']) if c['name'] == cmd]
        if icmd:
            i = icmd[0]
            # assign the global variable
            # get the list of unique experiments (in string)
            global EXPERIMENTS
            EXPERIMENTS = ",".join(df['experiment'].unique()).replace(" ", "")
            # replace constants
            tpl['commands'][i] = replace_val_rec(tpl['commands'][i], repl)
            # add the parameters into each rule
            tpl['commands'][i]['rules'] = add_rules_createID(df, tpl['commands'][i]['rules'], EXPERIMENTS)
            # add the whole parametes (infiles, outfiles, params) to command line
            add_params_cline( tpl['commands'][i]['rules'] )
        del indata[cmd]
    

    logging.info("fill the parameters and rules for each command")
    for cmd,df in indata.items():
        if cmd == 'RATIOS':
            icmd = [i for i,c in enumerate(tpl['commands']) if c['name'] == cmd]
            if icmd:
                i = icmd[0]
                # replace constants
                tpl['commands'][i] = replace_val_rec(tpl['commands'][i], repl)
                # add the parameters into each rule
                tpl['commands'][i]['rules'] = add_rules_createID(df, tpl['commands'][i]['rules'], EXPERIMENTS)
                # add the whole parametes (infiles, outfiles, params) to command line
                # add_params_cline( tpl['commands'][i]['rules'] )
                
        else: # the rest of commands            
            icmd = [i for i,c in enumerate(tpl['commands']) if c['name'] == cmd]
            if icmd:
                i = icmd[0]
                # replace constants
                tpl['commands'][i] = replace_val_rec(tpl['commands'][i], repl)
                # duplicate rules for each row data
                # add the parameters into each rule
                tpl['commands'][i]['rules'] = list(df.apply( add_rules, args=(tpl['commands'][i]['rules']), axis=1))
                # add the whole parametes (infiles, outfiles, params) to command line
                # add_params_cline( tpl['commands'][i]['rules'] )


    logging.info("fill the parameters with intrinsic files in the commands")
    # get the list of output files
    outfiles = []
    for i in range(len(tpl['commands'])):
        for j in range(len(tpl['commands'][i]['rules'])):
            for k in range(len(tpl['commands'][i]['rules'][j])):
                trule = tpl['commands'][i]['rules'][j][k]
                outfiles += trule['outfiles'].values()
    # replace the input files that contains the "recursive value" (**)
    for i in range(len(tpl['commands'])):
        for j in range(len(tpl['commands'][i]['rules'])):
            for k in range(len(tpl['commands'][i]['rules'][j])):
                trule = tpl['commands'][i]['rules'][j][k]
                trule['infiles'] = add_corrected_files_intrinsic(trule['infiles'], outfiles)

    

    logging.info("fill the clines")
    # add the whole parametes (infiles, outfiles, params) to command line
    for i in range(len(tpl['commands'])):
        add_params_cline( tpl['commands'][i]['rules'] )


    
    # write the output file
    logging.info("write the output file")
    with open(args.outfile, 'w') as file:
        yaml.dump(tpl, file, sort_keys=False, width=float("inf"))
    

        



if __name__ == "__main__":
    # parse arguments
    parser = argparse.ArgumentParser(
        description='Convert the table in config file for snakemake',
        epilog='''
        Example:
            python table2cfg.py
        ''')        
    parser.add_argument('-a', '--attfile', required=True, help='Input file with the attributes of given workflow: name, ncpu, version, etc. (YMAL format)')
    parser.add_argument('-t', '--intpl',   required=True, help='Template of commands (yaml format)')
    parser.add_argument('-i', '--indir',   required=True, help='Input directory where iSanXoT config files are saved')
    parser.add_argument('-o', '--outfile', required=True, help='Config file to be execute by snakemake')
    parser.add_argument('-vv', dest='verbose', action='store_true', help="Increase output verbosity")
    args = parser.parse_args()

    # get the name of script
    script_name = os.path.splitext(os.path.basename(__file__))[0].upper()

    # logging debug level. By default, info level
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG,
                            stream=sys.stdout,
                            format=script_name+' - '+str(os.getpid())+' - %(asctime)s - %(levelname)s - %(message)s',
                            datefmt='%m/%d/%Y %I:%M:%S %p')
    else:
        logging.basicConfig(level=logging.INFO,
                            stream=sys.stdout,
                            format=script_name+' - '+str(os.getpid())+' - %(asctime)s - %(levelname)s - %(message)s',
                            datefmt='%m/%d/%Y %I:%M:%S %p')

    # start main function
    logging.info('start script: '+"{0}".format(" ".join([x for x in sys.argv])))
    main(args)
    logging.info('end script')
