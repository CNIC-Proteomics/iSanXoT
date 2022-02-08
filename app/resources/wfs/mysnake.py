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
import argparse
import logging
import multiprocessing as mp
import yaml
import subprocess
import time
import shlex
import re


####################
# Global variables #
####################
import gvars

NCPUS = int(2/3* mp.cpu_count())
COMMAND_ORDER = ['COPY_INPUTS','MAIN_INPUTS','CREATE_IDQUANT','FDR_Q','FDR','JOINER_FDR','JOINER_ID','JOINER_IDQ','MASTERQ',
                 'GET_IDSTATS',
                 'RELS_CREATOR',
                 'WSPP_SBT','WSPPG_SBT','WPP_SBT','WPPG_SBT',
                 'LEVEL_CREATOR','LEVEL_CALIBRATOR',
                 'INTEGRATE','NORCOMBINE','RATIOS_INT','SBT',
                 'SANSON','REPORT'
                 ]

###################
# Local functions #
###################

# remove the output files of programs whose execution will be forced
def remove_outfiles(cfg):
    # go through each rule witin cmds
    for cmds in cfg['commands']:
        for cmd in cmds:
            cmd_force = cmd['force']
            if ( cmd_force == 1 ):
                outfiles = [ o.split(';') for rule in cmd['rules'] for o in rule['outfiles'].values() ]
                # remove the output files from the list of list
                [ os.remove(o) for out in outfiles for o in out if os.path.isfile(o) ]

# define executor function
def executor(cmd):
    
    def _extract_files(files):
        out = []
        for f in list(files.values()):
            if f != '':
                out += f.split(';')
        return out
    
    def _is_locked(filepath):
        """Checks if a file is locked by opening it in append mode.
        If no exception thrown, then the file is not locked.
        """
        locked = None
        file_object = None
        if os.path.exists(filepath):
            try:
                buffer_size = 8
                # Opening file in append mode and read the first 8 characters.
                file_object = open(filepath, 'a', buffer_size)
                if file_object:
                    locked = False
            except IOError:
                locked = True
            finally:
                if file_object:
                    file_object.close()
        return locked
    
    def _file_ready(f):
        if os.path.exists(f):
            # path exists
            if os.path.isfile(f): # is it a file?
                # also works when file is a link and the target is writable
                if os.access(f, os.W_OK):
                    if _is_locked(f):
                        return False
                    else:
                        return True
                else:
                    return False
                return os.access(f, os.W_OK)
            elif os.path.dirname(f): # is it a dir?
                # target is creatable if parent dir is writable
                return os.access(f, os.W_OK)
            else:
                return False # otherwise, is not writable

    def _all_ready(files):
        return all([ _file_ready(f) for f in files ])

    def _exec(cline, lfile, cmd_name, cmd_force, rule_name, rule_pos):        
        # output
        start_time = time.asctime()
        output = {
            'name': rule_name,
            'state': 'executing',
            'start_time': start_time,
            'end_time': '-',
            'info': '-',
            'log_file': f'{lfile}'
        }
        try:
            # logfile
            lf = open(lfile, "a+")
            # Run the command
            cargs = shlex.split(cline) # convert string into args            
            print(f"MYSNAKE_LOG_START_RULE_EXEC\t{start_time}\t{cmd_name}\t{cmd_force}\t{rule['name']}\t{rule_pos}", flush=True)
            proc = subprocess.call(cargs, stdout=lf, stderr=subprocess.STDOUT)
            if proc != 0:
                raise Exception("error")
            state = 'finished'
        except Exception as exc:
            state = 'error'
            raise Exception("ERROR!! Executing {} the input file of workflow: {}".format(cline, exc))
        finally:
            # save status of execution
            end_time = time.asctime()
            output['state'] = state
            output['end_time'] = end_time
            # print the end execution of rule
            print(f"MYSNAKE_LOG_END_RULE_EXEC\t{end_time}\t{cmd_name}\t{cmd_force}\t{rule['name']}\t{rule_pos}\t{state}", flush=True)
            # check if it is the last executed rule of command
            # in that case, we print the end execution of a command
            if eval(rule_pos) == 1.0:
                print(f"MYSNAKE_LOG_END_CMD_EXEC\t{end_time}\t{cmd_name}\t{cmd_force}\t{rule['name']}\t{rule_pos}\t{state}", flush=True)
        return output
        
    # for each rule
    outputs = []
    for i in range(len(cmd['rules'])):
        # input parameter
        rule = cmd['rules'][i]
        cmd_name, cmd_force, rule_pos = cmd['name'],cmd['force'],f"{i+1}/{len(cmd['rules'])}"
    
        # declare output
        output = {
            'name': rule['name'],
            'state': 'waiting',
            'start_time': '-',
            'end_time': '-',
            'info': '-',
            'log_file': 'rule[logfile]' }
        # get the list of files: inputs, outputs and logs
        ifiles = _extract_files(rule['infiles'])
        ofiles = _extract_files(rule['outfiles'])
        # create directories recursevely
        [os.makedirs(os.path.dirname(f), exist_ok=True) for f in ifiles]
        [os.makedirs(os.path.dirname(f), exist_ok=True) for f in ofiles]
        
        # this processes would be able to execute
        # wait until the input files are ready to read/write
        while not _all_ready(ifiles):
            try:
                time.sleep(1)
            except:
                raise Exception("Caught KeyboardInterrupt, terminating workers")
        
        # It is the moment of the execution
        if cmd_force == 1 and _all_ready(ifiles):
            output = _exec(rule['cline'], rule['logfile'], cmd_name, cmd_force, rule['name'], rule_pos)
        elif (cmd_force == 0 or cmd_force == '') and not _all_ready(ofiles):
            output = _exec(rule['cline'], rule['logfile'], cmd_name, cmd_force, rule['name'], rule_pos)
        elif (cmd_force == 0 or cmd_force == '') and _all_ready(ifiles) and _all_ready(ofiles):
            state = 'cached'
            end_time = time.asctime()
            output['cmd_force'] = cmd_force
            output['end_time'] = end_time
            print(f"MYSNAKE_LOG_END_CMD_EXEC\t{end_time}\t{cmd_name}\t{cmd_force}\t{rule['name']}\t{rule_pos}\t{state}", flush=True)
        else:
            state = 'already_exec'
            end_time = time.asctime()
            output['cmd_force'] = cmd_force
            output['end_time'] = end_time
            print(f"MYSNAKE_LOG_END_CMD_EXEC\t{end_time}\t{cmd_name}\t{cmd_force}\t{rule['name']}\t{rule_pos}\t{state}", flush=True)
        outputs.append(output)
        
    return outputs



#################
# Main function #
#################
def main(args):
    '''
    Main function
    '''
    
    # ------
    print(f"MYSNAKE_LOG_STARTING\t{time.asctime()}", flush=True)
    
    logging.debug("check input parameters")
    if args.cores:
        global NCPUS
        NCPUS = int(args.cores)

    logging.debug("read config file")
    try:
        with open(args.configfile, 'r') as stream:
            cfg = yaml.safe_load(stream)
    except yaml.YAMLError as exc:
        sys.exit("ERROR!! Reading the config file: {}".format(exc))

    logging.debug("remove the output files of programs whose execution will be forced")
    try:
        remove_outfiles(cfg)
    except Exception as exc:
        sys.exit("ERROR!! Removing the output files of forced commands:\n{}".format(exc))


    # ------
    print(f"MYSNAKE_LOG_PREPARING\t{time.asctime()}", flush=True)
    
    logging.debug("extract the commands in order")
    try:
        cfg_rules = [ {
            'name': cmd['name'],
            'force': cmd['force'],
            'rules': cmd['rules']
        } for cmds in cfg['commands'] for cmd in cmds ]
        if not cfg_rules:
            raise Exception('the rule list of confing is empty')
    except yaml.YAMLError as exc:
        sys.exit("ERROR!! Extracting the rules for each command: {}".format(exc))
    # get the total of commands
    total_cmds = len(cfg_rules)
    # get dict with the commands_names and list of their own rules
    dict_1=dict()
    for c in cfg_rules:
        n = re.sub('\_\d*$','',c['name'])
        dict_1.setdefault(n, []).append(c)
    # extract the order of processes
    cfg_rules = [ dict_1[c] for c in COMMAND_ORDER if c in dict_1 ]
    cfg_rules = [i for s in cfg_rules for i in s]


    
    # ------
    print(f"MYSNAKE_LOG_EXECUTING\t{time.asctime()}\t{total_cmds}", flush=True)
    
    logging.debug(f"start the execution of {total_cmds} commands using {NCPUS} processes in parallel")
    pool = mp.Pool(processes=NCPUS)
    results = []
    for cmd in cfg_rules:
        results.append(pool.apply_async(executor, (cmd, )))
    
    logging.debug("close the pool")
    pool.close()
    pool.join()
    
    
    # ------
    print(f"MYSNAKE_STATS_EXECUTING\t{time.asctime()}", flush=True)
    
    logging.debug("execute the statistic processes")
    try:
        # command line
        cline = f'''"{gvars.ISANXOT_PYTHON_EXEC}" "{gvars.ISANXOT_SRC_HOME}/src/cmds/getVariances.py"
        --indir    "{args.directory}/jobs"
        --outfile  "{args.directory}/stats/variance_report.html"'''
        # Run the command
        cargs = shlex.split(cline) # convert string into args            
        proc = subprocess.call(cargs, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        if proc != 0:
            raise Exception("error")
    except Exception as exc:
        print("ERROR!! Getting the variance report:\n{}".format(exc), flush=True)

    # ------
    print(f"MYSNAKE_LOG_FINISHED\t{time.asctime()}", flush=True)

    


if __name__ == "__main__":
    # parse arguments
    parser = argparse.ArgumentParser(
        description='Mysnake is workflow management system.',
        epilog='''
        Example:
            python mysnake.py
        ''')        
    parser.add_argument('-c', '--configfile', required=True, help='Config file (YAML format)')
    parser.add_argument('-s', '--snakefile', required=True, help='Snake file')
    parser.add_argument('-j', '--cores',   help='Use at most N CPU cores/jobs in parallel. If N is omitted, the limit is set to 2/3 of the number of CPU cores.')
    parser.add_argument('-d', '--directory', required=True, help='Output directory')
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
    logging.debug('start script: '+"{0}".format(" ".join([x for x in sys.argv])))
    print('** start script: '+"{0}".format(" ".join([x for x in sys.argv])))
    main(args)
    logging.debug('end script')