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


####################
# Global variables #
####################
import gvars

NCPUS = int(2/3* mp.cpu_count())

###################
# Local functions #
###################

# remove the output files of programs whose execution will be forced
def remove_outfiles(cfg):
    # go through each rule witin cmds
    for command in cfg['commands']:
        for cmd in command['cmds']:
            cmd_force = cmd['force']
            if ( cmd_force == 1 ):
                outfiles = [ o.split(';') for rule in cmd['rules'] for o in rule['outfiles'].values() ]
                # remove the output files from the list of list
                [ os.remove(o) for out in outfiles for o in out if os.path.isfile(o) ]

def _exec(cline, lfile, cmd_name, cmd_force, rule_name, cmd_pos, rule_pos):
    '''
    Execute command line
    '''
    start_time = time.asctime()
    state = '-'
    output = {
        'name': rule_name,
        'state': state,
        'start_time': start_time,
        'end_time': '-',
        'info': '-'
    }
    proc = 0
    try:
        print(f"MYSNAKE_LOG_START_RULE_EXEC\t{start_time}\t{cmd_name}\t{cmd_force}\t{rule_name}\t{cmd_pos}\t{rule_pos}\t{state}", flush=True)
        # logfile
        lf = open(lfile, "a+")
        # Run the command
        cargs = shlex.split(cline) # convert string into args            
        proc = subprocess.call(cargs, stdout=lf, stderr=subprocess.STDOUT)
        if proc != 0:
            raise Exception("error")
        state = 'successfully'
    except Exception:
        state = 'error'
    finally:
        # save status of execution
        end_time = time.asctime()
        output['state'] = state
        output['end_time'] = end_time
        print(f"MYSNAKE_LOG_END_RULE_EXEC\t{end_time}\t{cmd_name}\t{cmd_force}\t{rule_name}\t{cmd_pos}\t{rule_pos}\t{state}", flush=True)
    return proc

# execute the stats prograns
def exec_stats(cfg_date, cmd_name, cmd_force, cmd_logfile, n_cmd, n_total_cmds):
    '''
    Execute the statistical programs
    '''
    # collect the kalibrate values
    # command line
    cline = f'''"{gvars.ISANXOT_PYTHON_EXEC}" "{gvars.ISANXOT_SRC_HOME}/cmds/getKlibrateVals.py"
    --n_workers "{NCPUS}"
    --indir     "{args.directory}/jobs"
    --outfile   "{args.directory}/stats/klibration_vals.tsv"'''
    # get pos variables
    n_cmd += 1
    cmd_pos = f"{n_cmd}/{n_total_cmds}"
    rule_pos = "1/1"
    _exec(cline, cmd_logfile, cmd_name, cmd_force, 'getKlibrateVals', cmd_pos, rule_pos)
    
    # collect the integration values
    # command line
    cline = f'''"{gvars.ISANXOT_PYTHON_EXEC}" "{gvars.ISANXOT_SRC_HOME}/cmds/getIntegrationVals.py"
    --n_workers "{NCPUS}"
    --indir     "{args.directory}/jobs"
    --outfile   "{args.directory}/stats/integration_vals.tsv"'''
    # get pos variables
    n_cmd += 1
    cmd_pos = f"{n_cmd}/{n_total_cmds}"
    rule_pos = "1/1"
    _exec(cline, cmd_logfile, cmd_name, cmd_force, 'getIntegrationVals', cmd_pos, rule_pos)
    
    # getting the time values...
    # command line
    cline = f'''"{gvars.ISANXOT_PYTHON_EXEC}" "{gvars.ISANXOT_SRC_HOME}/cmds/getTimeVals.py"
    --n_workers "{NCPUS}"
    --indir     "{args.directory}/logs"
    --logid     "{cfg_date}"
    --outfile   "{args.directory}/stats/times_{cfg_date}.tsv"'''
    # get pos variables
    n_cmd += 1
    cmd_pos = f"{n_cmd}/{n_total_cmds}"
    rule_pos = "1/1"
    _exec(cline, cmd_logfile, cmd_name, cmd_force, 'getTimeVals', cmd_pos, rule_pos)


# define executor function
def executor(cmd, n_cmd, n_total_cmds):
    
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
    
    # get the command variables
    cmd_name = cmd['name']
    cmd_force = cmd['force']
    cmd_logfile = cmd['logfile']
    cmd_pos = f"{n_cmd}/{n_total_cmds}"
    state = '-'
    start_time = time.asctime()
    rule_name = '-'
    rule_pos = '-'
    output = {
        'name': cmd_name,
        'state': state,
        'start_time': start_time,
        'end_time': '-',
        'info': '-'
    }
    print(f"MYSNAKE_LOG_START_CMD_EXEC\t{start_time}\t{cmd_name}\t{cmd_force}\t{rule_name}\t{cmd_pos}\t{rule_pos}\t{state}", flush=True)
    
    try:
        # execute every rule
        for i in range(len(cmd['rules'])):
            # input parameter
            rule = cmd['rules'][i]
            rule_pos = f"{i+1}/{len(cmd['rules'])}"
        
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
            
            # Forcing the executing...
            if cmd_force == 1 and _all_ready(ifiles):
                proc = _exec(rule['cline'], cmd_logfile, cmd_name, cmd_force, rule['name'], cmd_pos, rule_pos)
                if proc != 0:
                    raise Exception("error")
                state = 'successfully'
            # Executing without force
            elif (cmd_force == 0 or cmd_force == '') and not _all_ready(ofiles):
                proc = _exec(rule['cline'], cmd_logfile, cmd_name, cmd_force, rule['name'], cmd_pos, rule_pos)
                if proc != 0:
                    raise Exception("error")
                state = 'successfully'
            elif (cmd_force == 0 or cmd_force == '') and _all_ready(ifiles) and _all_ready(ofiles):
                state = 'cached'
    except Exception as exc:
        state = 'error'
        output['log'] = exc
        raise Exception("ERROR!! Executing {} command: {}".format(cmd_name, exc))
    finally:
        end_time = time.asctime()
        rule_name = '-'
        rule_pos = '-'
        output['end_time'] = end_time
        print(f"MYSNAKE_LOG_END_CMD_EXEC\t{end_time}\t{cmd_name}\t{cmd_force}\t{rule_name}\t{cmd_pos}\t{rule_pos}\t{state}", flush=True)
        
    return output



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
        cfg_cmds = [ cmd for command in cfg['commands'] for cmd in command['cmds'] ]
        if not cfg_cmds:
            raise Exception('the rule list of confing is empty')
    except yaml.YAMLError as exc:
        sys.exit("ERROR!! Extracting the rules for each command: {}".format(exc))
    # get the total of cmds
    n_total_cmds = len(cfg_cmds)
    # include the stats commands
    n_total_cmds += 3


    
    # ------
    print(f"MYSNAKE_LOG_EXECUTING\t{time.asctime()}\t{n_total_cmds}", flush=True)
    
    logging.debug(f"start the execution of {n_total_cmds} commands using {NCPUS} processes in parallel")
    pool = mp.Pool(processes=NCPUS)
    results = []
    n_cmd = 0
    for i in range(len(cfg_cmds)):
        n_cmd = i+1
        results.append(pool.apply_async(executor,  args=(cfg_cmds[i], n_cmd, n_total_cmds)))
        # executor(cfg_cmds[i], n_cmd, n_total_cmds)    
    logging.debug("close the pool")
    pool.close()
    pool.join()
    
    
    
    
    # ------
    print(f"MYSNAKE_STATS_EXECUTING\t{time.asctime()}", flush=True)
    
    logging.debug("execute the statistic processes")
    cfg_date = cfg['date']
    cfg_logdir = cfg['prj_workspace']['logdir']
    cmd_logfile = f"{cfg_logdir}/{cfg_date}/GET_STATS.log"
    exec_stats(cfg['date'], 'GET_STATS', 1, cmd_logfile, n_cmd, n_total_cmds)


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