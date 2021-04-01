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

def correcmatrix(tmt, df):
    '''
    Correct and normalize the matrix of isotopic distribution
    '''
    if not df.empty:
        try:
            ### TMT 10plex reporter isotopic Distributions matrix###
            if tmt.upper() == 'TMT10':
                m = df[["-2","-1","1","2"]].values.T
                isocorrm = np.array([
                    [100    , 0      , m[1][2], 0      , m[0][4], 0      , 0      , 0      , 0      , 0      ],
                    [0      , 100    , 0      , m[1][3], 0      , m[0][5], 0      , 0      , 0      , 0      ],
                    [m[2][0], 0      , 100    , 0      , m[1][4], 0      , m[0][6], 0      , 0      , 0      ],
                    [0      , m[2][1], 0      , 100    , 0      , m[1][5], 0      , m[0][7], 0      , 0      ],
                    [m[3][0], 0      , m[2][2], 0      , 100    , 0      , m[1][6], 0      , m[0][8], 0      ],
                    [0      , m[3][1], 0      , m[2][3], 0      , 100    , 0      , m[1][7], 0      , m[0][9]],
                    [0      , 0      , m[3][2], 0      , m[2][4], 0      , 100    , 0      , m[1][8], 0      ],
                    [0      , 0      , 0      , m[3][3], 0      , m[2][5], 0      , 100    , 0      , m[1][9]],
                    [0      , 0      , 0      , 0      , m[3][4], 0      , m[2][6], 0      , 100    , 0      ],
                    [0      , 0      , 0      , 0      , 0      , m[3][5], 0      , m[2][7], 0      , 100    ]
                ])/100
            isocorrm = preprocessing.normalize(isocorrm, axis=0, norm='l1')
            pass
        except Exception:
            isocorrm = [None]
            pass
    else:
        isocorrm = [None] 
    return isocorrm

def isobaric_labelling(tmt, df):
    '''
    Get the isobaric labels from the matrix of isotopic distribution
    '''    
    try:
        p = df[df['type_tmt'] == tmt.upper()][['tag','reporter_ion']]
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

def get_quant(spec_mz, spec_int, label, isotag, isocorrm):
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
    
    if label == "TMT10":
        b1 = monoisocorrec(b1, isocorrm)
    
    return b1


######################## Parse mzml functions ############

def array_decoder(a, ctype, dtypea):
    '''
    Decode bin64
    '''
    a = base64.b64decode(a)
    if ctype == "zlib compression":
        a = np.frombuffer(zlib.decompress(a), dtype=dtypea)
    else:
        a = np.frombuffer(a, dtype=dtypea)
    return a.astype('float32')

def get_spectrum_values(elem, label, isotag, isocorrm):
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
        for i,a in enumerate( get_quant(spec["mz"], spec["i"], label, isotag, isocorrm) ): spec[i] = a        
        del spec["mz"]
        del spec["i"]
        return list(spec.values())
            

def fast_iter(file, label, isotag, isocorrm):
    '''
    For each spectrum element, we get the wanted values.
    '''
    fh = []
    for _, elem in ET.iterparse(file, events=("end",), tag="{http://psi.hupo.org/ms/mzml}spectrum", remove_blank_text=True):
        fha = get_spectrum_values(elem, label, isotag, isocorrm)        
        if fha != None:
            fh.append(fha)
        # It's safe to call clear() here because no descendants will be accessed
        elem.clear()
        # # Also eliminate now-empty references from the root node to elem
        # for ancestor in elem.xpath('ancestor-or-self::*'):
        #     while ancestor.getprevious() is not None:
        #         del ancestor.getparent()[0]
    return fh


    
def parser_mzML(file, label, isotag, isoname, isocorrm):
    '''
    Parse the Mass Espectometry outputs in mzML format.
    '''
    fh = fast_iter(file, label, isotag, isocorrm)
    return fh

def parser_mz(file, spec_name, label, isotag, isoname, isocorrm, scan_list=None):
    '''    
    Parse the Mass Espectometry outputs in several formats.
    
    Parameters
    ----------
    file : TYPE
        DESCRIPTION.
    label : TYPE
        DESCRIPTION.
    isotag : TYPE
        DESCRIPTION.
    isoname : TYPE
        DESCRIPTION.
    isocorrm : TYPE
        DESCRIPTION.

    Returns
    -------
    fh : TYPE
        DESCRIPTION.

    '''
    # parse the mz file
    fh = []
    if file is not None and file.strip().endswith('.mzML'):
        fh = parser_mzML(file, label, isotag, isoname, isocorrm)

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

def prepare_params(ieddf, inddf, retbl):
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
      3 => '{Type of TMT: TMT10, TMT11, TMT16, etc}',
      4 => '{scan list for the Spectrum_FILENAME}',
      5 => '{Dataframe with the Mass Tags for the given type of TMT}',
      ]
    ]
    '''
    # get the input parameters based on the experiment in tuple df=(exp,df)
    idedf = ieddf[1]
    indata = inddf[1]

    # extract the quantification files and the experiemnt name
    # q => [['spectrum_file','mzfile','experiment','type_tmt']]
    q = indata[['mzfile','experiment','type_tmt']]
    s = list(indata['infile'])
    q.insert(0,'Spectrum_File', [os.path.basename(x) for x in s])
    q = q.drop_duplicates().values.tolist()

    # get the list of scans (for each Spectrum file)
    # a => [['spectrum_file','scan_list']]
    i = idedf[['Scan','Spectrum_File']]
    i = i.drop_duplicates()
    i = i.groupby('Spectrum_File')['Scan'].apply(list).reset_index()
    i = i.values.tolist()
    
    # add the table of isotopic distrution depending on the type of TMT
    qff = [ x+[y[1]]+[retbl[retbl['type_tmt'] == x[3].upper()]] for x,y in zip(q,i) if x[0]==y[0] ]
    qff = [i for s in qff for i in s] # flat list
    
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
      3 => '{Type of TMT: TMT10, TMT11, TMT16, etc}',
      4 => '{scan list for the Spectrum_FILENAME}',
      5 => '{Dataframe with the Mass Tags for the given type of TMT}',
      ]

    Returns
    -------
    quant: quantifications.

    '''
    # get params values
    spec_basename = params[0]
    mzfile = params[1]
    type_tmt = params[3]
    scan_list = params[4]
    isom = params[5]
    
    isocorrm = correcmatrix(type_tmt, isom)
    isoname, isotag = isobaric_labelling(type_tmt, isom)
    if isinstance(isocorrm, np.ndarray) and isoname != [None] and isotag != [None]:
        quant = parser_mz(mzfile, spec_basename, type_tmt, isotag, isoname, isocorrm, scan_list)
    
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
      3 => '{Type of TMT: TMT10, TMT11, TMT16, etc}',
      4 => '{scan list for the Spectrum_FILENAME}',
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
	print("It is a library used by preSanXoT and its satellite module")