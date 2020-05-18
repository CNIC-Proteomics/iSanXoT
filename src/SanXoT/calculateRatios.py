# -*- coding: utf-8 -*-
#!/usr/bin/python

# Module metadata variables
__author__ = ["Jose Rodriguez"]
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
import pandas as pd
import re



####################
# Global variables #
####################


###################
# Local functions #
###################
    
#################
# Main function #
#################
def main(args):
    '''
    Main function
    '''
    
    logging.info("read input files")
    df1 = pd.read_csv(args.numfile, sep="\t", na_values=['NA'], low_memory=False)
    df2 = pd.read_csv(args.denfile, sep="\t", na_values=['NA'], low_memory=False)
    
    
    # add suffix, except some columns
    keep_same = ['idinf']
    df1.columns = ['{}{}'.format(c, '' if c in keep_same else f"_1") for c in df1.columns]
    df2.columns = ['{}{}'.format(c, '' if c in keep_same else f"_2") for c in df2.columns]
    
    
    logging.info("merge the input files")
    df = pd.merge(df1, df2, on=keep_same)
    
    
    logging.info("drop the rows where at least one element is missing")
    df.dropna(inplace=True)
        
    
    logging.info("calculate the new Xq")
    # Xq = Xq1 - Xq2
    df["X'inf"] = df["X'inf_1"] - df["X'inf_2"]


    logging.info(f"calculate the new Vq using {args.v_method} form")
    if args.v_method == 'max': # Vq = Max(V1,V2)
        df["Vinf"] = df[["Vinf_1", "Vinf_2"]].max(axis=1)
        
    elif args.v_method == 'form': # Vq = 1/(1/V1+1/V2)
        df["Vinf"] = 1/ (1/df["Vinf_1"] + 1/df["Vinf_2"])

    elif args.v_method == 'avg': # Vq = Avg(V1,V2)
        df["Vinf"] = df[["Vinf_1", "Vinf_2"]].mean(axis=1)


    logging.info("remove surplus columns")
    df.drop(df.columns.difference(['idinf', "X'inf", "Vinf"]), 1, inplace=True)


    logging.info(f"print output file")
    df.to_csv(args.outfile, sep="\t", index=False)





if __name__ == "__main__":
    # parse arguments
    parser = argparse.ArgumentParser(
        description='Calculate the ratios',
        epilog='''
        Example:
            python calculateRatios.py
        ''')
    parser.add_argument('-i',  '--numfile',  required=True, help='Input file for the numerator ratio')
    parser.add_argument('-s',  '--denfile',  required=True, help='Input file for the denominator ratio')
    parser.add_argument('-m',  '--v_method', required=True, choices=['form','max','avg'], default='max', help='Type of operation ["form" (Vq = 1/(1/V1+1/V2)), "max ("Vq = Max(V1,V2)), "avg" (Vq = Avg(V1,V2))] (default: %(default)s)')
    parser.add_argument('-o',  '--outfile',  required=True, help='Output file with the reports')
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
