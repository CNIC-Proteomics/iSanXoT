# ------------------------- #
# Functions for the methods #
# ------------------------- #
def create_ad_hoc_params(method, wildcards):
    rep,param = {},''
    if method == "aljamia":
        if wildcards and wildcards.exp and wildcards.name:
            l = INDATA[wildcards.exp]["names"][wildcards.name]["ratio_num"]
            c = INDATA[wildcards.exp]["names"][wildcards.name]["ratio_den"]
            lbl_tag = str(l).replace(",","-")+"_Mean" if ',' in l else l
            lbl_ctr = str(c).replace(",","-")+"_Mean" if ',' in c else c
            rep["--TAG--"]        = lbl_tag
            rep["--CONTROLTAG--"] = lbl_ctr

    elif method == "scan2peptide":
        if wildcards and wildcards.exp and wildcards.name:
            lbl_fdr = " -f {} ".format(INDATA[wildcards.exp]["names"][wildcards.name]["s>p FDR"])
            try:
                if type(INDATA[wildcards.exp]["names"][wildcards.name]["s>p Var"]) is bool:
                    lbl_var = " -V s2p_infoFile.txt "
                else:
                    f = float(INDATA[wildcards.exp]["names"][wildcards.name]["s>p Var"])
                    lbl_var = " -v {} ".format(str(f))
            except:
                lbl_var = " -V s2p_infoFile.txt "
            rep["--PARAMS__FDR--"]        = lbl_fdr
            rep["--PARAMS__VARIANCE--"]   = lbl_var
        
    elif method == "scan2peptide_ptm":
        if wildcards and wildcards.exp and wildcards.name:
            lbl_fdr = " -f {} ".format(INDATA[wildcards.exp]["names"][wildcards.name]["s>p FDR"])
            try:
                if type(INDATA[wildcards.exp]["names"][wildcards.name]["s>p Var"]) is bool:
                    lbl_var = " -V s2p_noptm_infoFile.txt "
                else:
                    f = float(INDATA[wildcards.exp]["names"][wildcards.name]["s>p Var"])
                    lbl_var = " -v {} ".format(str(f))
            except:
                lbl_var = " -V s2p_noptm_infoFile.txt "
            rep["--PARAMS__FDR--"]        = lbl_fdr
            rep["--PARAMS__VARIANCE--"]   = lbl_var

    elif method == "peptide2protein":
        if wildcards and wildcards.exp and wildcards.name:
            lbl_fdr = " -f {} ".format(INDATA[wildcards.exp]["names"][wildcards.name]["p>q FDR"])
            try:
                if type(INDATA[wildcards.exp]["names"][wildcards.name]["p>q Var"]) is bool:
                    lbl_var = " -V p2q_infoFile.txt "
                else:
                    f = float(INDATA[wildcards.exp]["names"][wildcards.name]["p>q Var"])
                    lbl_var = " -v {} ".format(str(f))
            except:
                lbl_var = " -V p2q_infoFile.txt "
            rep["--PARAMS__FDR--"]        = lbl_fdr
            rep["--PARAMS__VARIANCE--"]   = lbl_var

    elif method == "protein2category":
        if wildcards and wildcards.exp and wildcards.name:
            lbl_fdr = " -f {} ".format(INDATA[wildcards.exp]["names"][wildcards.name]["q>c FDR"])
            try:
                if type(INDATA[wildcards.exp]["names"][wildcards.name]["q>c Var"]) is bool:
                    lbl_var = " -V q2c_infoFile.txt "
                else:
                    f = float(INDATA[wildcards.exp]["names"][wildcards.name]["q>c Var"])
                    lbl_var = " -v {} ".format(str(f))
            except:
                lbl_var = " -V q2c_infoFile.txt "
            rep["--PARAMS__FDR--"]        = lbl_fdr
            rep["--PARAMS__VARIANCE--"]   = lbl_var
    
    return rep,param