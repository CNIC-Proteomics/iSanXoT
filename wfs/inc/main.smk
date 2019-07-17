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

# Give an excise number of cores... It will be replaced by the given cores as parameter
CORES_EXCISE =  40

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
    # scan every rule: inputs and outputs
    for rule in CONF_RULES:
        if rule["enabled"]:
            inputs  = rule["inputs"]
            outputs = rule["outputs"]
            dynamic_outdir  = replace_params(rule["outdir"])

            # Convert the result from MaxQuant (txt/evidences) to ID-q file: label-free
            if "converter" == rule["name"]:
                yield expand(["{outdir}/{fname}"], outdir=dynamic_outdir, fname=outputs)

            # # phantom output for the pRatio rules
            # if "pratio" == rule["name"]:
            #     # yield "{outdir}/.pratio".format(outdir=TMP_OUTDIR)
            #     yield expand(["{outdir}/{fname}"], outdir=dynamic_outdir, fname=outputs)

            # Output for the pre_sanxot: calculation of ratios (Xs, Vs,...)
            if "pre_sanxot" == rule["name"]:
                yield expand(["{outdir}/{fname}"], outdir=dynamic_outdir, fname=outputs)

            # apply the corrected methods for the experiments info
            # output files created by sanxot workflow
            for exp, indat in INDATA.items():
                for name in indat["names"]:
                    # SanXoT rules
                    if "aljamia" == rule["name"]:
                        yield expand(["{outdir}/{exp}/{name}/{fname}"], outdir=dynamic_outdir, exp=exp, name=name, fname=outputs)
                    if "aljamia_cat" == rule["name"]:
                        yield expand(["{outdir}/{exp}/{name}/{fname}"], outdir=dynamic_outdir, exp=exp, name=name, fname=outputs)
                    if "scan2peptide" == rule["name"]:
                        yield expand(["{outdir}/{exp}/{name}/{fname}"], outdir=dynamic_outdir, exp=exp, name=name, fname=outputs)
                    if "peptide2protein" == rule["name"]:
                        yield expand(["{outdir}/{exp}/{name}/{fname}"], outdir=dynamic_outdir, exp=exp, name=name, fname=outputs)
                    if "protein2category" == rule["name"]:
                        yield expand(["{outdir}/{exp}/{name}/{fname}"], outdir=dynamic_outdir, exp=exp, name=name, fname=outputs)
                    if "peptide2all" == rule["name"]:
                        yield expand(["{outdir}/{exp}/{name}/{fname}"], outdir=dynamic_outdir, exp=exp, name=name, fname=outputs)
                    if "protein2all" == rule["name"]:
                        yield expand(["{outdir}/{exp}/{name}/{fname}"], outdir=dynamic_outdir, exp=exp, name=name, fname=outputs)
                    if "category2all" == rule["name"]:
                        yield expand(["{outdir}/{exp}/{name}/{fname}"], outdir=dynamic_outdir, exp=exp, name=name, fname=outputs)
            
            # we merge the multiple results files from compilator
            if "compilator" == rule["name"]:
                yield expand(["{outdir}/{fname}"], outdir=dynamic_outdir, fname=outputs)

            # SanXoT rule that will operate within 'flexilble' output directory (the sub-directory is in the output file name)
            if "sanxot" == rule["name"]:
                yield expand(["{outdir}/{fname}"], outdir=dynamic_outdir, fname=outputs)


def replace_params(in_param, rep=None, indir=None, tmpdir=None):
    '''
    Replace the variable values for the parameters
    '''
    # init 
    REPLACE_CONST = {}
    # add more replacements
    if indir:
        REPLACE_CONST["--WF__EXPTO__DIR--"] = indir
    if tmpdir:
        REPLACE_CONST["--WF__EXPTO__TMPDIR--"] = tmpdir
    # add experimets
    REPLACE_CONST["--EXPTS--"] = ",".join(INDATA_EXPTO)
    # add more replacements for control labels and tag labesl
    if rep and "controltags" in rep:
        r = rep["controltags"]
        s = str(r).replace(",","-")+"_Mean" if ',' in r else r
        REPLACE_CONST["--CONTROLTAG--"] = s
    if rep and "labeltags" in rep:
        r = rep["labeltags"]
        s = str(r).replace(",","-")+"_Mean" if ',' in r else r
        REPLACE_CONST["--TAG--"] = s
    # replace action if apply
    if REPLACE_CONST:
        optrep = dict((re.escape(k), v) for k, v in REPLACE_CONST.items())
        pattern = re.compile("|".join(optrep.keys()))
        output = pattern.sub( lambda m: optrep[re.escape(m.group(0))], in_param )
    else:
        output = in_param
    return output


def extract_method_parameters(method, indir, outdir, optrep=None, tmpdir=None):
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
        for key,value in method["params"].items():
            if isinstance(value, str):
                if value != "":
                    params += ' '+key+' "'+replace_params(value, rep=optrep, indir=indir, tmpdir=tmpdir)+'" '
                else: #empty parameter
                    params += ' '+key+' '
    return inputs,params,outputs


def extract_method(rule_name, outputs):
    fnames = [os.path.basename(o) for o in outputs]
    r = next((r for r in CONF_RULES if r["name"] == rule_name and any(e in fnames for e in r["outputs"])), None)
    return r


def execute_methods(methods, indir, outdir, log, optrep=None, tmpdir=None):
    cmd  = ''
    # prepare temporal workspace
    if tmpdir:
        os.makedirs(tmpdir, exist_ok=True)
    # create command line for the whole methods
    for method in methods:
        interpret = ISANXOT_PYTHON3x_HOME+'/tools/python'
        script    = ISANXOT_SRC_HOME+'/src/'+method["script"]
        inputs, params, outputs = extract_method_parameters(method, indir, outdir, optrep=optrep, tmpdir=tmpdir)
        cmd  += '"{}" "{}" {} {} {} 1>> "{}" 2>&1 && '.format(interpret, script, inputs, params, outputs, log)
    cmd = re.sub(r'&&\s*$', '', cmd)
    shell(cmd)



# Config variables from the input data
INDATA,INDATA_EXPTO,INDATA_NAMES = load_indata(INFILE_DAT)
