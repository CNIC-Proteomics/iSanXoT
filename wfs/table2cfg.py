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
    for f in ifiles.split(";"):
        with open(f, "r") as file:
            idta += file.read()
    match = re.findall(r'\s*#([^\s]*)\s*([^#]*)', idta, re.I | re.M)
    idta = [(c,pd.read_csv(io.StringIO(l), sep='\t', dtype=str, skip_blank_lines=True).dropna(how="all").dropna(how="all", axis=1).astype('str')) for c,l in match]    
    for c, d in idta:
        if c in indata:
            indata[c] = pd.concat( [indata[c], d], sort=False)
        else:
            for c2 in c.split('&'):
                indata[c2] = d
    return indata

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



    
def add_rules(row, *trules):
    '''
    Create rule list for each command
    '''
    r = copy.deepcopy(trules)
    data_params = list(row.index.values)
    for i in range(len(r)):
        trule = r[i]
        for p in data_params:            
            # add data parameters in the infiles/outfiles
            # add data_parameters into the parameters section for each rule
            add_datparams(p, trule, row.loc[p])
    return r

def add_rules_createID(df, trules, val):
    '''
    Create rule list for each command
    '''
    r = tuple(copy.deepcopy(trules))
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
    # read the multiple input files to string and split by command
    # create a list of tuples (command, dataframe with parameters)
    # dropping empty rows and empty columns
    # create a dictionary with the concatenation of dataframes for each command
    # {command} = concat.dataframes
    logging.info("read the multiple input files with the commands")
    indata = read_command_table(args.infiles)
       
    # TODO CHECK THE INPUT TABLE!!!!!
    # COMPRUEBA QUE:
    # 1. La columna de 'names' es unica
    # 2. Que para las columnas de '* Var(x)' los valores o es False o un float
    
    
    
    # read the templates of commands
    logging.info("read the template of commands")
    with open(args.intpl, 'r') as stream:
        try:
            tpl = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            sys.exit("ERROR!! Reading the template of commands: {}".format(exc))
       
    
    # get the unique commands from the input table
    logging.info("get the unique commands from the input table")
    cmds = list(indata.keys())
    dels = [i for i in tpl['commands'] if not (i['name'] in cmds)]
    for c in dels:
        del tpl['commands'][ tpl['commands'].index(c) ]
    
    
    logging.info("fill the parameters and rules for each command")
    for cmd,df in indata.items():
        if cmd == 'MAIN_INPUTS': # always HAS TO BE THE FIRST COMMAND from the input dataframe
            # add main inputs
            # replace constant
            logging.info("add main inputs in config")
            add_values(indata['MAIN_INPUTS'], tpl['main_inputs'])
            repl = {
                    '__MAIN_INPUTS_OUTDIR__':  tpl['main_inputs']['outdir']
            }
            tpl['main_inputs'] = replace_val_rec(tpl['main_inputs'], repl)
                        
            # replace constants from the main_inputs
            # This variable is used for the next commands!!
            logging.info("create fill the parameters for each command")
            repl = {
                
                    '__ISANXOT_SRC_HOME__':         os.environ['ISANXOT_SRC_HOME'],
                    '__ISANXOT_PYTHON3x_HOME__':    os.environ['ISANXOT_PYTHON3x_HOME'],                    
                    '__NCPU__':                     str(tpl['ncpu']),
                    '__WF_VERBOSE__':               str(tpl['verbose']),
                    '__MAIN_INPUTS_DATFILE_INP__':  tpl['main_inputs']['datfiles']['inp'],
                    '__MAIN_INPUTS_DATFILE_IDE__':  tpl['main_inputs']['datfiles']['ide'],
                    '__MAIN_INPUTS_DATFILE_STS__':  tpl['main_inputs']['datfiles']['sts'],
                    '__MAIN_INPUTS_DATFILE_INT__':  tpl['main_inputs']['datfiles']['int'],
                    '__MAIN_INPUTS_DATFILE_REP__':  tpl['main_inputs']['datfiles']['rep'],
                    '__MAIN_INPUTS_DBFILE__':       tpl['main_inputs']['dbfile'],
                    '__MAIN_INPUTS_CATFILE__':      tpl['main_inputs']['catfile'],
                    '__MAIN_INPUTS_INDIR__':        tpl['main_inputs']['indir'],
                    '__MAIN_INPUTS_OUTDIR__':       tpl['main_inputs']['outdir'],                    
                    '__MAIN_INPUTS_EXPDIR__':       tpl['main_inputs']['expdir'],
                    '__MAIN_INPUTS_TMPDIR__':       tpl['main_inputs']['tmpdir'],
                    '__MAIN_INPUTS_RSTDIR__':       tpl['main_inputs']['rstdir'],
                    '__MAIN_INPUTS_LOGDIR__':       tpl['main_inputs']['logdir'],
            }
            
        elif cmd == 'CREATE_ID':
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

        elif cmd == 'RATIOS':
            icmd = [i for i,c in enumerate(tpl['commands']) if c['name'] == cmd]
            if icmd:
                i = icmd[0]
                # replace constants
                tpl['commands'][i] = replace_val_rec(tpl['commands'][i], repl)
                # add the parameters into each rule
                tpl['commands'][i]['rules'] = add_rules_createID(df, tpl['commands'][i]['rules'], EXPERIMENTS)
                # add the whole parametes (infiles, outfiles, params) to command line
                add_params_cline( tpl['commands'][i]['rules'] )
                
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
    parser.add_argument('-ii', '--infiles',  required=True, help='Multiple input files separated by comma')
    parser.add_argument('-t',  '--intpl',    required=True, help='Template of commands (yaml format)')
    parser.add_argument('-o',  '--outfile',   required=True, help='Config file to be execute by snakemake')
    parser.add_argument('-vv', dest='verbose', action='store_true', help="Increase output verbosity")
    args = parser.parse_args()

    # get the name of script
    script_name = os.path.splitext(os.path.basename(__file__))[0].upper()

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
