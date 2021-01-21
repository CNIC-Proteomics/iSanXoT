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
import multiprocessing as mp
import signal
import yaml
import subprocess
import shutil
import re
import time
import shlex



####################
# Global variables #
####################
NCPUS            = int(2/3* mp.cpu_count())
ISANXOT_LIB_HOME = os.environ['ISANXOT_LIB_HOME']
ISANXOT_SRC_HOME = f"{os.path.dirname(__file__)}/.."


###################
# Local functions #
###################

# define executor function
def executor(proc):
    
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

    def _exec(rname, cline, lfile, cmd_name, pos_rule):
        # output
        start_time = time.asctime()
        output = {
            'name': rname,
            'state': 'executing',
            'start_time': start_time,
            'end_time': '-',
            'info': '-',
            'log_file': f'{lfile}' }
        try:
            # logfile
            lf = open(lfile, "a+")
            # Run the command
            cargs = shlex.split(cline) # convert string into args            
            print(f"START_EXEC\t{cmd_name}\t{rule['name']}\t{pos_rule}\t{start_time}", flush=True)
            state = 'finished'
            proc = subprocess.call(cargs, stdout=lf, stderr=subprocess.STDOUT)
            if proc != 0:
                raise Exception("error")
            print(f"OUT_EXEC\t{cmd_name}\t{rule['name']}\t{pos_rule}\t{state}", flush=True)
            output['state'] = state
        except Exception as exc:
            state = 'error'
            print(f"OUT_EXEC\t{cmd_name}\t{rule['name']}\t{pos_rule}\t{state}", flush=True)
            output['state'] = state
            raise Exception("ERROR!! Executing {} the input file of workflow: {}".format(cline, exc))
        finally:
            end_time = time.asctime()
            print(f"END_EXEC\t{cmd_name}\t{rule['name']}\t{pos_rule}\t{end_time}", flush=True)
            output['end_time'] = end_time
        return output
    
    # input parameter
    cmd,pos,rule = proc
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
    # get the attribute of execution
    exec_attr = 'exec'
    if exec_attr == 'not' and not _all_ready(ofiles):
        raise Exception(f"ERROR!! The user decided not exectute the {rule['name']} rule but the outputs of the process do not exit")
    elif exec_attr == 'not':
        output['state'] = 'finished'
        output['end_time'] = time.asctime()
    else:
        # wait until the input files are ready to read/write
        while not _all_ready(ifiles):
            try:
                time.sleep(1)
            except:
                raise Exception("Caught KeyboardInterrupt, terminating workers")
        
        # It is the moment of the execution
        if exec_attr == 'force' and _all_ready(ifiles):
            output = _exec(rule['name'], rule['cline'], rule['logfile'], cmd, pos)
        elif exec_attr == 'exec' and not _all_ready(ofiles):
            output = _exec(rule['name'], rule['cline'], rule['logfile'], cmd, pos)

    return output



#################
# Main function #
#################
def main(args):
    '''
    Main function
    '''
    
    logging.info("check input parameters")
    if args.cores:
        global NCPUS
        NCPUS = int(args.cores)


    logging.info("validate the input files of workflow")
    try:
        # Run the command
        proc = subprocess.run([f"{ISANXOT_LIB_HOME}/python/tools/Scripts/snakemake.exe",
                                  '--configfile', f"{args.configfile}",
                                  '--snakefile',  f"{args.snakefile}",
                                  '--directory',  f"{args.directory}",
                                  '-n','-r'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        if proc.returncode != 0:
            raise Exception(f"{proc.stdout.decode('utf-8')}")
        # remove tmp folder of snakemake
        shutil.rmtree(f"{args.directory}/.snakemake")
    except Exception as exc:
        sys.exit("ERROR!! Validating the input file of workflow:\n{}".format(exc))



    logging.info("extract the order of processes")
    try:
        proc_ord = re.findall(r'Job\s*\d+:\s*([^\:]*)',str(proc.stdout))
        if not proc_ord:
            raise Exception('the ordered list of processes is empty')
        logging.debug(f"{proc_ord}")
    except Exception as exc:
        sys.exit("ERROR!! Extracting the order of processes: {}".format(exc))



    logging.info("read config file and reorder rules")
    with open(args.configfile, 'r') as stream:
        try:
            cfg = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            sys.exit("ERROR!! Reading the config file: {}".format(exc))



    logging.info("reorder the rules")
    with open(args.configfile, 'r') as stream:
        try:
            rul = [ (cmd['name'], f"{i+1}/{len(cmd['rules'])}", cmd['rules'][i]) for cmds in cfg['commands'] for cmd in cmds for i in range(len(cmd['rules'])) ]
            rules = {}
            for c,n,r in rul: 
                k = r['name']
                rules[k] = (c,n,r)
            rules_ord = [ rules[o] for o in proc_ord ]
            if not rules_ord:
                raise Exception('the ordered list of rules is empty')
        except yaml.YAMLError as exc:
            sys.exit("ERROR!! Reordering the rules: {}".format(exc))
    
    


    logging.info(f"execute the processes: {NCPUS} processes in parallel")
    pool = mp.Pool(processes=NCPUS)
    results = []
    for rule in rules_ord:
        results.append(pool.apply_async(executor, (rule,)))
    
    logging.info("close the pool")
    pool.close()
    pool.join()
    
    logging.info("wait for each running task to complete")
    for result in results:
        out, err = result.get()
        print("out: {} err: {}".format(out, err), flush=True)

    


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
    logging.info('start script: '+"{0}".format(" ".join([x for x in sys.argv])))
    main(args)
    logging.info('end script')