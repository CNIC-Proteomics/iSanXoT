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

####################
# Global variables #
####################
ROOT_FOLDER = r'[\/|\\]jobs[\/|\\]'

####################
# Common functions #
####################

def get_job_name(file):
    # get the job name from file or from string (command line)
    if os.path.isfile(file):
        # get the name of 'experiment' until the root folder
        # By default, we get the last folder name of path
        fpath = os.path.dirname(file)
        name = os.path.basename(fpath)
    # the input is string (not empty)
    elif file != '':
        fpath = file
        name = file
    else:
        fpath = None
        name = ''
    # extract the job name from the ROOT folder
    if fpath is not None:
        # split until the root folder
        if re.search(ROOT_FOLDER, fpath):
            s = re.split(ROOT_FOLDER,fpath)
            if len(s) > 1:
                s = s[1]
                name = re.sub(r'[/|\\]+', '/', s) # replace
                name = name.split()[0] # get the first word
    return name


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
        d = pd.read_csv(inpt, nrows=0, sep="\t", index_col=False)
    else:
        d = inpt
    # determines which kind of searh engines we have.
    search_engines = ["PD","Comet-with-comm","Comet","MSFragger","MaxQuant"]
    cond = (
        all(c in list(d.columns) for c in PD.COLS_NEEDED), # PD
        len(d.columns) == 4, # Comet-with-comm (the first row is a comment)
        all(c in list(d.columns) for c in Comet.COLS_NEEDED), # Comet without the comment line
        all(c in list(d.columns) for c in MSFragger.COLS_NEEDED), # MSFragger
    )
    se = [i for (i, v) in zip(search_engines, cond) if v]
    se = se[0] if se else None
    return se


def select_search_engine(d):
    # determines which kind of searh engines we have.
    search_engines = ["PD","Comet-with-comm","Comet","MSFragger","MaxQuant"]
    cond = (
        all(c in list(d.columns) for c in PD.COLS_NEEDED), # PD
        len(d.columns) == 4, # Comet-with-comm (the first row is a comment)
        all(c in list(d.columns) for c in Comet.COLS_NEEDED), # Comet without the comment line
        all(c in list(d.columns) for c in MSFragger.COLS_NEEDED), # MSFragger
    )
    se = [i for (i, v) in zip(search_engines, cond) if v]
    se = se[0] if se else None
    return se


def read_task_table(ifile):
    '''
    read the task table
    '''
    indata = pd.DataFrame()
    # read the multiple input files to string and split by command
    with open(ifile, "r") as file:
        idta = file.read()
    # read table
    # add if the parameter if the command is executed in one time for all table
    d = pd.read_csv(io.StringIO(idta), sep='\t', dtype=str, skip_blank_lines=True).dropna(how="all").dropna(how="all", axis=1).astype('str')
    # # discard the rows when the first empty columns
    # if not d.empty:
    #     l = list(d[d.iloc[:,0] == 'nan'].index)
    #     d = d.drop(l)
    indata = d
    return indata


def read_commands_from_tables(ttablefiles):
    '''
    dropping empty rows and empty columns
    create a dictionary with the concatenation of dataframes for each command
    '''
    indata = dict()
    for ttablefile in ttablefiles:
        c = ttablefile['name']
        indata[c] = {}
        # if ttable exists, it includes it
        if 'ttables' in ttablefile:
            indata[c]['ttables']=[]
            for ttable in ttablefile['ttables']:
                tf = ttable['file']
                with open(tf, "r") as file:
                    idta = file.read()
                # read table
                # add if the parameter if the command is executed in one time for all table
                # replace the '\' to '/'
                d = pd.read_csv(io.StringIO(idta), sep='\t', dtype=str, skip_blank_lines=True).dropna(how="all").dropna(how="all", axis=1).astype('str')
                if not d.empty:
                    d = d.replace('\\','/')
                    indata[c]['ttables'].append(d)
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
                df_new = df.loc[idx.index.to_list(),:]
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
    def _crumble_condition(df, cmp_str):
        try:
            # extract the variable/operator/values from the logical condition
            x = re.match(rf"^(.*)\s*({rc})\s*(.*)$", cmp_str)
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
            # replace empty values with nan
            d = d.mask(d == '')
            # fill nan with inf
            d = d.fillna(np.inf)
        except Exception as exc:
            # not filter
            logging.error(f"There was a problem crumbling the condition: {cmp_str}\n{exc}")
            d = df
        return (d, var, cmp, val)

    def _eval_or_condition(df, idx, cmp_str):
        # crumble the simplest condition (var operator value)
        (d, var, cmp, val) = _crumble_condition(df, cmp_str)
        try:
            # evaluate the condition getting any value
            ix = pd.eval(f"(d {cmp} {val})").any(axis=1)
            # comparison between given serie and calculated
            if not idx.empty:
                if not ix.empty:
                    idx = pd.eval("(idx | ix)")
            else:
                idx = ix
        except Exception as exc:
            # not filter
            logging.error(f"There was a problem evaling the condition: {cmp_str}\n{exc}")
        return idx

    def _eval_and_condition(idx, ix):
        try:
            # comparison between given serie and calculated
            if not idx.empty:
                if not ix.empty:
                    idx = pd.eval("(idx & ix)")
            else:
                idx = ix
        except Exception as exc:
            # not filter
            logging.error(f"There was a problem evaling the 'and' condition:\n{exc}")
        return idx

    # variable with the boolean operators
    comparisons = ['>=', '<=', '!=', '<>', '==', '>', '<']
    rc = r'|'.join(comparisons)
    # variable with index
    idx_a = pd.Series([])
    
    # split the conditions by & operator
    comps_and = re.split('\&',flt)
    for cmp_a in comps_and:
        cmp_a = re.sub(r"^\s*\(\s*|\s*\)\s*$", '', cmp_a) # trim whitespaces and parenthesis

        # split the conditions by | operator        
        comps_or = re.split('\|',cmp_a)
        idx_o = pd.Series([]) # variable with index for 'or' conditions
        for cmp_o in comps_or:
            cmp_o = re.sub(r"^\s*\(\s*|\s*\)\s*$", '', cmp_o) # trim whitespaces and parenthesis
            # evaluate the 'or' condition
            idx_o = _eval_or_condition(df, idx_o, cmp_o)
        # evaluate the 'and' condition
        idx_a = _eval_and_condition(idx_a, idx_o)
    
    # extract the dataframe from the index
    try:        
        if not idx_a.empty:
            df_new = df[idx_a]
    except Exception as exc:
        # not filter
        logging.error(f"It is not filtered. There was a problem extracting the datafram from the index rows: {exc}")
        df_new = df

    return df_new

def print_tmpfile(df, outfile):
    '''
    Print tmpfile
    '''
    # create workspace
    if not os.path.exists(os.path.dirname(outfile)):
        os.makedirs(os.path.dirname(outfile), exist_ok=False)
    # remove obsolete file
    ofile = f"{outfile}.tmp"
    if os.path.isfile(ofile):
        os.remove(ofile)
    # print
    df.to_csv(ofile, index=False, sep="\t", line_terminator='\n')
    return ofile


def rename_tmpfile(f):
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
    return ofile


def create_workspace_from_file(f):
    '''
    Create a directory from a file path
    '''
    try:
        d = os.path.dirname(f)
        if not os.path.exists(d):
            os.makedirs(d, exist_ok=False)
    except:
        return None
    return None


if __name__ == "__main__":
	print("It is a library used by SanXoT and its adaptor modules")