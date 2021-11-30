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
import sys
import argparse
import logging
import pandas as pd
import numpy as np
import concurrent.futures
from sklearn import preprocessing
import lxml.etree as ET
import base64
import zlib
from scipy.optimize import nnls
import itertools
import shutil


#########################
# Import local packages #
#########################
sys.path.append(f"{os.path.dirname(__file__)}/libs")
import createID


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

def prepare_params(df, refile, outdir):
    '''
    Prepare the parameters to get the quantification

    Parameters
    ----------
    idf : TYPE
        DESCRIPTION.
    quantbl : TYPE
        DESCRIPTION.
    retbl : TYPE
        DESCRIPTION.

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
      5 => '{Identification file}',
      6 => '{Dataframe with the Mass Tags for the given type of TMT}',
      ]
    ]
    '''
    # get the input parameters based on the experiment in tuple df=(exp,df)
    exp = df[0]
    indata = df[1]

    # read the isotopic distribution table
    retbl = createID.read_infiles(refile)

    # extract the quantification files and the experiemnt name
    q = indata[['mzfile','experiment','type_tmt']]
    s = list(indata['infile'])
    q.insert(0,'Spectrum_File', [os.path.basename(x) for x in s])
    q = q.drop_duplicates().values.tolist()
    
    # read the identification table based on the experiment
    indir_e = os.path.join(outdir, exp)
    idefile = f"{indir_e}/ID.tsv"
    idetbl = createID.read_infiles(idefile)
    # get the list of scans for each identification
    i = idetbl[['Scan','Spectrum_File']]
    i = i.drop_duplicates()
    i = i.groupby('Spectrum_File')['Scan'].apply(list).reset_index()
    i = i.values.tolist()
    
    # from the same spectrum FILENAME, we get the scan list
    # r => [['spectrum_file','mzfile','experiment','type_tmt']]
    # a => [['spectrum_file','scan_list']]
    # add the identification file (ID.tsv)
    # add the table of isotopic distrution depending on the type of TMT
    qff = [ x+[y[1]]+[idefile]+[retbl[retbl['type_tmt'] == x[3].upper()]] for x,y in zip(q,i) if x[0]==y[0] ]
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
      5 => '{Identification file}',
      6 => '{Dataframe with the Mass Tags for the given type of TMT}',
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
    isom = params[6]
    
    isocorrm = correcmatrix(type_tmt, isom)
    isoname, isotag = isobaric_labelling(type_tmt, isom)
    if isinstance(isocorrm, np.ndarray) and isoname != [None] and isotag != [None]:
        quant = parser_mz(mzfile, spec_basename, type_tmt, isotag, isoname, isocorrm, scan_list)
    
    return quant

def merge_quantification(itup, params):
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
    exp = itup[0]
    quant = itup[1]
    
    # get the params based on experiment
    p = [ x for x in params if x[0] == exp][0]
    
    # get identification file
    idefile = p[5]
    
    # read the identification table based on the experiment
    idetbl = createID.read_infiles(idefile)
    
    # add the quantification columns based on "scan" and "basename" of spectrum file    
    df = idetbl.merge(quant, left_on=["Scan","Spectrum_File"], right_on=["Scan","Spectrum_File"], how='left', suffixes=('_old', ''))
    df.drop(df.filter(regex='_old$').columns.tolist(), axis=1, inplace=True)
    
    return df

def copy_by_experiment(exp, outdir):
    '''
    Print the output file by experiments
    '''
    # get file names
    outdir_e = os.path.join(outdir, exp)
    ifile = f"{outdir_e}/ID.tsv"
    ofile = f"{outdir_e}/ID-quant.tsv"
    # remove obsolete file
    if os.path.isfile(ofile):
        os.remove(ofile)
    # copy file
    try:
        shutil.copyfile(ifile, ofile)
        pass
    except Exception:
        sms = f"Error copying files: {ifile}"
        print(sms) # message to stdout with logging output
        sys.exit(sms)
        pass    
    return ofile

    
def main(args):
    '''
    Main function
    '''
    logging.info("read the quantification table")
    indata = createID.read_task_table(args.intbl)
    if indata.empty:
        sms = "There is not task-table"
        logging.error(sms)
        sys.exit(sms)

    

    # check if mzfile and type_tmt columns are fillin. Otherwise, the program does nothing.
    c = indata.columns.tolist()
    if 'mzfile' in c and 'type_tmt' in c and not all(indata['mzfile'].str.isspace()) and not all(indata['type_tmt'].str.isspace()):    
    
        infiles = [createID.get_path_file(i, args.indir) for i in list(indata['mzfile']) if not pd.isna(i)]
        indata['mzfile'] = infiles
        logging.debug(infiles)
        
        
        logging.info("prepare the parameters")
        with concurrent.futures.ProcessPoolExecutor(max_workers=args.n_workers) as executor:            
            params = executor.map(prepare_params, list(indata.groupby("experiment")), itertools.repeat(args.retbl), itertools.repeat(args.outdir))
        params = list(params)
        # params = prepare_params(list(indata.groupby("experiment"))[0], args.retbl, args.outdir)
    
    
        logging.info("extract the quantification")
        with concurrent.futures.ProcessPoolExecutor(max_workers=args.n_workers) as executor:            
            quant = executor.map(extract_quantification, params)
        quant = pd.concat(quant)
        # quant = extract_quantification(params[0])
        
        
        logging.info("merge the quantification")
        with concurrent.futures.ProcessPoolExecutor(max_workers=args.n_workers) as executor:            
            idequant = executor.map(merge_quantification, list(quant.groupby("Spectrum_File")), itertools.repeat(params))
        idequant = pd.concat(idequant)
        # idequant = merge_quantification(list(quant.groupby("Spectrum_File"))[0], params)
    
    
        logging.info("print the ID files by experiments")
        with concurrent.futures.ProcessPoolExecutor(max_workers=args.n_workers) as executor:        
            tmpfiles = executor.map( createID.print_by_experiment,
                                    list(idequant.groupby("Experiment")),
                                    itertools.repeat(args.outdir),
                                    itertools.repeat("ID-quant.tsv") )  
        # rename tmp file deleting before the original file 
        [createID.print_outfile(f) for f in list(tmpfiles)]

    # the program "does anything"... copy the ID.tsv to ID-quant.tsv
    else:
    
        logging.info("extract the list of experiments")
        Expt = list(indata['experiment'].unique())
        logging.debug(Expt)


        logging.info("copy the identify files to quantify files from the list of experiments")
        with concurrent.futures.ProcessPoolExecutor(max_workers=args.n_workers) as executor:        
            tmpfiles = executor.map( copy_by_experiment, Expt, itertools.repeat(args.outdir) )  
        # rename tmp file deleting before the original file 
        [createID.print_outfile(f) for f in list(tmpfiles)]
    
    
        
if __name__ == '__main__':    
    # parse arguments
    parser = argparse.ArgumentParser(
        description='Extract the quantification from mzML',
        epilog='''
        Example:
            python quantification.py

        ''')
    parser.add_argument('-w',  '--n_workers', type=int, default=2, help='Number of threads/n_workers (default: %(default)s)')
    parser.add_argument('-i',  '--indir', required=True, help='Input Directory')
    parser.add_argument('-t',  '--intbl', required=True, help='File with the input data: filename, experiments, mzfile, type_tmt')
    parser.add_argument('-r',  '--retbl', required=True, help='File that reports the ion isotopic distribution')
    parser.add_argument('-o',  '--outdir',  required=True, help='Output directory')
    parser.add_argument('-xx', '--phantom_infiles',  help='Phantom Input files needed for the iSanXoT workflow (snakemake)')
    parser.add_argument('-x',  '--phantom_outfiles',  help='Phantom Output files needed for the iSanXoT workflow (snakemake)')
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
