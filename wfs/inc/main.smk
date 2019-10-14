import os
import pandas
import re
import json

def replace_consts(config):
    '''
    Just in case, replace the constants
    '''
    # Config variables for workflow
    infile_dat         = config["indata"].replace("\\", "/")
    indir              = config["indir"].replace("\\", "/")
    # infile_names       = config["infilenames"]
    infile_db          = config["dbfile"].replace("\\", "/")
    infile_cat         = config["catfile"].replace("\\", "/")
    outdir             = config["outdir"].replace("\\", "/")
    tmpdir             = config["tmpdir"].replace("\\", "/")
    rstdir             = config["rstdir"].replace("\\", "/")
    logdir             = config["logdir"].replace("\\", "/")
    # replace tag-constant values
    cfg_string = json.dumps(config)
    cfg_string = cfg_string.replace("--WF__INDATA--", infile_dat)
    cfg_string = cfg_string.replace("--WF__INDIR--", indir)
    # cfg_string = cfg_string.replace("--WF__INFILE__NAMES--", infile_names)
    cfg_string = cfg_string.replace("--WF__INFILE__DB--", infile_db)
    cfg_string = cfg_string.replace("--WF__INFILE__CAT--", infile_cat)
    cfg_string = cfg_string.replace("--WF__OUTDIR--", outdir)
    cfg_string = cfg_string.replace("--WF__WKS__TMPDIR--", tmpdir)
    cfg_string = cfg_string.replace("--WF__WKS__RSTDIR--", rstdir)
    cfg_string = cfg_string.replace("--WF__WKS__LOGDIR--", logdir)
    config = json.loads(cfg_string)
    # write data in a file. 
    # cfg_file = open(outdir+"/isanxot_cfg_2.json","w")  
    # cfg_file.writelines( json.dumps(json.loads(cfg_string), indent=2, sort_keys=False) ) 
    # cfg_file.close()
    return config

# Env. variables
ISANXOT_SRC_HOME       = os.environ['ISANXOT_SRC_HOME']
ISANXOT_PYTHON3x_HOME  = os.environ['ISANXOT_PYTHON3x_HOME']

# Config variables for workflow
config = replace_consts(config) # just in case, replace the constanst to their values
INFILE_DAT         = config["indata"]
INDIR              = config["indir"]
INFILE_NAMES       = config["infilenames"]
INFILE_DB          = config["dbfile"]
INFILE_CAT         = config["catfile"]
OUTDIR             = config["outdir"]
TMP_OUTDIR         = config["tmpdir"]
RST_OUTDIR         = config["rstdir"]
LOG_OUTDIR         = config["logdir"]
CONF_RULES         = config["workflow"]["rules"]
RULES              = [ r["name"] for r in CONF_RULES ]
WF_VERBOSE_MODE    = " -vv " if config["workflow"]["verbose"] else ""



def load_indata(ifile):
    '''
    Handles the input data (output files for the workflow)
    '''
    # init 
    indata,indata_expto,indata_names = {},[],[]

    # read input data
    df_indata = pandas.read_csv(ifile, converters={"experiment":str, "name":str, "ratio_numerator":str, "ratio_denominator":str})

    # load experiments and names
    indata_expto = df_indata["experiment"].unique()
    indata_names = df_indata["name"].unique()

    # apply the corrected methods for the experiments info
    # output files created by sanxot workflow
    # for each row
    for idx, indat in df_indata.iterrows():
        exp       = indat["experiment"]
        name      = indat["name"]
        ratio_num = indat["ratio_numerator"]
        ratio_den = indat["ratio_denominator"]
        sp_fdr    = indat["s>p FDR"]
        pq_fdr    = indat["p>q FDR"]
        qc_fdr    = indat["q>c FDR"]
        sp_var    = indat["s>p Var(x)"]
        pq_var    = indat["p>q Var(x)"]
        qc_var    = indat["q>c Var(x)"]
        # init variable for experiment
        if exp not in indata:
            indata[exp] = {}
            indata[exp]["indir"] = INDIR
            indata[exp]["outdir"] = TMP_OUTDIR
            indata[exp]["names"] = {}
        indata[exp]["names"][name] = {}
        indata[exp]["names"][name]["s>p FDR"] = sp_fdr
        indata[exp]["names"][name]["p>q FDR"] = pq_fdr
        indata[exp]["names"][name]["q>c FDR"] = qc_fdr
        indata[exp]["names"][name]["s>p Var"] = sp_var
        indata[exp]["names"][name]["p>q Var"] = pq_var
        indata[exp]["names"][name]["q>c Var"] = qc_var
        # ratio numerator and denominator have to be defined
        if not pandas.isnull(ratio_num) and not pandas.isnull(ratio_den) and not ratio_num == "" and not ratio_den == "":
            indata[exp]["names"][name]["ratio_num"] = ratio_num
            indata[exp]["names"][name]["ratio_den"] = ratio_den

    return indata,indata_expto,indata_names

def setup_outfiles_from_indata():
    '''
    Handles the input data (output files for the workflow)
    '''
    # apply the rule executors to rule (method)
    for rule in CONF_RULES:
        if rule["enabled"]:
            inputs  = rule["inputs"]
            outputs = rule["outputs"]

            # rules that work on another directories
            if rule["executor"] == "on_outdir" or rule["executor"] == "indir_to_outdir" or rule["executor"] == "infiles_to_outdir":
                yield expand(["{outdir}/{fname}"], outdir=OUTDIR, fname=outputs)

            # rules that work on experiment directories
            if rule["executor"] == "indir_to_tmpdir":
                for exp, indat in INDATA.items():
                    yield expand(["{outdir}/{exp}/{fname}"], outdir=TMP_OUTDIR, exp=exp, fname=outputs)

            # rules that work on another directories
            if rule["executor"] == "on_rstdir" or rule["executor"] == "outdir_to_rstdir" or rule["executor"] == "tmpdir_to_rstdir" or rule["executor"] == "indir_to_rstdir":
                yield expand(["{outdir}/{fname}"], outdir=RST_OUTDIR, fname=outputs)

            # rules that work on experiment directories
            if rule["executor"] == "on_tmpdir" or rule["executor"] == "outdir_to_tmpdir" or rule["executor"] == "tmpdir_to_tmpdir":
                for exp, indat in INDATA.items():
                    for name in indat["names"]:
                        yield expand(["{outdir}/{exp}/{name}/{fname}"], outdir=TMP_OUTDIR, exp=exp, name=name, fname=outputs)


def replace_params(in_param, optrep=None, indir=None, tmpdir=None):
    '''
    Replace the variable values for the parameters
    '''
    if optrep:
        orep = dict((re.escape(k), v) for k, v in optrep.items())
        pattern = re.compile("|".join(orep.keys()))
        output = pattern.sub( lambda m: orep[re.escape(m.group(0))], in_param )
    else:        
        output = in_param if in_param is not None else ''
    return output


def extract_method_parameters(method, indir, outdir, optparam=None, optrep=None, tmpdir=None):
    '''
    Extract command execution of a method from the from an unique output file name
    '''
    inputs,params,outputs = '','',''
    # handle outputs
    if "inputs" in method:
        _dir = indir
        for key,value in method["inputs"].items():
            if isinstance(value, list):
                inputs  = ' {} '.format(key)
                for val in value:
                    inputs  += '"{}/{}" '.format(_dir, val) if _dir != "" else '"{}" '.format(val)
            else: # string
                inputs  += ' {} "{}/{}" '.format(key, _dir, value) if _dir != "" else ' {} "{}" '.format(key, value)
    # handle outputs
    if "outputs" in method:
        _dir = outdir
        for key,value in method["outputs"].items():
            if isinstance(value, list):
                outputs  = ' {} '.format(key)
                for val in value:
                    outputs  += '"{}/{}" '.format(_dir, val)
            else: # string
                outputs  += ' {} "{}/{}" '.format(key, _dir, value)
    # handle params
    if "params" in method:
        params = replace_params(method["params"], optrep=optrep) + replace_params(optparam)
    return inputs,params,outputs


def extract_method(rule_name, outputs):
    fnames = [os.path.basename(o) for o in outputs]
    r = next((r for r in CONF_RULES if r["name"] == rule_name and all(e in fnames for e in r["outputs"])), None)
    return r


def execute_methods(methods, indir, outdir, log, optparam=None, optrep=None, tmpdir=None):
    cmd  = ''
    # prepare temporal workspace
    if tmpdir:
        os.makedirs(tmpdir, exist_ok=True)
    # create command line for the whole methods
    for method in methods:
        interpret = ISANXOT_PYTHON3x_HOME+'/tools/python'
        script    = ISANXOT_SRC_HOME+'/src/'+method["script"]
        inputs, params, outputs = extract_method_parameters(method, indir, outdir, optparam=optparam, optrep=optrep, tmpdir=tmpdir)
        cmd  += '"{}" "{}" {} {} {} 1>> "{}" 2>&1 && '.format(interpret, script, inputs, params, outputs, log)
    cmd = re.sub(r'&&\s*$', '', cmd)
    shell(cmd)



# Config variables from the input data
if INFILE_DAT and INFILE_DAT != "":
    INDATA,INDATA_EXPTO,INDATA_NAMES = load_indata(INFILE_DAT)
