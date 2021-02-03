#!/usr/bin/python

# import global modules
import os
import sys
import argparse
import logging
import re
import pandas as pd
import numpy as np
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
    indat = pd.read_csv(file, sep="\t", dtype=str, na_values=['NA'], low_memory=False)
    return indat

def get_cols_from_inheaders(df, headers):
    if not df.empty:
        cols = df.columns
        cols = re.split(r'\s*&\s*', headers) if headers else []
        for c in cols:
            if not( '*' in c or '!' in c or ('[' in c and ']' in c) or ('{' in c and '}' in c) ) and not( c in cols ):
                logging.error(f"The column name {c} does not exit in the given files")
                sys.exit(1)
    return cols

def exploding_columns(idf):
    def _exploding_columns(idf, x, y):
        # Exploding into multiple cells
        # We start with creating a new dataframe from the series with  as the index
        df = pd.DataFrame(idf[x].str.split(';').tolist(), index=idf[y]).stack()
        # We now want to get rid of the secondary index
        # To do this, we will make  as a column (it can't be an index since the values will be duplicate)
        df = df.reset_index([0,y])
        # rename colum
        df.rename(columns={0:x}, inplace=True)
        # reorder columns from the given df
        cols = idf.columns.tolist()
        df = df[cols]
        return df
        
    cols = idf.columns.tolist()
    it = iter(cols)
    for x in it:
        y = next(it)
        # check if ';' exits in column
        df = _exploding_columns(idf, x, y) if any(idf[x].str.contains(';')) else idf
        df = _exploding_columns(df, y, x) if any(idf[y].str.contains(';')) else df
    return df
    
def create_crossref_dataframe(inf_df, sup_df):
    # if given output dataframe is not empty and has only one column, then 
    # make the cross-reference between the given output df and the calculated df
    df = pd.DataFrame()
    if not inf_df.empty:
        inf_cols = inf_df.columns.to_list()
        sup_cols = []
        for ic in inf_cols:
            sup_cols += [ c for c in sup_df.columns if sup_df[c].isin(inf_df[ic]).any() ]
        # if we have xref columns, then we merge both dataframes
        if sup_cols and len(inf_cols) == len(sup_cols):
            df = pd.merge(sup_df, inf_df, left_on=sup_cols, right_on=inf_cols)
        else:
            df = sup_df
    else:
        df = sup_df

    return df

def _extract_columns(idf, cols):
    df = pd.DataFrame()
    for col in cols:
        # check if the col is a constant value: [1]
        # check if the col is a the order of column: {1}
        # otherwise, the col is the list of column names
        if '[' in col and ']' in col:
            c = re.findall(r'\[([^\]]*)\]', col)[0]
            # create a column with the given constant
            # extract the column with the constant
            idf[col] = c
            idf = idf.reset_index()
            df[col] = idf[col]
        elif '{' in col and '}' in col:
            c = int(re.findall(r'\{([^\}]*)\}', col)[0])
            # rename the output header
            df.rename(columns={col: idf.columns[c]}, inplace=True)
            # extract the column by position
            df[idf.columns[c]] = idf[idf.columns[c]]
        elif '*' in col:
            # convert to regex replacing '*' to '\w+'
            col = col.replace('*','\w+')
            col = rf"({col})"
            # get the columns that match with the given col name (regex)
            ms = []
            for s in idf.columns:
                if re.match(col, s):
                    ms = ms + [ m for m in re.findall(col, s)]
            df[ms] = idf[ms]
        elif '!' in col:
            # delete ! char
            col = col.replace('!','')
            # remove column
            df.drop(col, axis=1, inplace=True, errors='ignore')
        else:
            # # extract the list of columns by name
            # if col in idf.columns:
            #     df[col] = idf[col]
            # extract the list of columns by name separated by the delimeter '-'
            for s in col.split("-"):
                if s in idf.columns:
                    if df.empty:
                        df[col] = idf[s]
                    else:
                        df[col] = df[col] + "-" + idf[s]
    
    return df

def _filter_columns(idf, filters):
    
    # filter values
    def _filter_tuple(tup, filt, tup_avail):
        out = []
        for i,t in enumerate(tup):
            if i in tup_avail: # filter olny in the columns available
                s = ";".join(re.findall(rf"{filt}", t)) if not pd.isnull(t) else np.nan
                s = np.nan if s == '' else s
            else:
                s = t
            out.append(s)
        return tuple(out)
    
    # get columns
    cols = idf.columns.tolist()
    # get list of filters
    flts = re.split(r'\s*&\s*', filters) if filters else []
    for flt in flts:
        fc = re.split(r'\s*:\s*', flt)
        if fc and len(fc) == 2:
            col = fc[0]
            f = fc[1]            
            # get the columns that match with the given col name (regex)
            tup_avail = []
            col = col.replace('*','\w+')# convert to regex replacing '*' to '\w+'
            col = rf"({col})"
            for i,c in enumerate(cols):
                if re.match(col, c):
                    tup_avail = tup_avail + [ i for m in re.findall(col, c)]

            # if we find matched columns we apply the filters
            if tup_avail:
                # create pattern with the string separated by comma
                # eg.
                # f = IDA,ISS,HDA
                # p = ([^\;]*\|IDA:[^\;]*|[^\;]*\|ISS:[^\;]*|[^\;]*\|HDA:[^\;]*)
                p = ":[^\;]*|[^\;]*\|".join( re.split(r'\s*,\s*',f) )
                p = rf"([^\;]*\|{p}:[^\;]*)"
                # create list of tuples
                # apply pattern for the list of tuples                    
                idf_tuples = [tuple(x) for x in idf.to_numpy()]
                idf_filt = [_filter_tuple(tup,p, tup_avail) for tup in idf_tuples]
                idf = pd.DataFrame(idf_filt, columns=idf.columns.tolist())
    
    return idf

def extract_columns(idf, list_cols, list_names, filters=None):
    # init output dataframe
    odf = pd.DataFrame(columns=list_names)
    # the number of columns and names has to be te same
    if len(list_cols) == len(list_names):
        # look through the list of columns and names
        for i,cols in enumerate(list_cols):
            # get the name of colums
            name = list_names[i]

            # extract columns
            df = _extract_columns(idf, cols)
                    
            # Check if we get something
            if df.empty:
                logging.error(f"We can not extract data from the {name} column")
                sys.exit(1)
            else:
                # filter columns
                if filters:
                    df = _filter_columns(df, filters)
                
                # If there are multiple columns, we concatenate in one
                c = df.columns.tolist()
                if len(c) > 1:
                    #WARNING!!!!!
                    odf[name] = [";".join([str(j) for j in s if not pd.isnull(j)]) for s in df.to_numpy()]
                else:
                    c = "".join(c)
                    odf[name] = df[c]
                
        # remove duplicates
        odf.drop_duplicates(inplace=True)

        # remove row with any empty columns
        odf.replace('', np.nan, inplace=True)
        odf.dropna(inplace=True)

    return odf

def extract_xref_columns(inf_df, sup_df, inf_cols, sup_cols, inf_name, sup_name, filters=None):
    # extract only inferior column
    inf_out = extract_columns(inf_df, [inf_cols], [inf_name], filters)
    
    # if apply we create the dataframe with the cross-reference columns based on the given df's
    xref_df = create_crossref_dataframe(inf_out, sup_df)

    # extract inferior and superior columns
    sup_out = extract_columns(xref_df, [inf_cols,sup_cols], [inf_name,sup_name], filters)
        
    return sup_out

def extract_xref_columns_before_merge(inf_df, sup_df, inf_cols, sup_cols, inf_name, sup_name, filters=None):
    # extract interseted column
    ic = inf_df.columns
    sc = sup_df.columns
    k = list(set(ic) & set(sc))
    if k and len(k) >= 1:
        xref_df = pd.merge(inf_df, sup_df, on=k)

    # extract inferior and superior columns
    sup_out = extract_columns(xref_df, [inf_cols,sup_cols], [inf_name,sup_name], filters)
        
    return sup_out

    
#################
# Main function #
#################
def main(args):
    '''
    Main function
    '''
    logging.info("read input files of inferior header")
    # with concurrent.futures.ProcessPoolExecutor(max_workers=args.n_workers) as executor:            
    #     infdat = executor.map(read_infiles,args.inf_infiles.split(";"))
    # infdat = pd.concat(infdat)
    l = []
    for f in args.inf_infiles.split(";"):
        d = pd.read_csv(f, sep="\t", dtype=str, na_values=['NA'], low_memory=False)
        l.append(d)
    infdat = pd.concat(l)

    logging.info("read input file of superior header")
    # with concurrent.futures.ProcessPoolExecutor(max_workers=args.n_workers) as executor:            
    #     supdat = executor.map(read_infiles,args.sup_infiles.split(";"))
    # supdat = pd.concat(supdat)
    l = []
    for f in args.sup_infiles.split(";"):
        d = pd.read_csv(f, sep="\t", dtype=str, na_values=['NA'], low_memory=False)
        l.append(d)
    supdat = pd.concat(l)

    if args.thr_header:
        logging.info("read input file of third header")
        # with concurrent.futures.ProcessPoolExecutor(max_workers=args.n_workers) as executor:            
        #     thrdat = executor.map(read_infiles,args.thr_infiles.split(";"))
        # thrdat = pd.concat(thrdat)
        l = []
        for f in args.thr_infiles.split(";"):
            d = pd.read_csv(f, sep="\t", dtype=str, na_values=['NA'], low_memory=False)
            l.append(d)
        thrdat = pd.concat(l)
    
    
    logging.info("check if input headers are within dataframes")
    inf_cols = get_cols_from_inheaders(infdat, args.inf_header)
    sup_cols = get_cols_from_inheaders(supdat, args.sup_header)
    if args.thr_header:
        thr_cols = get_cols_from_inheaders(thrdat, args.thr_header) 
    
    
    logging.info("init output dataframe")
    inf_name = re.sub(r"\s+",'-', args.inf_header)
    sup_name = re.sub(r"\s+",'-', args.sup_header)
    if args.thr_header:
        thr_name = re.sub(r"\s+",'-', args.thr_header)
        
    
    if args.xref_before:
        logging.info("make cross-reference before extract the inferior-superior level")        
        outdat = extract_xref_columns_before_merge(infdat, supdat, inf_cols, sup_cols, inf_name, sup_name, args.filters)        
        
    else:    
        logging.info("extract the inferior-superior level")
        outdat = extract_xref_columns(infdat, supdat, inf_cols, sup_cols, inf_name, sup_name, args.filters)
        
            
    logging.info("change the order of columns")
    cols = outdat.columns.to_list()
    cols = [cols[i] for i in [1,0]]
    outdat = outdat[cols]


    logging.info("exploding the columns into multiple rows")
    outdat = exploding_columns(outdat)
    

    if args.thr_header:
        logging.info("extract the superior-third level")
        outdat = extract_xref_columns(outdat, thrdat, sup_cols, thr_cols, sup_name, thr_name, args.filters)

    
    logging.info("remove duplicates and remove row with any empty column")
    # remove duplicates
    outdat.drop_duplicates(inplace=True)
    # remove row with any empty columns
    outdat.replace('', np.nan, inplace=True)
    outdat.dropna(inplace=True)


    logging.info('print output')
    outdat.to_csv(args.outfile, sep="\t", index=False)






if __name__ == "__main__":
    
    class addDefaultToOtherParams(argparse.Action):
        # adapted from documentation
        def __call__(self, parser, namespace, values, option_string=None):
            setattr(namespace, self.dest, values)
            setattr(namespace, 'sup_infiles', values)
            setattr(namespace, 'thr_infiles', values)
        
    # parse arguments
    parser = argparse.ArgumentParser(
        description='Create the relationship tables from several files',
        epilog='''Examples:
        python  src/preSanXoT/createRelsAlt.py
          -ii TMT1/ID-q.tsv;TMT2/ID-q.tsv
          -o rels_table.tsv
        ''',
        formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('-w',  '--n_workers', type=int, default=2, help='Number of threads/n_workers (default: %(default)s)')
    parser.add_argument('-i',  '--inf_header',  required=True, help='Column(s) for the inferior level')
    parser.add_argument('-ii', '--inf_infiles',  required=True, action=addDefaultToOtherParams, help='Input file for the inferior header')
    parser.add_argument('-j',  '--sup_header',  required=True, help='Column(s) for the superior level')
    parser.add_argument('-ji', '--sup_infiles',  help='Input file for the superior header')
    parser.add_argument('-k',  '--thr_header',  help='Column(s) for the third level')    
    parser.add_argument('-ki', '--thr_infiles',  help='Input file for the third header')   
    parser.add_argument('-o',  '--outfile', required=True, help='Output file with the relationship table')
    parser.add_argument('-f',  '--filters',   help='Boolean expression for the filtering of report')
    parser.add_argument('-b',  '--xref_before', action='store_true', help='Make a cross-reference with the input files before everything')
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
