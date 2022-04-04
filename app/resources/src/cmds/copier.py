#!/usr/bin/python

# import global modules
import os
import sys
import argparse
import logging
import shutil


# Module metadata variables
__author__ = "Jose Rodriguez"
__credits__ = ["Jose Rodriguez", "Jesus Vazquez"]
__license__ = "Creative Commons Attribution-NonCommercial-NoDerivs 4.0 Unported License https://creativecommons.org/licenses/by-nc-nd/4.0/"
__version__ = "1.0.1"
__maintainer__ = "Jose Rodriguez"
__email__ = "jmrodriguezc@cnic.es"
__status__ = "Development"


#########################
# Import local packages #
#########################
sys.path.append(f"{os.path.dirname(__file__)}/../libs")
import common

#################
# Main function #
#################
def main(args):
    '''
    Main function
    '''
    logging.info("copy the content of source to destination")
    try:
        # print to tmp file
        f = f"{args.outfile}.tmp"
        shutil.copyfile(args.infile, f)
        # rename tmp file deleting before the original file 
        common.rename_tmpfile(f)        
    except Exception as exc:
        sms = "ERROR!! Copying file: {}".format(exc)
        print(sms) # message to stdout with logging output
        sys.exit(sms)




if __name__ == "__main__":
    # parse arguments
    parser = argparse.ArgumentParser(
        description='Program that join multiple files in one',
        epilog='''Examples:
        python  src/SanXoT/joiner.py
          -ii TMT1/ID-q.tsv;TMT2/ID-q.tsv
          -o ID-q.tsv
        ''',
        formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('-i',  '--infile',  required=True, help='Input file')
    parser.add_argument('-o',  '--outfile', required=True, help='Output file')
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
