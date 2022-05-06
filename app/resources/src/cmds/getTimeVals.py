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
import glob
import re
import pandas as pd
from subprocess import Popen, PIPE
from datetime import datetime
import concurrent.futures
from itertools import repeat


#########################
# Import local packages #
#########################
sys.path.append(f"{os.path.dirname(__file__)}/../libs")
import common

###################
# Local functions #
###################
def get_time(infile, cols):
    # init output
    df = pd.DataFrame(columns=cols)
    try:
        # get file name
        fname = os.path.basename(infile)
        # get process name
        ps = re.findall("([^#]+)#([^#]+)#([^\.]+)\.log", fname)
        if ps:
            ps = ps[0]
            cmd = ps[0]
            irule = ps[1]
            rule = ps[2]
            # get process time (end time - start time)
            # extract the start time and end time
            fh = open(infile, "r").readlines()
            sc = fh[0]  if len(fh) > 0 and "- start script" in fh[0] else None
            ec = fh[-1] if len(fh) > 0 and "- end script"   in fh[-1] else None
            # get time only if both times exist
            if sc and ec:
                # # get the command line
                # c = re.split('start script\s*:\s*',sc)
                # cline = c[1] if len(c) >= 2 else sc
                # get the sample name
                sname = common.get_job_name(sc)
                # get the time
                sc = re.split(r'\s*-\s*', sc)
                ec = re.split(r'\s*-\s*', ec)
                if len(sc) >= 3 and len(ec) >= 3:
                    # crete the object
                    so = datetime.strptime(sc[2], '%m/%d/%Y %H:%M:%S %p')
                    eo = datetime.strptime(ec[2], '%m/%d/%Y %H:%M:%S %p')
                    # calculate the difference
                    diff = int((eo - so).total_seconds())
                    # return data
                    df = pd.DataFrame([(cmd,irule,rule,sname,diff)], columns=cols)
    except Exception as exc:
        print("ERROR!! Getting the time values:\n{}".format(exc), flush=True)
    return df



def main(args):
    '''
    Main function
    '''
    logging.info("getting the list of log files...")
    infiles = glob.glob(os.path.join(args.indir,args.logid,'*.log'), recursive = True)
    if not infiles:
        sys.exit("ERROR!! There are not input files")
    # discard isanxot log
    infiles = [ i for i in infiles if os.path.basename(i) != 'isanxot.log']

    logging.info(f"getting time for every file in parallel ({args.n_workers})...")
    cols = ['command','index','process','sample','time (sec)']
    with concurrent.futures.ProcessPoolExecutor(max_workers=args.n_workers) as executor:            
        ddf = executor.map( get_time, infiles, repeat(cols) )
    ddf = pd.concat(ddf)
    # begin: for debugging in Spyder
    # ddf = get_time( infiles[2], cols)
    # end: for debugging in Spyder
        
    logging.info("sorting by...")
    ddf.sort_values(['command','index'], ascending=True, inplace=True)
    
    logging.info("adding the time sum by command...")
    df = ddf.groupby('command')['time (sec)'].sum().reset_index()
    df['command'] = df['command']+'_Total'
    ddf = pd.concat([df,ddf], ignore_index=True)

    logging.info('printing tsv output...')
    ddf.to_csv(args.outfile, index=False, sep="\t", line_terminator='\n', columns=[c for c in cols if c != 'index'])


    
    

if __name__ == '__main__':
    # parse arguments
    parser = argparse.ArgumentParser(
        description='Extract the times from log folder and log id',
        epilog='''
        Example:
            python getTimeVals.py -i logs/ -d 20220504000636 -o stats/times.tsv

        ''')
    parser.add_argument('-w',   '--n_workers', type=int, default=2, help='Number of threads/n_workers (default: %(default)s)')
    parser.add_argument('-i',  '--indir', required=True, help='Input log Directory')
    parser.add_argument('-l',  '--logid', required=True, help='Input log identifier')
    parser.add_argument('-o',  '--outfile',   required=True, help='Output file')
    parser.add_argument('-x',  '--phantom_files',  help='Phantom output files needed for the handle of iSanXoT workflow (snakemake)')
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