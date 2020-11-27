#!/usr/bin/python

# import global modules
import os
import sys
import argparse
import logging
import pandas as pd
import re
# import concurrent.futures


# Module metadata variables
__author__ = "Jose Rodriguez"
__credits__ = ["Jose Rodriguez", "Jesus Vazquez"]
__license__ = "Creative Commons Attribution-NonCommercial-NoDerivs 4.0 Unported License https://creativecommons.org/licenses/by-nc-nd/4.0/"
__version__ = "1.0.1"
__maintainer__ = "Jose Rodriguez"
__email__ = "jmrodriguezc@cnic.es"
__status__ = "Development"

###################
# Local functions #
###################
def read_infiles(file):
    indat = pd.read_csv(file, sep="\t", na_values=['NA'], low_memory=False)
    return indat

def filter_dataframe(df, flt):
    '''
    Filter the dataframe

    Parameters
    ----------
    df : pandas dataframe
        Report.
        
    flt : str
        Boolean expression.

    Returns
    -------
    Filtered dataframe.

    '''
    # variable with the boolean operators
    comparisons = ['>=', '<=', '!=', '<>', '==', '>', '<']
    logicals = ['\|', '&', '~']
    rc = r'|'.join(comparisons)
    rl = r'|'.join(logicals)
    
    # create the new flt replacing variables
    # split the string flt by all logical operators
    # go throught the comparisons
    # extract the variable and value
    # replace the variable by the df comparison
    # replace the value with commas
    comps = re.split(rl,flt)
    for cmp_str in comps:
        cmp_str = cmp_str.strip().replace('(','').replace(')','')
        cmp = re.split(rc,cmp_str)
        var = cmp[0].strip()
        val = cmp[1].strip().replace('"','').replace("'",'')
        var_new = "df['{}']".format(var)
        try:
            val_new = "{}".format(float(val))
        except ValueError:
            val_new = "'{}'".format(val)        
        # the order of replacements is important!
        cmp_str_new = cmp_str
        cmp_str_new = re.sub(rf'{val}\b',val_new,cmp_str_new) # replace exact match
        cmp_str_new = re.sub(rf'{var}\b',var_new,cmp_str_new) # replace exact match
        flt = flt.replace(cmp_str,cmp_str_new)

    # evaluate flt
    # examples        
    # flt = df[df['FDR'] < 0.05 ]
    try:
        flt = "df[{}]".format(flt)
        df_new = pd.eval(flt, engine='python')
    except:
        # not filter
        df_new = df
    
    return df_new


#################
# Main function #
#################
# BEGIN: OLD DESCRIPTION --
# Workflow stops here for the preparation of the file C2A_outStats_clean.tsv following these steps:
# i  ) Duplicate the C2A_outStats.tsv file;
# ii ) Rename the duplicate file to C2A_outStats_clean.tsv;
# iii) Remove the unnecessary categories; bear in mind that when a comma is present in a category name.
#         VLOOKUP will produce a "Not found" result.
#         So any commas must be removed from the category names in all these files:
#           C2A_outStats.tsv, Q2C_noOuts_outStats.tsv and Q2COuts_tagged.tsv
# iv ) Remove all the information (including all the headings) except for the
#         names of the relevant categories.
# END: OLD DESCRIPTION --
def main(args):
    '''
    Main function
    '''    
    logging.info("read stats files")
    # with concurrent.futures.ProcessPoolExecutor(max_workers=args.n_workers) as executor:            
    #     indat = executor.map(read_infiles,args.infiles.split(";"))
    # indat = pd.concat(indat)
    indat = pd.read_csv(args.infiles, sep="\t", na_values=['NA'], low_memory=False)

    logging.info("read relationship files")
    # with concurrent.futures.ProcessPoolExecutor(max_workers=args.n_workers) as executor:            
    #     indat = executor.map(read_infiles,args.refiles.split(";"))
    # indat = pd.concat(indat)
    redat = pd.read_csv(args.refiles, sep="\t", dtype=str, na_values=['NA'], low_memory=False)
    
    # rename columns of relation file because we are going to use the 'idsup' as 'idinf'
    logging.info("rename columns of relationship files")
    redat.rename(columns={'idinf':'idinf_rel', 'idsup':'idinf', 'tags': 'tags_rel'}, inplace=True)

    # merge df's based on 'idinf' column
    logging.info("merge df's based on 'idinf' column")
    indat = pd.merge(indat,redat, on='idinf')

    # discards the tags
    logging.info("discard the given tags")
    for t in re.split(r'\s*&\s*', args.tags.strip()):
        if t.startswith('!'):
            t = t.replace('!','')
            indat = indat[indat['tags_rel'] != t ]
    
    # add the number of proteins (idinf_rel) per category (idinf): nq
    df = indat.groupby('idinf').agg({
        'idinf_rel': 'count'
    })
    df.rename(columns={'idinf_rel': 'nq'}, inplace=True)
    df.reset_index(inplace=True)
    indat = pd.merge(indat, df, on='idinf')
    
    # apply given filter. By default: (FDR < 0.05) & (nq > 10) & (nq < 100)
    indat = filter_dataframe(indat, args.filters)
    
    # - Remove all the information (including all the headings) except for the names of the relevant categories.
    # - Remove duplicates
    indat = indat['idinf']
    indat.drop_duplicates(inplace=True)

    logging.info("print output file without header")
    indat.to_csv(args.outfile, sep="\t", index=False, header=False)



if __name__ == "__main__":
    # parse arguments
    parser = argparse.ArgumentParser(
        description='Create a file with the list of files by experiment',
        epilog='''Examples:
        python  src/SanXoT/createSansonHighLevel.py
          -ii w1/c2a_outStats.tsv;wt2/c2a_outStats.tsv
          -o c2a_levels.tsv
        ''',
        formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('-ii',  '--infiles',  required=True, help='Multiple outStats files separated by comma')
    parser.add_argument('-rr',  '--refiles',  required=True, help='Multiple Relationship file separated by comma')
    parser.add_argument('-o',   '--outfile',  required=True, help='Output file with the relationship table')
    parser.add_argument('-t',   '--tags',     default='!out', help='Multiple Relationship file separated by comma')
    parser.add_argument('-f',   '--filters',  default='(FDR < 0.05) & (nq > 10) & (nq < 100)', help='Boolean expression for the filtering of report')
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
