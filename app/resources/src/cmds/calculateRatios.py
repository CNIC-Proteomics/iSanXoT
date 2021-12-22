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
import concurrent.futures


####################
# Global variables #
####################
# col_names = ['idinf', "X'inf", "Vinf"]
col_names = ['idsup', "Xsup", "Vsup"]


###################
# Local functions #
###################
def read_infiles(file):
    indat = pd.read_csv(file, sep="\t", na_values=['NA'], low_memory=False)
    return indat
    
#################
# Main function #
#################
def main(args):
    '''
    Main function
    '''
    logging.info("read 'numaretor' files")
    # df_num = indat = pd.read_csv(args.numfiles, sep="\t", na_values=['NA'], low_memory=False)
    with concurrent.futures.ProcessPoolExecutor(max_workers=args.n_workers) as executor:            
        df_num = executor.map(read_infiles,args.numfiles.split(";"))
    df_num = pd.concat(df_num)
    
    
    logging.info("read 'denominator' files")
    # df_den = indat = pd.read_csv(args.denfiles, sep="\t", na_values=['NA'], low_memory=False)
    with concurrent.futures.ProcessPoolExecutor(max_workers=args.n_workers) as executor:            
        df_den = executor.map(read_infiles,args.denfiles.split(";"))
    df_den = pd.concat(df_den)
    
    
    # logging.info("group by the id and calculate the mean for all denominators") 
    # df_den = df_den.groupby('idsup').mean()
    
    
    # add suffix, except some columns
    keep_same = col_names[0]
    df_num.columns = ['{}{}'.format(c, '' if c in keep_same else "_1") for c in df_num.columns]
    df_den.columns = ['{}{}'.format(c, '' if c in keep_same else "_2") for c in df_den.columns]
    
    
    logging.info("merge the input files")
    df = pd.merge(df_num, df_den, on=keep_same)
    
    
    logging.info("drop the rows where at least one element is missing")
    df.dropna(inplace=True)
        
    
    logging.info("calculate the new Xq")
    # Xq = Xq1 - Xq2
    # df["X'inf"] = df["X'inf_1"] - df["X'inf_2"]
    df[f"{col_names[1]}"] = df[f"{col_names[1]}_1"] - df[f"{col_names[1]}_2"]


    logging.info(f"calculate the new Vq using {args.v_method} form")
    if args.v_method == 'max': # Vq = Max(V1,V2)
        df[f"{col_names[2]}"] = df[[f"{col_names[2]}_1", f"{col_names[2]}_2"]].max(axis=1)
        
    elif args.v_method == 'form': # Vq = 1/(1/V1+1/V2)
        df[f"{col_names[2]}"] = 1/ (1/df[f"{col_names[2]}_1"] + 1/df[f"{col_names[2]}_2"])

    elif args.v_method == 'avg': # Vq = Avg(V1,V2)
        df[f"{col_names[2]}"] = df[[f"{col_names[2]}_1", f"{col_names[2]}_2"]].mean(axis=1)


    logging.info("remove surplus columns")
    # df.drop(df.columns.difference(['idinf', "X'inf", "Vinf"]), 1, inplace=True)
    df.drop(df.columns.difference(col_names), 1, inplace=True)


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
    parser.add_argument('-w',  '--n_workers', type=int, default=2, help='Number of threads/n_workers (default: %(default)s)')
    parser.add_argument('-ii', '--numfiles',  required=True, help='Input files for the numerator ratio')
    parser.add_argument('-dd', '--denfiles',  required=True, help='Input files for the denominator ratio')
    parser.add_argument('-v',  '--v_method', required=True, choices=['form','max','avg'], default='max', help='Type of operation ["form" (Vq = 1/(1/V1+1/V2)), "max ("Vq = Max(V1,V2)), "avg" (Vq = Avg(V1,V2))] (default: %(default)s)')
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
