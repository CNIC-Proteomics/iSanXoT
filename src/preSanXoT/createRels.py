#!/usr/bin/python

# import global modules
import os
import sys
import argparse
import logging
import re
import pandas as pd
import numpy as np


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

def get_cols_from_inheaders(df_cols, headers):
    out = []
    if df_cols and headers:
        if isinstance(headers, str): headers = re.split(r'\s*:\s*', headers)
        for c in headers:
            if c in df_cols:
                out.append(c)
            elif '*' in c:
                c = c.replace('*','\w+')
                for s in df_cols:
                    if re.match(c, s):
                        out = out + [ m for m in re.findall(c, s)]
            elif '[' in c and ']' in c:
                out.append(c)
            elif '{' in c and '}' in c:
                out.append(c)
    return out


def filter_rows(idf, filters):
    
    # filter values
    def _filter_tuple(tup, filt, tup_avail):
        # filter olny in the selected columns
        out = [ re.findall(rf"{filt}", str(t)) if i in tup_avail else t for i,t in enumerate(tup) ]
        # the list of tuples coming from the "findall" is joined with ';'
        out = [ ';'.join([str(x) for t in l for x in t if x != '']) if isinstance(l,list) else l for l in out]

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
                # r"IDA:\[([^\]]+)\]|ISS:\[([^\]]+)\]|HDA:\[([^\]]+)\]"
                p = ":\[([^\]]+)\]|".join( re.split(r'\s*,\s*',f) )
                p = rf"{p}:\[([^\]]+)\]"
                # create list of tuples
                # apply pattern for the list of tuples                    
                df_tuples = [tuple(x) for x in idf.to_numpy()]
                df_filt = [_filter_tuple(tup,p, tup_avail) for tup in df_tuples]
                idf = pd.DataFrame(df_filt, columns=idf.columns.tolist())
    
    # Important! for the reduction of memory
    # remove duplicates
    idf.drop_duplicates(inplace=True)

    return idf


def extract_and_join_columns(idf, header_inf, header_sup, header_thr, cols_inf, cols_sup, cols_thr):
    # extract the columns. If there are multiple columns, join in one
    def _extract_and_join_columns(idf, cols, header):
        out = []
        if len(cols) > 1:
            if ':' in header:
                out = [":".join([str(j) for j in s if not pd.isnull(j) and j != '']) for s in idf[cols].to_numpy()]
            else:
                out = [";".join([str(j) for j in s if not pd.isnull(j) and j != '']) for s in idf[cols].to_numpy()]
        elif len(cols) == 1:
            # get the column
            col = cols[0]
            # check if the col is a constant value: [X]
            # check if the col is a the order of column: {1}
            # otherwise, the col is the list of column names
            if col and '[' in col and ']' in col:
                c = re.findall(r'\[([^\]]*)\]', col)[0]
                # create a column with the given constant
                # extract the column with the constant
                idf[col] = c
                # idf = idf.reset_index()
                out = idf[col]
            elif col and '{' in col and '}' in col:
                c = int(re.findall(r'\{([^\}]*)\}', col)[0])
                # extract the column by position
                out = idf[idf.columns[c]]
            elif col:
                # extract the column
                out = idf[col]
        return out

    # create a list of tuple with the (input columns and the output heaers)
    colheaders = [(cols_inf,header_inf)]
    if header_sup and cols_sup: colheaders.append((cols_sup,header_sup))
    if header_thr and cols_thr: colheaders.append((cols_thr,header_thr))
    
    # init output dataframe
    odf = pd.DataFrame(columns=[h[1] for h in colheaders])
    
    # get the columns with its -header
    for col,header in colheaders:
        odf[header] = _extract_and_join_columns(idf, col, header)

    # remove duplicates to reduce the use of memory
    odf.drop_duplicates(inplace=True)
    # remove row with any empty columns
    odf.replace('', np.nan, inplace=True)
    odf.dropna(inplace=True)
    
    return odf


def exploding_columns(idf):
    def _exploding_columns(idf, x, y):
        # replace np.nan to ''
        idf.replace(np.nan, '', inplace=True)
        # Exploding into multiple cells
        # We start with creating a new dataframe from the series with  as the index
        df = pd.DataFrame(idf[x].str.split(';').tolist(), index=idf[y]).stack().rename(x)
        df = df.reset_index()
        # convert the index, which is a list of tuple, into columns
        a = df.iloc[:,0].tolist()
        df[y] = pd.DataFrame(a, columns=y)
        # remove columns based on the old index (2 columns)
        df.drop( df.columns[0:2], axis=1, inplace=True)
        # reorder columns from the given df
        cols = idf.columns.tolist()
        df = df[cols]
        return df
        
    cols = idf.columns.tolist()
    df = idf
    for x in cols:
        y = [i for i in cols if i != x]
        # check if ';' exits in column
        if any(df[x].str.contains(';')): df = _exploding_columns(df, x, y)
    return df


def replace_by_xrefprotein(intcols, iscols, df_inf, cols_datsup):
    '''
    WARNING!!! THIS METHOD IS HARD-CORE!! But it was the only way I thought to do it
    First, check if intersection columns is "Protein".
    Second, check if the columns of sup df contains the xref proteins.
    Third, extract the first value (not NaN) of 'Protein', and check if the value keeps the regex of one xref id.
    Fourth, replace the 'Protein' by the new xref column name.
    '''
    # check if intersection columns is "Protein"
    if 'Protein' in intcols:
        # check if the columns of sup df contains the xref proteins
        xrefs = {'xref_Ensembl_protId':   r'^ENS(\w{3})?P\d+',
                 'xref_Ensembl_transcId': r'^ENS(\w{3})?T\d+',
                 'xref_Ensembl_GeneId':   r'^ENS(\w{3})?G\d+',
                 'xref_RefSeq_protId':    r'^[N|X|Y]P_\d+',
                 'xref_RefSeq_transcId':  r'^[N|X][M|C]_\d+',
        }
        intxrefs = np.intersect1d(list(xrefs.keys()),cols_datsup).tolist() if cols_datsup else []
        # extract the first value (not NaN) of 'Protein'
        x = df_inf['Protein'].tolist()[0]
        # check if the value keeps the regex of one xref id
        m = [ i for i,r in xrefs.items() if re.match(r,x) ]
        if m:
            intcols = [ m[0] if i == 'Protein' else i for i in intcols ]
            iscols  = [ m[0] if i == 'Protein' else i for i in iscols ]
      
    return intcols,iscols

def merge_unknown_columns(df_inf, df_sup):
    # extract interseted column
    ic = df_inf.columns
    sc = df_sup.columns
    k = list(set(ic) & set(sc))
    if k and len(k) >= 1:
        df = pd.merge(df_inf, df_sup, on=k)
    else:
        df = None

    return df



#################
# Main function #
#################
def main(args):
    '''
    Main function
    '''
    # get input variables
    header_inf = args.inf_header
    header_sup = args.sup_header
    header_thr = args.thr_header
    
    # HARD-CODE: Filter the GO terms based on the evidence codes:
    # http://geneontology.org/docs/guide-go-evidence-codes/
    # IMPORTANT NOTE!! This filter is important because otherwise the memory exploits
    filters = "cat_GO_*:EXP,IDA,IPI,IMP,IGI,IEP,HTP,HDA,HMP,HGI,HEP,IBA,IBD,IKR,IRD"
    # filters = None
    
    logging.info("read input files of inferior header")
    l = []
    for f in args.inf_infiles.split(";"):
        d = pd.read_csv(f, sep="\t", dtype=str, na_values=['NA'], low_memory=False)
        l.append(d)
    datinf = pd.concat(l)

    datsup = None
    if args.sup_infiles:
        logging.info("read input file of superior header")
        l = []
        for f in args.sup_infiles.split(";"):
            d = pd.read_csv(f, sep="\t", dtype=str, na_values=['NA'], low_memory=False)
            l.append(d)
        datsup = pd.concat(l)

    datthr = None
    if args.thr_infiles:
        logging.info("read input file of third header")
        l = []
        for f in args.thr_infiles.split(";"):
            d = pd.read_csv(f, sep="\t", dtype=str, na_values=['NA'], low_memory=False)
            l.append(d)
        datthr = pd.concat(l)
    
    
    
    logging.info("get the columns from the given headers")
    # get the columns of all tables
    cols_datinf = datinf.columns.to_list()
    cols_datsup = datsup.columns.to_list() if (datsup is not None and not datsup.empty) else []
    cols_datthr = datthr.columns.to_list() if (datthr is not None and not datthr.empty) else []
    # get the inf/sup/thr columns based on all tables
    all_cols = cols_datinf + cols_datsup + cols_datthr
    cols_inf = get_cols_from_inheaders(all_cols, header_inf)
    cols_sup = get_cols_from_inheaders(all_cols, header_sup)
    cols_thr = get_cols_from_inheaders(all_cols, header_thr)
    
    
    
    
    logging.info("get the intersected columns")
    # get the intersected columns
    iheader = cols_inf + cols_sup + cols_thr
    iicols = get_cols_from_inheaders(cols_datinf, iheader)
    iscols = get_cols_from_inheaders(cols_datsup, iheader) if (datsup is not None and not datsup.empty) else []
    itcols = get_cols_from_inheaders(cols_datthr, iheader) if (datthr is not None and not datthr.empty) else []
    # remove the column values with [x] and {x}
    iicols = [ c for c in iicols if not ('[' in c and ']' in c) and not ('{' in c and '}' in c) ]
    iscols = [ c for c in iscols if not ('[' in c and ']' in c) and not ('{' in c and '}' in c) ]
    itcols = [ c for c in itcols if not ('[' in c and ']' in c) and not ('{' in c and '}' in c) ]
    
    
    
    # EXTRACT AND MERGE SECTION ---
    
    # first files - second files
    outdat = datinf
    if (datsup is not None and not datsup.empty):
        # chech if there are intersected columns
        intcols = np.intersect1d(iicols,iscols).tolist() if iscols else iicols
        if intcols:
            logging.info("merge the first file and the second file based on the intersected columns")

            # Check the Protein column:
            # check if the intersection column is from a xref-protein column, by default is the protein column
            intcols2,iscols = replace_by_xrefprotein(intcols, iscols, outdat, cols_datsup)
            
            # extract the inf columns
            outdat = outdat[iicols]            
            # extract the sup columns
            datsup = datsup[iscols]
            
            # merge the inf - sup df's
            outdat = outdat.merge(datsup, left_on=intcols, right_on=intcols2, how='left', suffixes=('', '_old'))
        else:
            logging.info("make cross-reference with the first and second file before merge")
            outdat = merge_unknown_columns(outdat, datsup)
    
    # second files - third files
    if (datthr is not None and not datthr.empty):
        intcols = np.intersect1d(iscols,itcols).tolist() if itcols else intcols
        if intcols:
            logging.info("merge with the third based on the intersected columns")
            
            # Check the Protein column:
            # check if the intersection column is from a xref-protein column, by default is the protein column
            intcols2,itcols = replace_by_xrefprotein(intcols, itcols, outdat, cols_datthr)
            
            # extract the thr columns
            datthr = datthr[itcols]
            
            # merge withe thr df
            outdat = outdat.merge(datthr, left_on=intcols, right_on=intcols2, how='left', suffixes=('', '_old'))
            
        else:
            logging.info("make cross-reference with the third file before merge")
            outdat = merge_unknown_columns(outdat, datthr)

    
    # FILTER SECTION ---
    if filters:
        logging.info("filter the rows")
        outdat = filter_rows(outdat, filters)
        

    # EXTRACT BASED ON HEADER NAME AND JOIN MULTIPLE COLUMNS IN ONE ---
    logging.info("join the columns and add 1's")
    outdat = extract_and_join_columns(outdat, header_inf, header_sup, header_thr, cols_inf, cols_sup, cols_thr)
    
    
    logging.info("change the order of columns")
    cols = outdat.columns.to_list()
    cols = [cols[i] for i in [1,0,2] if (i < len(cols))]
    outdat = outdat[cols]


    logging.info("exploding the columns into multiple rows")
    outdat = exploding_columns(outdat)


    logging.info("remove duplicates and remove row with any empty column")
    # remove duplicates
    outdat.drop_duplicates(inplace=True)
    # remove row with any empty columns
    outdat.replace('', np.nan, inplace=True)
    outdat.dropna(inplace=True)


    logging.info('print output')
    outdat.to_csv(args.outfile, sep="\t", index=False)



if __name__ == "__main__":
    
    # parse arguments
    parser = argparse.ArgumentParser(
        description='Create the relationship tables from several files',
        epilog='''Examples:
        python  src/preSanXoT/createRelsAlt.py
          -ii TMT1/ID-q.tsv;TMT2/ID-q.tsv
          -o rels_table.tsv
        ''',
        formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('-i',  '--inf_header',  required=True, help='Column(s) for the inferior level')
    parser.add_argument('-j',  '--sup_header',  help='Column(s) for the superior level')
    parser.add_argument('-k',  '--thr_header',  help='Column(s) for the third level')
    parser.add_argument('-ii', '--inf_infiles',  required=True, help='Input file for the inferior header')
    parser.add_argument('-ji', '--sup_infiles',  help='Input file for the superior header')
    parser.add_argument('-ki', '--thr_infiles',  help='Input file for the third header')
    parser.add_argument('-o',  '--outfile', required=True, help='Output file with the relationship table')
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
