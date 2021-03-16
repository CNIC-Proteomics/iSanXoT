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
import glob
import argparse
import logging
import copy
import re
import json
import yaml
import shlex

####################
# Global variables #
####################
ISANXOT_LIB_HOME    = os.environ['ISANXOT_LIB_HOME']
ISANXOT_SRC_HOME    = f"{os.path.dirname(__file__)}/.."
ISANXOT_PYTHON_EXEC = sys.executable
ISANXOT_JAVA_EXEC   = f"{ISANXOT_LIB_HOME}/exec/java/bin/java.exe"
ISANXOT_DOT_EXEC    = f"{ISANXOT_LIB_HOME}/exec/graphviz/bin/dot.exe"


OUTPUTS_FOR_CMD     = None
TPL_DATE            = None
MAIN_INPUTS_JOBDIR  = None
MAIN_INPUTS_RELDIR  = None
MAIN_INPUTS_RSTDIR  = None
MAIN_INPUTS_LOGDIR  = None
RULE_SUFFIX         = None

#########################
# Import local packages #
#########################
sys.path.append(f"{ISANXOT_SRC_HOME}/src/preSanXoT/")
import createID


###################
# Local functions #
###################
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

    # create a list with all output directories for each command
    # create a dictionary with the output for each command
    outdirs = []
    outputs_cmd = {}
    # iterate over all commands
    for cmd,df in indata.items():
        # discard RATIOS_WSPP command because the tasktable is duplicated with WSPP_SBT
        if cmd != 'RATIOS_WSPP':
            outs = []
            if 'output' in df.columns and 'level' in df.columns:
                outs = list((df['output']+'/'+df['level']).values)
            if 'output' in df.columns and 'sup_level' in df.columns:
                outs = list((df['output']+'/'+df['sup_level']).values)
            if outs:
                outdirs.extend(outs)
                for o in outs:
                    outputs_cmd[o] = cmd

    # check if there are duplicates in the output directories
    if outdirs:
        if len(outdirs) != len(set(outdirs)):
            uniq_list, dup_list = get_set_unique_list(outdirs)
            sms = "ERROR!! There are dupplicated outdirs: {}".format(dup_list)
            print(sms) # message to stdout with logging output
            sys.exit(sms)
    
    # return the output for each command
    return outputs_cmd
    
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
                if dat and dat != 'nan':
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
def _transform_report_path(val):
    # the intermediate report file is with in Result WORKSPACE
    if val != 'nan' and val != '':
        # here it is important to use the "/" slash with format because if you use os.path.join snakemae does not recognize the path
        return "{}/{}".format(MAIN_INPUTS_RSTDIR, f"{val}.tsv")
    else:
        return ''

def add_datparams(p, trule, val):
    # remove all the leading and trailing whitespace characters
    val = val.strip()
    # Replace the label for the value for each section: infiles, outfiles, and parameters
    if p == 'ratio_numerator':
        l = '__WF_RATIO_NUM__'
        _replace_datparams(val, trule['infiles'],  l)
        # _replace_datparams(val, trule['outfiles'], l)
        if trule['parameters'] is not None and 'tags' in trule['parameters']:
            r = val.replace(" ", "").replace(",","-")
            _replace_datparams_params(r, trule['parameters']['tags'], '__WF_RATIO_NUM__')
            
    elif p == 'ratio_denominator':
        l = '__WF_RATIO_DEN__'
        _replace_datparams(val, trule['infiles'],  l)
        # _replace_datparams(val, trule['outfiles'], l)
        if trule['parameters'] is not None and 'tags' in trule['parameters']:
            r = val.replace(" ", "").replace(",","-")
            _replace_datparams_params(r, trule['parameters']['tags'], '__WF_RATIO_DEN__')

    elif p == 'reported_vars':
        l = '__WF_'+p.upper()+'__'
        trule['parameters'] = replace_val_rec(trule['parameters'], {l: val})

    elif p == 'rep_file':
        l = '__WF_'+p.upper()+'__'
        # transform the input file
        v = _transform_report_path(val)
        _add_datparams_params(p, trule, v)

    elif p == 'more_params':
        _add_datparams_moreparams(p, trule, val)
    
    # general case
    # p == 'experiment','input','output','level','norm','low_level', 'int_level','hig_level','lowhig_level','inthig_level','inf_infiles'
    else:
        l = '__WF_'+p.upper()+'__'
        _replace_datparams(val, trule['infiles'],  l)
        _replace_datparams(val, trule['outfiles'], l)
        _add_datparams_params(p, trule, val)
        trule['parameters'] = replace_val_rec(trule['parameters'], {l: val})

    # handle the parameters not required
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
                sf = re.split(r'\*+', file)
                if len(sf) > 1:
                    b = sf[0] if sf[0] != '' else sf[1]
                    e = sf[len(sf)-1]
                    for outfile in outfiles:
                        if b in outfile and outfile.endswith(e):
                            l += [outfile]
            if len(l) > 0:
                trule[k] = ";".join(l)
    return trule
    
def add_cmd(row, icmd):
    '''
    Create rule list for each command
    '''
    # deep copy the input cmd
    cmd = copy.deepcopy(icmd)
    
    # if 'output' folder does not exits, then we copy the value of 'input' folder
    if 'output' in row:
        if 'input' in row:
            row['output'] = row['output'] if row['output'] != 'nan' and row['output'] != '' else row['input']
    else:
        if 'input' in row:
            row['output'] = row['input']
    
    # Add the label of forced execution
    if 'force' in row:
        cmd['force'] = int(row['force'])
            
    # Exception in SBT command!!
    # if "lowhig_level" and "inthig_level" don't exit, Then, we include the "low_level"ALL and "int_level"ALL, respectivelly.
    if not 'lowhig_level' in row and 'low_level' in row:
        row['lowhig_level'] = row['low_level']+'all'
    if not 'inthig_level' in row and 'int_level' in row:
        row['inthig_level'] = row['int_level']+'all'

    # Exception in SANSON command!!
    # if "low_norm" and "hig_norm" don't exit, Then, we include the "low_level"ALL and "hig_level"ALL, respectivelly.
    if not 'low_norm' in row and 'low_level' in row:
        row['low_norm'] = row['low_level']+'all'
    if not 'hig_norm' in row and 'hig_level' in row:
        row['hig_norm'] = row['hig_level']+'all'

    # extract the list of columns
    data_params = list(row.index.values)
    # go through the rules of cmd
    for i in range(len(cmd['rules'])):
        trule = cmd['rules'][i]
        for p in data_params:
            # add data parameters in the infiles/outfiles
            # add data_parameters into the parameters section for each rule
            add_datparams(p, trule, row.loc[p])
        # add the correct files if '*' asterisk is in the path
        # at the moment, only for 'infiles'
        trule['infiles'] = _add_corrected_files(trule['infiles'])
    return cmd

def add_unique_cmd_from_table(df, icmd):
    '''
    Create rule list for each command
    '''
    # deep copy the input cmd
    cmd = copy.deepcopy(icmd)
    
    # get the list of unique experiments (in string)
    exps = ",".join(df['experiment'].unique()).replace(" ", "")
    if 'lab_decoy' in df.columns:
        ldecoy = df['lab_decoy'].values[0]
    else:
        ldecoy = ''
        
    # Add the label of forced execution
    if 'force' in df:
        cmd['force'] = int(df['force'].any(skipna=False))

    # go through the rules of cmd
    for i in range(len(cmd['rules'])):
        trule = cmd['rules'][i]
        # add only the given parameters for each rule
        add_datparams('experiment', trule, exps)
        add_datparams('lab_decoy', trule, ldecoy)
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
        c = '{}="{}" '.format(k,str(v)) if str(v) != '' else ''
    elif k == "DEL": # we provide only the value without parameter
        c = '"{}" '.format(str(v)) if str(v) != '' else ''
    else:
        c = '{} "{}" '.format(k,str(v)) if str(v) != '' else ''
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
            rule['name'] = rname
            RULE_SUFFIX += 1
            # Add the log file
            rule['logfile'] = "{}/{}/{}".format(MAIN_INPUTS_LOGDIR, TPL_DATE, f"{rname}.log")
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


    # extract the list of task-tables (datafiles)
    # split by command
    # create a list of tuples (command, dataframe with parameters)
    # dropping empty rows and empty columns
    # create a dictionary with the concatenation of dataframes for each command
    # {command} = concat.dataframes
    logging.info("read the multiple input files with the commands")
    infiles = ";".join([d['file'] for d in tpl['datfiles']])
    indata = createID.read_command_table(infiles)
    
    
    # check the tasktable parameters for each command:
    # 1. check whether there are duplicates in the output directories
    # 2. check whether the values of '* Var(x)' are False or a float

# TODO!!!!! 3. Check the MAIN_INPUTS table is full. All the files have one experiment name

# TODO!!! 4. Check the columns: level, inf_level and sup_level are not empty
    
    # return a variable with the outputs for each command    
    logging.info("check the tasktable parameters for each command")
    global OUTPUTS_FOR_CMD
    OUTPUTS_FOR_CMD = check_command_parameters(indata)
    
    

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
    dels = [i for i in tpl_cmds if not (i['name'] in cmds)]
    for c in dels:
        del tpl_cmds[ tpl_cmds.index(c) ]

    
    # if the cfg file of workflow has not 'database' information, we remove the indata of dataframes
    if not tpl['databases']:
        indata['RELS_TABLE_CATDB'].drop(indata['RELS_TABLE_CATDB'].index, inplace=True)
        indata['RELS_TABLE_CATFILE'].drop(indata['RELS_TABLE_CATFILE'].index, inplace=True)


    # assign the global variables
    global MAIN_INPUTS_EXPDIR
    global MAIN_INPUTS_JOBDIR
    global MAIN_INPUTS_RELDIR
    global MAIN_INPUTS_RSTDIR
    global MAIN_INPUTS_LOGDIR
    global TPL_DATE
    MAIN_INPUTS_EXPDIR = tpl['prj_workspace']['expdir']
    MAIN_INPUTS_JOBDIR = tpl['prj_workspace']['jobdir']
    MAIN_INPUTS_RELDIR = tpl['prj_workspace']['reldir']
    MAIN_INPUTS_RSTDIR = tpl['prj_workspace']['rstdir']
    MAIN_INPUTS_LOGDIR = tpl['prj_workspace']['logdir']
    TPL_DATE           = tpl['date']
    
    
    # replace the constants for the config template and the command templates
    logging.info("replace the constants for the config template and the command templates")
    repl = {        
            '__ISANXOT_SRC_HOME__':         ISANXOT_SRC_HOME,
            '__ISANXOT_PYTHON_EXEC__':      ISANXOT_PYTHON_EXEC,
            '__ISANXOT_JAVA_EXEC__':        ISANXOT_JAVA_EXEC,
            '__ISANXOT_DOT_EXEC__':         ISANXOT_DOT_EXEC,
            '__NCPU__':                     str(tpl['ncpu']),
            '__WF_VERBOSE__':               str(tpl['verbose']),
            '__MAIN_INPUTS_EXPDIR__':       MAIN_INPUTS_EXPDIR,
            '__MAIN_INPUTS_NAMDIR__':       MAIN_INPUTS_JOBDIR,
            '__MAIN_INPUTS_RELDIR__':       MAIN_INPUTS_RELDIR,
            '__MAIN_INPUTS_RSTDIR__':       MAIN_INPUTS_RSTDIR,
            '__MAIN_INPUTS_LOGDIR__':       MAIN_INPUTS_LOGDIR,
            '__MAIN_INPUTS_SEQFILE__':       '',
            '__MAIN_INPUTS_CATFILE__':      '',
            '__MAIN_INPUTS_CATDB__':        '',
    }
    # add the replacements for the databases
    for k_id in tpl['databases'].keys():
        repl[k_id] = tpl['databases'][k_id]
    # add the replacements for the main_inputs
    for k_id in tpl['main_inputs'].keys():
        repl[k_id] = tpl['main_inputs'][k_id]
    # add the replacements for the data files of tasktable commands
    for datfile in tpl['datfiles']:
        l = "__MAIN_INPUTS_DATFILE_{}__".format(datfile['type'].upper())
        repl[l] = datfile['file']    
    tpl = replace_val_rec(tpl, repl)
    tpl_cmds = replace_val_rec(tpl_cmds, repl)


    logging.info("create a command for each table row")
    tpl['commands'] = []
    for cmd,df in indata.items():
        if cmd == 'CREATE_ID' or cmd == 'RATIOS_WSPP' or cmd == 'MASTERQ' or cmd == 'JOINER':
            icmd = [i for i,c in enumerate(tpl_cmds) if c['name'] == cmd]
            if icmd and not df.empty:
                i = icmd[0]
                # add the parameters into each rule
                tpl['commands'].append(add_unique_cmd_from_table(df, tpl_cmds[i]))
                # replace constants
                tpl['commands'] = replace_val_rec(tpl['commands'], repl)
        else: # the rest of commands
            icmd = [i for i,c in enumerate(tpl_cmds) if c['name'] == cmd]
            if icmd and not df.empty:
                i = icmd[0]
                # create a command for each row
                # add the parameters for each rule
                tpl['commands'].append( list(df.apply( add_cmd, args=(tpl_cmds[i], ), axis=1)) )
                # replace constants
                tpl['commands'] = replace_val_rec(tpl['commands'], repl)

    
    logging.info("fill the parameters with intrinsic files in the commands")
    # get the list of output files
    outfiles = []
    for i in range(len(tpl['commands'])):
        for j in range(len(tpl['commands'][i])):
            for k in range(len(tpl['commands'][i][j]['rules'])):
                trule = tpl['commands'][i][j]['rules'][k]
                outfiles += trule['outfiles'].values()
    # replace the input files that contains the "recursive value" (**)
    # except its own outfiles
    for i in range(len(tpl['commands'])):
        for j in range(len(tpl['commands'][i])):
            for k in range(len(tpl['commands'][i][j]['rules'])):
                trule = tpl['commands'][i][j]['rules'][k]
                ofiles =  [i for i in outfiles if i not in trule['outfiles'].values()]
                trule['infiles'] = add_corrected_files_intrinsic(trule['infiles'], ofiles)

    

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
