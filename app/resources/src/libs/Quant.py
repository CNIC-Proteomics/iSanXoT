#!/usr/bin/python

# Module metadata variables
__author__ = ["Ricardo Magni", "Jose Rodriguez"]
__credits__ = ["Ricardo Magni", "Jose Rodriguez", "Jesus Vazquez"]
__license__ = "Creative Commons Attribution-NonCommercial-NoDerivs 4.0 Unported License https://creativecommons.org/licenses/by-nc-nd/4.0/"
__version__ = "1.0.1"
__maintainer__ = "Jose Rodriguez"
__email__ = "jmrodriguezc@cnic.es"
__status__ = "Development"

# import modules
import os
import pandas as pd
import numpy as np
from sklearn import preprocessing
import lxml.etree as ET
import base64
import zlib
from scipy.optimize import nnls



###################
# Local functions #
###################

######################## Tags and correction functions ############    

def correcmatrix(df):
    '''
    Correct and normalize the matrix of isotopic distribution
    '''
    if not df.empty:
        try:
            # get the columns with ONLY the percentage values and tags
            cols = [c for c in df.columns if c not in ['type_tmt', 'tag', 'reporter_ion']]
            m = df[cols]
            # get the tags
            tags = df[['tag']]
            
            # extract the type of TMT. Remove leading and trailing whitespaces. Uppercase
            tmt = df['type_tmt'].unique()[0].strip().upper()

            # create an object that compare the ison distribution and the positions up or down
            # that determines the tag that wins or loose the interference
            dist_pos = None
            if tmt == 'TMT10' or tmt == 'TMT11':
                # distribution column and the number of cells up or down.
                # eg. -2 column the cells going 4 position up 4; '1' columns, the cells going 2 positions down
                dist_pos = {'-2': 4, '-1': 2, 'monoisotopic': 0, '1': -2, '2': -4}
            elif tmt == 'TMT16' or tmt == 'TMT18':
                # distribution column and the number of cells up or down.
                # eg. -2 column the cells going 4 position up 4; '1' columns, the cells going 2 positions down
                dist_pos = {'-13C_-13C': 4,
                            '-13C_-15N': 3,
                            '-13C': 2,
                            '-15N': 1,
                            'monoisotopic': 0,
                            '+15N': -1,
                            '+13C': -2,
                            '+15N_+13C': -3,
                            '+13C_+13C': -4 }

            if dist_pos is not None:
                # add the tags in the cells where the percentage full down on tag
                for k,v in dist_pos.items():
                    tags[k] = tags['tag'].shift(v)
                # concat the tag labels and the percentage values (in this order!!)
                m = pd.concat([tags, m], axis=1)
                
                # create a matrix with the following pairs: tag_x, tag_y, percentage
                # for the all comparisons
                # the column name of tag_y and percentage has the same name
                ms = []
                for k in dist_pos.keys():
                    # get tag_x, tag_y (from key), percentage (from key)
                    a = m[['tag',k]]
                    # drop the row with nan
                    a.dropna(how='any',axis=0, inplace=True)
                    # rename columns
                    a.columns = ['tag_y', 'tag_x', 'corr']
                    # change order columns
                    a = a[['tag_x', 'tag_y', 'corr']]
                    # create a list
                    ms.append(a)
                m_pos = pd.concat(ms, axis=0)
                m_pos = m_pos.reset_index(drop=True)
                
                # make symetric matrix from list of pairs
                isocorrm = m_pos.pivot(*m_pos)
                # sort the index and columns fron the list of tags
                t = tags['tag'].values
                isocorrm = isocorrm.reindex(t)
                isocorrm = isocorrm[t]
                # fill Nan to 0
                isocorrm = isocorrm.fillna(0)
                
                # convert numpy list of list
                isocorrm = isocorrm.to_numpy()
                # percentage to [0,1]
                isocorrm = isocorrm / 100
                # normalize
                isocorrm = preprocessing.normalize(isocorrm, axis=0, norm='l1')

            else:
                tmt,isocorrm = None,[None]
            pass
        except Exception:
            tmt,isocorrm = None,[None]
            pass
    else:
        tmt,isocorrm = None,[None]
    return tmt,isocorrm

def isobaric_labelling(df):
    '''
    Get the isobaric labels from the matrix of isotopic distribution
    '''    
    try:
        p = df[['tag','reporter_ion']]
        p = p.values.T.tolist()
        pass
    except Exception:
        pass
        p = [[None],[None]]
        
    return p

def monoisocorrec(b1, isocorrm):
    '''    
    TMT 10plex reporter isotopic Distributions correction
    '''
    b1 = np.array(b1)
    b1 = nnls(isocorrm, b1.astype("float32"))[0]   
    return b1

def get_quant(spec_mz, spec_int, isotag, isocorrm):
    '''
    Get ion quantification
    '''
    ppm = 20
    p1 = []
    po = np.zeros(len(spec_mz), dtype=bool)
    for i,j in enumerate(isotag): 
        if np.any( np.logical_and(np.greater_equal(spec_mz, j-j*ppm*1e-6), np.less_equal(spec_mz, j+j*ppm*1e-6)) ) == True:
            po += np.logical_and(np.greater_equal(spec_mz, j-j*ppm*1e-6), np.less_equal(spec_mz, j+j*ppm*1e-6))
            p1.append(i)

    spec_mz = spec_mz[po]
    spec_int = spec_int[po]
    p1 = np.array(p1)
    
    b1 = []
    for i in np.arange(len(isotag)):
        b2 = spec_int[np.where(p1==i)]    
        if len(b2) == 0:
            b1.append(0)
        else:
            b1.append(b2[0])
    
    if isinstance(isocorrm, np.ndarray):
        b1 = monoisocorrec(b1, isocorrm)
    
    return b1


######################## Parse mzml functions ############

def array_decoder(a, ctype, dtypea):
    '''
    Decode bin64
    '''
    if a is not None:
        a = base64.b64decode(a)
        if ctype == "zlib compression":
            a = np.frombuffer(zlib.decompress(a), dtype=dtypea)
        else:
            a = np.frombuffer(a, dtype=dtypea)
        return a.astype('float32')
    else:
        return np.array([])

def get_spectrum_values(elem, isotag, isocorrm):
    '''
    Get the values of spectrum
    '''
    
    val = []
    type_array = { "64-bit float": np.float64, "32-bit float": np.float32 }
    class_array = { "m/z array": "mz", "intensity array": "i" }
    spec = {
        "sn": int(elem.attrib["id"].split("scan=")[1].split(" ")[0]),
        "mslevel": "",
        "psn": ""
    }
    for e in elem.iterdescendants(tag="{http://psi.hupo.org/ms/mzml}*"):
        if e.tag == "{http://psi.hupo.org/ms/mzml}cvParam":        
            if e.attrib["name"] == "ms level":
                spec["mslevel"] = int(e.attrib["value"])
        elif e.tag == "{http://psi.hupo.org/ms/mzml}precursor":
            spec["psn"] = int(e.attrib["spectrumRef"].split("scan=")[1].split(" ")[0])
        elif e.tag=="{http://psi.hupo.org/ms/mzml}binaryDataArray":
            if spec["mslevel"] == 2 or spec["mslevel"] == 3:
                if spec["mslevel"] == 3: spec["sn"] = spec["psn"]
                val = [
                    e[0].attrib["name"],
                    e[1].attrib["name"],
                    e[2].attrib["name"]
                ]
                ctype = ["zlib compression" if "zlib compression" in val else ""][0]
                dtypea = [(type_array[k]) for k in val if k in type_array][0]
                vname = [(class_array[k]) for k in val if k in class_array][0]
                spec[vname] = e[3].text
                spec[vname] = array_decoder(spec[vname], ctype, dtypea)       
        else:
            continue
        
    del spec["psn"]
    
    if spec["mslevel"] == 1:
        return None
    else:
        for i,a in enumerate( get_quant(spec["mz"], spec["i"], isotag, isocorrm) ): spec[i] = a        
        del spec["mz"]
        del spec["i"]
        return list(spec.values())
            

def fast_iter(file, isotag, isocorrm):
    '''
    For each spectrum element, we get the wanted values.
    '''
    fh = []
    for _, elem in ET.iterparse(file, events=("end",), tag="{http://psi.hupo.org/ms/mzml}spectrum", remove_blank_text=True):
        fha = get_spectrum_values(elem, isotag, isocorrm)        
        if fha != None:
            fh.append(fha)
        # It's safe to call clear() here because no descendants will be accessed
        elem.clear()
        # # Also eliminate now-empty references from the root node to elem
        # for ancestor in elem.xpath('ancestor-or-self::*'):
        #     while ancestor.getprevious() is not None:
        #         del ancestor.getparent()[0]
    return fh


    
def parser_mzML(file, isotag, isoname, isocorrm):
    '''
    Parse the Mass Espectometry outputs in mzML format.
    '''
    fh = fast_iter(file, isotag, isocorrm)
    return fh

def parser_mz(file, spec_name, isotag, isoname, isocorrm, scan_list=None):
    '''    
    Parse the Mass Espectometry outputs in several formats.
    '''
    # parse the mz file
    fh = []
    if file is not None and file.strip().endswith('.mzML'):
        fh = parser_mzML(file, isotag, isoname, isocorrm)

    # create df with the columns of tags
    columns = ["Scan","Quant level"]+isoname
    columns = list(filter(None, columns))
    df = pd.DataFrame(fh,columns=columns)
    
    # add the Spectrum Name which is the Basename of file
    df["Spectrum_File"] = spec_name
    
    # get the quantifications for each scan, if apply
    if scan_list: df = df[df["Scan"].isin(scan_list)]
    
    return df

######################## main functions ############

def prepare_params(tpl):
    '''
    Prepare the parameters to get the quantification. It will be a list of spectrum file (for each experiment)

    Returns
    -------
    qff : (List of list)
    [
      [
      0 => '{Spectrum File}',
      1 => '{mz file}',
      2 => '{Name of experiment}',
      3 => '{Ion distribution file}',
      4 => '{scan list for the Spectrum_File}',
      5 => '{Dataframe that reports the Ion Distribution}',
      ]
    ]
    '''
    # get the input parameters based on the experiment in tuple df=(exp,df)
    spec = tpl[0]
    idedf = tpl[1]
    indata = tpl[2]

    # extract the files from the spectrum, quantification files and correction
    q = indata[['spectrum_file','mzfile','quan_method']]
    q.rename(columns={'spectrum_file': 'Spectrum_File'}, inplace=True)
    q = sorted(q.drop_duplicates().values.tolist(), key=lambda x: x[0]) # sort by the Spectrum_File

    # get the list of scans (for each Spectrum file)
    i = idedf[['Scan','Spectrum_File']]
    i = i.drop_duplicates()
    i = i.groupby('Spectrum_File')['Scan'].apply(list).reset_index()
    i = sorted(i.values.tolist(), key=lambda x: x[0]) # sort by the Spectrum_File
    
    # add the table of isotopic distrution depending from the input file (Ion distribution file)
    qff = [ x+[y[1]]+[pd.read_csv(x[2], sep="\t", comment='#', na_values=['NA'], low_memory=False)] for x,y in zip(q,i) if x[0]==y[0] ]
    
    return qff

def extract_quantification(params):
    '''
    Extract the quantification from the mzML files 
    
    Parameters
    ----------
    params : List of parameters:
      [
      0 => '{Spectrum File}',
      1 => '{mz file}',
      2 => '{Name of experiment}',
      3 => '{Ion distribution file}',
      4 => '{scan list for the Spectrum_File}',
      5 => '{Dataframe that reports the Ion Distribution}',
      ]

    Returns
    -------
    quant: quantifications.

    '''
    # # get the input parameters based on the list of lists
    # params = params[0]

    # print("extract_quantification 2 ----")
    # # print(params)
    # print(params[0])
    # print(params[5])
    # print("-----\n\n")
    
    # get params values
    spec_basename = params[0]
    mzfile = params[1]
    ion_file = params[2]
    scan_list = params[3]
    isom = params[4]
    
    label_tmt,isocorrm = correcmatrix(isom)
    isoname, isotag = isobaric_labelling(isom)
    if isinstance(isocorrm, np.ndarray) and isoname != [None] and isotag != [None]:
        quant = parser_mz(mzfile, spec_basename, isotag, isoname, isocorrm, scan_list)
    
    return quant

def merge_quantification(ieddf, iqddf):
    '''
    Merge the identification and quantification tables

    Parameters
    ----------
    quant : Dataframe
        Quantifaction table.
    params : List of parameters:
      [
      0 => '{Spectrum File}',
      1 => '{mz file}',
      2 => '{Name of experiment}',
      3 => '{Ion distribution file}',
      4 => '{scan list for the Spectrum_File}',
      5 => '{Identification file}',
      6 => '{Dataframe with the Mass Tags for the given type of TMT}',
      ]

    Returns
    -------
    df : TYPE
        DESCRIPTION.
    '''
    # get the input parameters based on the experiment in tuple df=(exp,df)
    idedf = ieddf[1]
    quadf = iqddf[1]

    # add the quantification columns based on "scan" and "basename" of spectrum file    
    df = idedf.merge(quadf, left_on=["Scan","Spectrum_File"], right_on=["Scan","Spectrum_File"], how='left', suffixes=('_old', ''))
    df.drop(df.filter(regex='_old$').columns.tolist(), axis=1, inplace=True)
    
    return df


if __name__ == "__main__":
	print("It is a library used by SanXoT and its adaptor modules")