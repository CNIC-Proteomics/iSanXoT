#!/usr/bin/python

# Module metadata variables
__author__ = "Jose Rodriguez"
__credits__ = ["Jose Rodriguez", "Jesus Vazquez"]
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


#########################
# Import local packages #
#########################
sys.path.append(f"{os.path.dirname(__file__)}/../libs")
import common


###################
# Local functions #
###################
def parse_arguments(argv):
    # parse arguments
    parser = argparse.ArgumentParser(
        description='Create a file with the list of files by experiment',
        epilog='''Examples:
        python  src/SanXoT/createCardenioTags.py
          -ii w1/p2q_lowerNormV.tsv;wt2/p2q_lowerNormV.tsv
          -o exps_lowerNormV.tsv
        ''',
        formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('-ii',  '--infiles',  required=True, help='Multiple input files separated by comma')
    parser.add_argument('-o',   '--outfile', required=True, help='Output file with the relationship table')
    parser.add_argument('-vv', dest='verbose', action='store_true', help="Increase output verbosity")
    args = parser.parse_args(argv)
    
    # get the name of script
    script_name = os.path.splitext( os.path.basename(__file__) )[0].upper()

    # logging debug level. By default, info level
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG,
                            format=script_name+' - '+str(os.getpid())+' - %(asctime)s - %(levelname)s - %(message)s',
                            datefmt='%m/%d/%Y %I:%M:%S %p',
                            force=True)
    else:
        logging.basicConfig(level=logging.INFO,
                            format=script_name+' - '+str(os.getpid())+' - %(asctime)s - %(levelname)s - %(message)s',
                            datefmt='%m/%d/%Y %I:%M:%S %p',
                            force=True)
    return args


def main(argv):
    '''
    Main function
    '''
    # PARSE ARGUMENTS ---
    args = parse_arguments(argv)

    logging.info("create tag file with the list of experiments")
    infiles = args.infiles.split(";")
    if infiles:
        # create workspace
        common.create_workspace_from_file(args.outfile)
        with open(args.outfile, 'w') as outfile:
            outfile.write( "{}\t{}\n".format("Tag","File path") )            	
            for i,infile in enumerate(infiles):
                # get the name of 'job' until the root folder
                exp_name = common.get_job_name(infile)
                # write file for cardenio
                outfile.write( "{}\t{}\n".format(exp_name,infile) )






if __name__ == "__main__":
    # start main function
    logging.info('start script: '+"{0}".format(" ".join([x for x in sys.argv])))
    main(sys.argv[1:])
    logging.info('end script')
