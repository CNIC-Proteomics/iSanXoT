#!/usr/bin/python

# Module metadata variables
__author__ = "Jose Rodriguez"
__credits__ = ["Jose Rodriguez", "Jesus Vazquez"]
__license__ = "Creative Commons Attribution-NonCommercial-NoDerivs 4.0 Unported License https://creativecommons.org/licenses/by-nc-nd/4.0/"
__version__ = "0.0.1"
__maintainer__ = "Jose Rodriguez"
__email__ = "jmrodriguezc@cnic.es"
__status__ = "Development"

#########################
# Import global modules #
#########################
import os
import sys
# import glob
import argparse
import logging
import copy
import re
import json
import yaml
import shlex
import numpy as np
import pandas as pd
import itertools

####################
# Global variables #
####################
import gvars

__EXPDIR__  = None
__JOBDIR__  = None
__RELDIR__  = None
__RSTDIR__  = None
__LOGDIR__  = None
__STADIR__  = None
__IDQFIL__  = None

OUTPUTS_FOR_CMD     = None
TPL_DATE            = None
RULE_SUFFIX         = None

OUTFILES = []

#########################
# Import local packages #
#########################
sys.path.append(gvars.ISANXOT_LIB_COMMON)
import common


###################
# Local functions #
###################
def check_command_parameters(indata):
    '''
    check the tasktable parameters for each command:
        1. check whether there are duplicates in the output directories
        2. check whether the values of '* Var(x)' are False or a float (deprecated)??
        3. NOT WORK HERE because the input file does not exist yet!!! For Level_Creator: check if the column headers are in the input files and there are not repeated.
        4. NOT WORK HERE because the input file does not exist yet!!! For Rels_Creator: check if the column headers are in the input files and there are not repeated.
        # -que ya existen las tablas de relaciones que necesitamos para todas las integraciones ???

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
    def check_headers(file, headers):
        '''
        get the list of elements that are not included in the cols and if there are duplicated
        '''
        cols = pd.read_csv(file, nrows=0, sep="\t", comment='#', index_col=False).columns.tolist()
        # remove cases with [] and {}
        headers = [h for h in headers if not ('[' in h and ']' in h) and not ('{' in h and '}' in h)]
        return [e for e in headers if e not in cols or cols.count(e) > 1]
    
    # create a list with all output directories for each command
    # create a dictionary with the output for each command
    outdirs = []
    outfiles = {}
    # iterate over all commands
    for cmd,indat in indata.items():
        if 'table' in indat:
            df = indat['table']
            outs = []
            if 'output' in df.columns and 'level' in df.columns:
                outs = list((df['output']+'/'+df['level']).values)
            if 'output' in df.columns and 'sup_level' in df.columns:
                outs = list((df['output']+'/'+df['sup_level']).values)
            if outs:
                outdirs.extend(outs)
                for o in outs:
                    outfiles[o] = cmd
        
        #  BEGIN:  NOT WORK HERE because the input file does not exist yet!!!
        
        # # 3. For Level_Creator: check if the column headers are in the input files and there are not repeated.
        # if cmd == 'LEVEL_CREATOR':
        #     # create the headers
        #     # extract the unique values that below to specific columns
        #     h = list(df.groupby(['feat_col','ratio_numerator','ratio_denominator']).groups.keys())
        #     h = [re.split(r'\s*,\s*',x) for x in list(itertools.chain(*h))]
        #     h = np.unique([i for sublist in h for i in sublist])
        #     # 'Experiment' column is mandatory
        #     headers = np.concatenate( (['Experiment'], h) )
        #     # check if headears are included in the input file
        #     if os.path.isfile(__IDQFIL__):
        #         elems_not_included = check_headers(__IDQFIL__, headers)
        #         if len(elems_not_included) > 0:
        #             sms = "ERROR!! These headers {} are not included in the file {}".format(elems_not_included, __IDQFIL__)
        #             print(sms) # message to stdout with logging output
        #             sys.exit(sms)
        #     else:
        #         sms = "ERROR!! The input file {} does not exist".format(__IDQFIL__)
        #         print(sms) # message to stdout with logging output
        #         sys.exit(sms)

        # # 4. For Rels_Creator: check if the column headers are in the input files and there are not repeated.
        # elif cmd == 'RELS_CREATOR':
        #     # check if headers are in the input file
        #     cols = ['inf_infiles'] + [c for c in df.columns if c in ['inf_headers', 'sup_headers', 'thr_headers']]
        #     sms = ''
        #     for x in df[cols].itertuples(index=False, name=None):
        #         file = x[0]
        #         h = x[1:]
        #         if os.path.isfile(file):
        #             elems_not_included = check_headers(file, h)
        #             if len(elems_not_included) > 0:
        #                 sms += "ERROR!! These headers {} are not included in the file {}\n".format(elems_not_included, file)
        #         else:
        #             sms += "ERROR!! The input file {} does not exist\n".format(file)
        #     if sms != '':
        #         print(sms) # message to stdout with logging output
        #         sys.exit(sms)
        
        #  END:  NOT WORK HERE because the input file does not exist yet!!!

    # 2. check if there are duplicates in the output directories
    if outdirs:
        if len(outdirs) != len(set(outdirs)):
            uniq_list, dup_list = get_set_unique_list(outdirs)
            sms = "ERROR!! There are dupplicated outdirs: {}".format(dup_list)
            print(sms) # message to stdout with logging output
            sys.exit(sms)
    
    # return all outfiles
    return outfiles.keys()

def read_tpl_command(path, cmd_id):
    cmd_tpl = None
    # get the file with the template of commands
    file = f"{path}/{cmd_id.lower()}.yaml"
    if os.path.isfile(file):
        # read the templates of commands
        with open(file, 'r') as stream:
            try:
                cmd_tpl = yaml.safe_load(stream)
                cmd_tpl = cmd_tpl[0]
            except yaml.YAMLError as exc:
                sms = "ERROR!! Reading the template of commands: {}".format(exc)
                print(sms) # message to stdout with logging output
                sys.exit(sms)
    return cmd_tpl

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
            params = params.replace('\\','/') # for windows path's
            jparams = json.loads(params)
            for k,pr in jparams.items():
                if k in name:
                    out += pr
        except:
            out = ''
        return out
    else:
        return out

def _add_datparams_params(p, trule, dat):
    # add parameters into 'parameters' coming from the task-table
    if trule['parameters'] is not None and p in trule['parameters']:
        fk = list(trule['parameters'][p].keys())
        if fk:
            k = str(fk[0])
            # Exceptions in the 'Variance' parameters:
            # If the value is not false, apply the new variance
            # Otherwise, by default
            if p.endswith('Var(x)') and dat != 'nan':
                if dat.upper() != 'FALSE':
                    del trule['infiles']['-V'] # delete the infile with the variance (by default)
                    trule['parameters'][p][k] = dat
                else:
                    del trule['parameters'][p] # delete the optional parameter of variance
            # Exceptions in the 'Tag' parameters:
            # Update the template values (not overwrite from the given data)
            elif p.endswith('tag') and dat != 'nan':
                if trule['parameters'][p][k] == '':
                    trule['parameters'][p][k] = dat
                else:
                    trule['parameters'][p][k] += ' & '+ dat
            # The rest of kind of parameters
            elif dat and dat != 'nan':
                trule['parameters'][p][k] = dat

    # add optional parameters into 'infiles' coming from the task-table
    # the tag parameter to the program, it is the same name than the header table
    elif trule['infiles'] is not None and '--'+p in trule['infiles']:
        if dat and dat != 'nan':
            trule['infiles']['--'+p] = dat
        

def _add_datparams_moreparams(p, trule, dat):
    trule['more_params'] = _add_more_params(trule['name'], str(dat))

def _replace_datparams(dat, trule, label):
    for k,tr in trule.items():
        if label in tr:
            l = []
            for d in dat.split(','):
                d = d.strip() # remove all the leading and trailing whitespace characters
                l.append( tr.replace(label, d) )
            trule[k] = ";".join(l)

def _replace_datparams_params(dat, trule, label):
    for k,tr in trule.items():
        if label in tr:
            trule[k] = tr.replace(label, dat)

# Transform the "input file" (report file)
def _transform_report_path(vals):
    l = []
    # for each input file
    for val in vals.split(','):
        # remove all the leading and trailing whitespace characters
        val = val.strip()
        # the relate table could be a full path or only a name of RT in the rels directory
        if val != 'nan' and val != '':
            if os.path.isfile(val):
                l.append(val)
            else:
                l.append( "{}/{}".format(__RSTDIR__, f"{val}.tsv") )
    if len(l) > 0:
        return ";".join(l)
    else:
        return ''

# return the list of relationship files separated by semicolon
def _transform_relationship_path(vals):
    l = []
    # for each input file
    for val in vals.split(','):
        # remove all the leading and trailing whitespace characters
        val = val.strip()
        # the relate table could be a full path or only a name of RT in the rels directory
        if val != 'nan' and val != '':
            if os.path.isfile(val):
                l.append(val)
            else:
                l.append( "{}/{}".format(__RELDIR__, f"{val}.tsv") )
    if len(l) > 0:
        return ";".join(l)
    else:
        return ''

def add_datparams(p, trule, val):
    # remove all the leading and trailing whitespace characters
    val = val.strip()
    
    # Replace the label for the value for each section: infiles, outfiles, and parameters
    if p == 'reported_vars':
        l = '__WF_'+p.upper()+'__'
        trule['parameters'] = replace_val_rec(trule['parameters'], {l: val})

    elif p == 'rep_file':
        l = '__WF_'+p.upper()+'__'
        # transform the input file
        v = _transform_report_path(val)
        _add_datparams_params(p, trule, v)

    elif p == 'rel_file':
        l = '__WF_'+p.upper()+'__'
        # transform the input file
        v = _transform_relationship_path(val)
        _add_datparams_params(p, trule, v)

    elif p == 'more_params':
        _add_datparams_moreparams(p, trule, val)
    
    # general case
    # p == 'experiment','input','output','level','norm','low_level', 'int_level','hig_level','lowhig_level','inthig_level','inf_infiles'
    else:
        l = '__WF_'+p.upper()+'__'
        # removes whitespaces before/after comma. removes end commas
        val = re.sub(r"\s*,\s*",",", val)
        val = re.sub(r",+$","", val)
        # replace the constant to the given value
        _replace_datparams(val, trule['infiles'],  l)
        _replace_datparams(val, trule['outfiles'], l)
        _add_datparams_params(p, trule, val)
        trule['parameters'] = replace_val_rec(trule['parameters'], {l: val})



def _add_rules(row, irules):
    '''
    add rules
    '''
    # deep copy the input cmd
    rules = copy.deepcopy(irules)

    # if 'output' folder does not exits, then we copy the value of 'input' folder
    if 'output' in row:
        if 'input' in row:
            row['output'] = row['output'] if row['output'] != 'nan' and row['output'] != '' else row['input']
    else:
        if 'input' in row:
            row['output'] = row['input']
            
    # Exception in SBT command!!
    # if "lowhig_level" and "inthig_level" don't exit, Then, we include the "low_level"ALL and "int_level"ALL, respectively.
    if not 'lowhig_level' in row and 'low_level' in row:
        row['lowhig_level'] = row['low_level']+'all'
    if not 'inthig_level' in row and 'int_level' in row:
        row['inthig_level'] = row['int_level']+'all'
    
    # Exception in SANSON command!!
    # if "low_norm" and "hig_norm" don't exit, Then, we include the "low_level"ALL and "hig_level"ALL, respectively.
    if not 'low_norm' in row and 'low_level' in row:
        row['low_norm'] = row['low_level']+'all'
    if not 'hig_norm' in row and 'hig_level' in row:
        row['hig_norm'] = row['hig_level']+'all'

    # extract the list of columns
    data_params = list(row.index.values)

    # go through the rules of cmd
    for i in range(len(rules)):
        trule = rules[i]
        # add data parameters in the inpfiles/outfiles
        # add data_parameters into the parameters section for each rule
        for p in data_params:
            add_datparams(p, trule, row.loc[p])
            
    return rules

def add_rules(row, cmd_rules):
    '''
    add rules
    '''
    # if theres is a list of inputs...
    if 'input' in row:
        # exlode the rows based the list of inputs
        row['input'] = re.split(r'\s*,\s*', row['input'])
        row_df = pd.DataFrame(row)
        row_df = row_df.transpose().explode('input').reset_index(drop=True).transpose()
        # create a list of rules for each input
        rules = []
        for row in row_df.to_dict(orient='series').values():
            rule = _add_rules(row, cmd_rules)
            rules.append(rule)
        rules = [i for sublist in rules for i in sublist]
    else:
        rules = _add_rules(row, cmd_rules)
    return rules


def add_cmd(row, icmd):
    '''
    Create rule list for each command
    '''
    # deep copy the input cmd
    cmd = copy.deepcopy(icmd)
    
    # Add the label of forced execution
    if 'force' in row:
        cmd['force'] = int(row['force'])

    # add rules
    cmd['rules'] = add_rules(row, cmd['rules'])
    
    return cmd

def add_unique_cmd_from_table(df, icmd):
    '''
    Create rule list for each command
    '''
    # deep copy the input cmd
    cmd = copy.deepcopy(icmd)
        
    # lookthrough all columns and add the parameters
    for col in df.columns:
        # join the unique values
        vals = ",".join(df[col].unique()).replace(" ", "")
        # go through the rules of cmd
        for i in range(len(cmd['rules'])):
            trule = cmd['rules'][i]
            # add only the given parameters for each rule
            add_datparams(col, trule, vals)

    # Add the label of forced execution
    if 'force' in df:
        cmd['force'] = int(df['force'].any(skipna=False))

    return [cmd]
    
def _param_str_to_dict(s):
    s = s.replace('=',' ')
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
        c = '{}="{}" '.format(k,str(v).replace('"','\\"')) if str(v) != '' else ''
    elif k == "DEL": # we provide only the value without parameter
        c = '"{}" '.format(str(v).replace('"','\\"')) if str(v) != '' else ''
    else:
        c = '{} "{}" '.format(k,str(v).replace('"','\\"')) if str(v) != '' else ''
    return c
    
def add_params_cline(cmds):
    '''
    Add the whole parametes (infiles, outfiles, params) to command line
    Add the command suffix and rule suffix
    Add the log file for each rule
    '''
    cmd_suffix = 1
    # work with the global suffix
    global RULE_SUFFIX
    # go through each cmd
    for cmd in cmds:
        # Add suffix in the name and increase the value
        cmd['name'] = f"{cmd['name']}_{cmd_suffix}"
        cmd_suffix += 1
        # For each rule...
        # create string for the command line with the infiles, outfiles and parameters
        for rule in cmd['rules']:
            cparams = ''
            # Add suffix in the name and increase the value
            rname = f"{rule['name']}_{RULE_SUFFIX}"
            lname = f"{cmd['name']}#rule{RULE_SUFFIX}#{rule['name']}"
            rule['name'] = rname
            RULE_SUFFIX += 1
            # Add the log file
            rule['logfile'] = "{}/{}/{}".format(__LOGDIR__, TPL_DATE, f"{lname}.log")
            # Create command line with the input, output files and the parameters
            for p in ['infiles','outfiles','parameters']:
                if rule[p] is not None:
                    for k,v in rule[p].items():
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
            if rule['more_params'] is not None and rule['more_params'] != '':
                v = str(rule['more_params'])
                ccprs = _param_str_to_dict(cparams) # get dict from old params
                ncprs = _param_str_to_dict(v) # get dict from new more_params
                for nk,cpr in ncprs.items():
                    ccprs[nk] = cpr
                # create again the cparams
                cparams = ''
                for kv,vv in ccprs.items():
                    cparams += '{} "{}" '.format(kv,str(vv)) if str(vv) != '' else '{} '.format(kv)
            # add the command line
            rule['cline'] += " "+cparams
        
# def _add_corrected_files(trule):
#     '''
#     add the correct files if '*' asterisk is in the path
#     '''
#     for k,files in trule.items():
#         if '*' in files:
#             l = []
#             for file in files.split(";"):
#                 l += [f for f in glob.glob(file, recursive=True)]
#             if len(l) > 0:
#                 trule[k] = ";".join(l)
#     return trule

def _get_unmatch_folder(file, outfiles):
    '''
    if the file matches, then get the folder that is not equal
    '''
    l = []
    sf = re.split(r'\*{1,}', file)
    if len(sf) > 1:
        b = sf[0] if sf[0] != '' else sf[1]
        e = sf[len(sf)-1]
        for outfile in outfiles:
            if outfile.startswith(b) and outfile.endswith(e):
                d = outfile.replace(b,'')
                d = d.replace(e,'')
                l += [d]
    return l

def _get_match_files(file, outfiles):
    '''
    get the matched files
    '''
    l = []
    sf = re.split(r'\*{1,}', file)
    if len(sf) > 1:
        b = sf[0] if sf[0] != '' else sf[1]
        e = sf[len(sf)-1]
        for outfile in outfiles:
            if b in outfile and outfile.endswith(e):
                l += [outfile]
    return l

def add_recursive_files(trule, outfiles):
    '''
    if '*' is in the path, add the correct files based on the outputs that are intrinsic of workflow.
    These files are added into the same command
    '''
    for k,files in trule.items():
        if '*' in files:
            l = []
            for file in files.split(";"):
                l += _get_match_files(file, outfiles)
            if len(l) > 0:
                trule[k] = ";".join(l)
    return trule

def add_recursive_cmds(cmd):
    '''
    if '*' is in the path, add multiple commands based on the outputs that are intrinsic of workflow.
    '''
    if 'rule_infiles' not in cmd:
        trules = cmd['rules']
        global OUTFILES
        # get the files with '*'
        files_ast = [file for trule in trules for file in trule['infiles'].values() if '/*/' in file]
        if len(files_ast) > 0:
            # for each file, if the file matches, then get the folder that is not equal
            folders_exp = []
            for file in files_ast:
                folders_exp += _get_unmatch_folder(file, OUTFILES)
            # for each unmatched folder, create a list of rules and replace the '*' to unmatched folder
            rules_new = []
            for folder_exp in np.unique(folders_exp):
                rules_new.append( replace_val_rec(trules, {'\*': folder_exp}) )
            # assign the new rules to the command
            # update the output files
            if len(rules_new) > 0:
                rules_new = [i for sublist in rules_new for i in sublist]
                of = np.array([ofile for rule_new in rules_new for ofile in rule_new['outfiles'].values()])
                OUTFILES = np.unique( np.concatenate((OUTFILES, of)) )
                cmd['rules'] = rules_new
    elif cmd['rule_infiles'] == 'multiple':
        # replace the input files that contains the "multiple infiles" (except its own outfiles)
        for k in range(len(cmd['rules'])):
            trule = cmd['rules'][k]
            ofiles =  [i for i in OUTFILES if i not in trule['outfiles'].values()]
            trule['infiles'] = add_recursive_files(trule['infiles'], ofiles)

    return cmd



#################
# Main function #
#################
def main(args):
    '''
    Main function
    '''

    # init the output file with the given attributes of workflow
    logging.info("init the output file with the attributes of given workflow")
    with open(args.attfile, 'r') as stream:
        try:
            tpl = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            sms = "ERROR!! Reading the attributes file of workflow: {}".format(exc)
            print(sms) # message to stdout with logging output
            sys.exit(sms)

    # assign the global variables
    global __EXPDIR__
    global __JOBDIR__
    global __RELDIR__
    global __RSTDIR__
    global __LOGDIR__
    global __STADIR__
    global __IDQFIL__
    global TPL_DATE
    __EXPDIR__ = tpl['prj_workspace']['expdir'].replace('\\','/')
    __JOBDIR__ = tpl['prj_workspace']['jobdir'].replace('\\','/')
    __RELDIR__ = tpl['prj_workspace']['reldir'].replace('\\','/')
    __RSTDIR__ = tpl['prj_workspace']['rstdir'].replace('\\','/')
    __LOGDIR__ = tpl['prj_workspace']['logdir'].replace('\\','/')
    __STADIR__ = tpl['prj_workspace']['stadir'].replace('\\','/')
    __IDQFIL__ = __EXPDIR__ + '/ID-q.tsv'
    TPL_DATE   = tpl['date']
    
    # extract the list of task-tables (ttablefiles)
    # split by command
    # create a list of tuples (command, dataframe with parameters)
    # dropping empty rows and empty columns
    # create a dictionary with the concatenation of dataframes for each command
    # {command} = concat.dataframes
    logging.info("read the multiple input files with the commands")
    indata = common.read_commands_from_tables(tpl['ttablefiles'])
    

    # check the tasktable parameters for each command:
    # return a variable with the outputs for each command    
    # 1. check whether there are duplicates in the output directories
    # 2. check whether the values of '* Var(x)' are False or a float (deprecated)??
    # 3. For Level_Creator: check if the column headers are in the input files and there are not repeated.
    # 4. For Rels_Creator: check if the column headers are in the input files and there are not repeated.
    # # -que ya existen las tablas de relaciones que necesitamos para todas las integraciones ???
# TODO!!!!! 3. Check the MAIN_INPUTS table is full. All the files have one experiment name
# TODO!!! 4. Check the columns: level, inf_level and sup_level are not empty    
    logging.info("check the tasktable parameters for each command")
    global OUTPUTS_FOR_CMD
    OUTPUTS_FOR_CMD = check_command_parameters(indata)
    
    
    # replace the constants for the config template and the command templates
    logging.info("replace the constants for the config template and the command templates")
    repl = {        
            '__ISANXOT_SRC_HOME__':     gvars.ISANXOT_SRC_HOME,
            '__ISANXOT_PYTHON_EXEC__':  gvars.ISANXOT_PYTHON_EXEC,
            '__ISANXOT_JAVA_EXEC__':    gvars.ISANXOT_JAVA_EXEC,
            '__ISANXOT_DOT_EXEC__':     gvars.ISANXOT_DOT_EXEC,
            '__NCPU__':                 str(tpl['ncpu']),
            '__WF_VERBOSE__':           str(tpl['verbose']),
            '__EXPDIR__':               __EXPDIR__,
            '__NAMDIR__':               __JOBDIR__,
            '__RELDIR__':               __RELDIR__,
            '__RSTDIR__':               __RSTDIR__,
            '__LOGDIR__':               __LOGDIR__,
            '__STADIR__':               __STADIR__,
            '__IDQFIL__':               __IDQFIL__,
            '__CATDB__':                '',
    }
    # add the replacements for the main_inputs
    for k_id in tpl['adaptor_inputs'].keys():
        repl[k_id] = tpl['adaptor_inputs'][k_id]
        
    # add the replacements for the data files of tasktable commands
    for datfile in tpl['ttablefiles']:
        if 'file' in datfile:
            l = "__TTABLEFILE_{}__".format(datfile['type'].upper())
            repl[l] = datfile['file']    
    tpl = replace_val_rec(tpl, repl)



    logging.info("create a command for each tasktable row")
    tpl['commands'] = []
    for cmd,indat in indata.items():
        # commands with ttable
        if 'table' in indat:
            uniq_exec = indat['unique_exec']
            df = indat['table']
            # read the templates of commands
            cmd_tpl = read_tpl_command(args.intpl, cmd)
            # replace constant within command tpls
            cmd_tpl = replace_val_rec(cmd_tpl, repl)
            if cmd_tpl:
                if uniq_exec:
                    # add the parameters into each rule
                    tpl['commands'].append(add_unique_cmd_from_table(df, cmd_tpl))
                    # # replace constants
                    # tpl['commands'] = replace_val_rec(tpl['commands'], repl)
                else: # the rest of commands
                    # create a command for each row
                    # add the parameters for each rule
                    tpl['commands'].append( list(df.apply( add_cmd, args=(cmd_tpl, ), axis=1)) )
                    # # replace constants
                    # tpl['commands'] = replace_val_rec(tpl['commands'], repl)
                # replace constants
                tpl['commands'] = replace_val_rec(tpl['commands'], repl)
        # commands without ttable
        else:
            # read the templates of commands
            cmd_tpl = read_tpl_command(args.intpl, cmd)
            # replace constant within command tpls
            cmd_tpl = replace_val_rec(cmd_tpl, repl)
            if cmd_tpl:
                tpl['commands'].append([cmd_tpl])




    logging.info("get the list of outfiles")
    global OUTFILES
    for i in range(len(tpl['commands'])):
        for j in range(len(tpl['commands'][i])):
            for k in range(len(tpl['commands'][i][j]['rules'])):
                trule = tpl['commands'][i][j]['rules'][k]
                OUTFILES += [ofile for ofile in trule['outfiles'].values() if '*' not in ofile]
    OUTFILES = np.array(OUTFILES)

    
    logging.info("add the commands based on the '*' input files")
    for i in range(len(tpl['commands'])):
        for j in range(len(tpl['commands'][i])):
            cmd = tpl['commands'][i][j]
            cmd = add_recursive_cmds(cmd) # and also update the OUTFILES



    # logging.info("fill the '**' input_group files for each command")
    # # replace the input files that contains the "recursive value" (**)
    # # except its own outfiles
    # for i in range(len(tpl['commands'])):
    #     for j in range(len(tpl['commands'][i])):
    #         for k in range(len(tpl['commands'][i][j]['rules'])):
    #             trule = tpl['commands'][i][j]['rules'][k]
    #             if 'type_infiles' in trule and trule['type_infiles'] == 'multiple':
    #                 ofiles =  [i for i in OUTFILES if i not in trule['outfiles'].values()]
    #                 trule['infiles'] = add_recursive_files(trule['infiles'], ofiles)

    

    logging.info("add command suffix and rule suffix")
    logging.info("fill the clines")
    # add the whole parametes (infiles, outfiles, params) to command line
    # add number suffix that increase with the rule
    # add the logfile
    global RULE_SUFFIX
    RULE_SUFFIX = 1
    for i in range(len(tpl['commands'])):
        add_params_cline( tpl['commands'][i] )


    
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