# import global modules
import os
import re
import io
import pandas as pd
import numpy as np
import logging

#########################
# Import local packages #
#########################
import PD
import MSFragger
import Comet
import MaxQuant

####################
# Common functions #
####################

def get_path_file(i, indir):
    '''
    Get the full path
    '''
    if os.path.isfile(i):
        return i        
    elif os.path.isfile(f"{indir}/{i}"):
        return f"{indir}/{i}"
    else:
        return None

def select_search_engines(inpt):
    # if the input is file, read the first row
    # otherwise, we get dataframe
    if isinstance(inpt, str) and os.path.isfile(inpt):
        d = pd.read_csv(inpt, nrows=0, sep="\t", comment='#', index_col=False)
    else:
        d = inpt
    # determines which kind of searh engines we have.
    search_engines = ["PD","Comet","MSFragger","MaxQuant"]
    cond = (
        all(c in list(d.columns) for c in PD.COLS_NEEDED), # PD
        len(d.columns) == 4 or all(c in list(d.columns) for c in Comet.COLS_NEEDED), # Comet
        all(c in list(d.columns) for c in MSFragger.COLS_NEEDED), # MSFragger
        all(c in list(d.columns) for c in MaxQuant.COLS_NEEDED) # MaxQuant (from a list)
    )
    se = [i for (i, v) in zip(search_engines, cond) if v]
    se = se[0] if se else None
    return se

def select_search_engines_acid(inpt):
    '''
    Select the search engine After the CreateID
    '''
    # if the input is file, read the first row
    # otherwise, we get dataframe
    if isinstance(inpt, str) and os.path.isfile(inpt):
        d = pd.read_csv(inpt, nrows=0, sep="\t", comment='#', index_col=False)
    else:
        d = inpt
    # determines which kind of searh engines we have.
    search_engines = ["PD","Comet","MSFragger","MaxQuant"]
    cond = (
        all(c in list(d.columns) for c in PD.COLS_NEEDED_acid), # PD
        len(d.columns) == 4 or all(c in list(d.columns) for c in Comet.COLS_NEEDED_acid), # Comet
        all(c in list(d.columns) for c in MSFragger.COLS_NEEDED_acid), # MSFragger
        all(c in list(d.columns) for c in MaxQuant.COLS_NEEDED) # MaxQuant (from a list)
    )
    se = [i for (i, v) in zip(search_engines, cond) if v]
    se = se[0] if se else None
    return se

def read_command_table(ifiles):
    '''
    read the multiple input files to string and split by command
    create a list of tuples (command, dataframe with parameters)
    dropping empty rows and empty columns
    create a dictionary with the concatenation of dataframes for each command
    {command} = concat.dataframes
    '''
    indata = dict()
    idta = ''
    # read the multiple input files to string and split by command
    for f in ifiles.split(";"):
        with open(f, "r") as file:
            idta += file.read()
    # create a list of tuples (command, dataframe with parameters)
    match = re.findall(r'\s*#([^\s]*)\s*([^#]*)', idta, re.I | re.M)
    idta = [(c,pd.read_csv(io.StringIO(l), sep='\t', dtype=str, skip_blank_lines=True).dropna(how="all").dropna(how="all", axis=1).astype('str')) for c,l in match]
    # create a dictionary with the concatenation of dataframes for each command
    for c, d in idta:
        # discard the rows when the first empty columns
        if not d.empty:
            l = list(d[d.iloc[:,0] == 'nan'].index)
            d = d.drop(l)
            if c in indata:
                indata[c] = pd.concat( [indata[c], d], sort=False)
            else:
                for c2 in c.split('-'):
                    if c2 in indata:
                        indata[c2] = pd.concat( [indata[c2], d], sort=False)
                    else:
                        indata[c2] = d
    return indata


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
    # flag that controls whether the df was filtered or not.
    ok = False
    # check if the given filters is applied into given dataframe
    f_cols = re.findall(r'\[([^\]]*)\]',flt)
    intcols = np.intersect1d(df.columns,f_cols).tolist() if f_cols else []
    # the columns in the filters are within df
    if intcols:    
        # add the df variable
        flt = flt.replace("[","['").replace("]","']")
        flt = flt.replace('[','df[')
        flt = f"df[{flt}]"
        try:
            # evaluate condition
            idx = pd.eval(flt)
            # extract the dataframe from the index
            if not idx.empty:
                df_new = df.iloc[idx.index.to_list(),:]
                df_new = df_new.reset_index()
                ok = True
            else:
                # not filter
                logging.warning("The filter has not been applied")
                df_new = df
        except Exception as exc:
            # not filter
            logging.warning(f"The filter has not been applied. There was a problem evaluating the condition: {flt}\n{exc}")
            df_new = df
    else:
        df_new = df

    return ok,df_new


def filter_dataframe_multiindex(df, flt):
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
    # logicals = ['\|', '&', '~']
    logicals = ['&'] # for the moment only works with AND
    rc = r'|'.join(comparisons)
    rl = r'|'.join(logicals)
    # variable with index
    idx = pd.Series([])
    
    # go throught the comparisons
    comps = re.split(rl,flt)
    for cmp_str in comps:
        try:
            # trim whitespaces and parenthesis
            cmp_str = re.sub(r"^\s*\(\s*|\s*\)\s*$", '', cmp_str)
            # extract the variable/operator/values from the logical condition
            x = re.match(rf"^(.*)\s+({rc})\s+(.*)$", cmp_str)
            if x:
                var = x.group(1).strip()
                cmp = x.group(2).strip()
                val = x.group(3).strip()
                # use the multi-variables to filter the multiple columns
                if '@' in var:
                    v = var.split('@')
                    var0 = v[1]
                    vs = r'|'.join([rf"^\('{var0}',\s*'{v}'\)" for v in re.split(r'\s*,\s*', v[0])])
                else:
                    vs = rf"^\('{var}"
            # filter the column names
            # remember the columns are multiindex. For example, ('n_protein2category, '126_vs_Mean')
            # This is the reason we have included \(' in the regex
            d = df.filter(regex=f"{vs}", axis=1)
        except Exception as exc:
            # not filter
            logging.error(f"It is not filtered. There was a problem getting the columns: {cmp_str}\n{exc}")
            df_new = df
            break
        try:
            # evaluate condition
            ix = pd.eval(f"(d {cmp} {val})").any(axis=1)
            # comparison between two index Series
            # all -> &
            # any -> |
            if not idx.empty:
                if not ix.empty:
                    idx = pd.eval("(idx & ix)")
            else:
                idx = ix
        except Exception as exc:
            # not filter
            logging.error(f"It is not filtered. There was a problem evaluating the condition: {cmp_str}\n{exc}")
            df_new = df
            break

    # extract the dataframe from the index
    try:        
        if not idx.empty:
            df_new = df[idx]
    except Exception as exc:
        # not filter
        logging.error(f"It is not filtered. There was a problem extracting the datafram from the index rows: {exc}")
        df_new = df

    return df_new


def print_outfile(f):
    '''
    Rename the temporal files deleting the last suffix
    '''
    # get the output file deleting the last suffix
    ofile = os.path.splitext(f)[0]
    # remove obsolete output file
    if os.path.isfile(ofile):
        os.remove(ofile)
    # rename the temporal file
    os.rename(f, ofile)


# def all_files_ready(files):
#     def _is_locked(filepath):
#         """Checks if a file is locked by opening it in append mode.
#         If no exception thrown, then the file is not locked.
#         """
#         locked = None
#         file_object = None
#         if os.path.exists(filepath):
#             try:
#                 buffer_size = 8
#                 # Opening file in append mode and read the first 8 characters.
#                 file_object = open(filepath, 'a', buffer_size)
#                 if file_object:
#                     locked = False
#             except IOError:
#                 locked = True
#             finally:
#                 if file_object:
#                     file_object.close()
#         return locked
    
#     def _file_ready(f):
#         if os.path.exists(f):
#             # path exists
#             if os.path.isfile(f): # is it a file?
#                 # also works when file is a link and the target is writable
#                 if os.access(f, os.W_OK):
#                     if _is_locked(f):
#                         return False
#                     else:
#                         return True
#                 else:
#                     return False
#                 return os.access(f, os.W_OK)
#             elif os.path.dirname(f): # is it a dir?
#                 # target is creatable if parent dir is writable
#                 return os.access(f, os.W_OK)
#             else:
#                 return False # otherwise, is not writable

#     return all([ _file_ready(f) for f in files ])


if __name__ == "__main__":
	print("It is a library used by SanXoT and its adaptor modules")