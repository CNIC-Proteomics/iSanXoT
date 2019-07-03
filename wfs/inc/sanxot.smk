# ------------ #
# SanXoT rules #
# ------------ #

rule_name = "aljamia"
r = next((r for r in CONF_RULES if r["name"] == rule_name), None)
if r and r["enabled"]:
    rule aljamia:
        '''
        Convert the result from MaxQuant (txt/evidences) to ID-q file: label-free
        '''
        threads: r["threads"]
        message: "Executing '{rule}' with {threads} threads"
        input:
            expand(["{indir}/{fname}"], indir=replace_params(r["indir"]), fname=r["inputs"])
        output:
            replace_params(r["outdir"])+"/{exp}/{name}/"+fname for fname in r["outputs"]
        log:
            LOG_OUTDIR+"/"+rule_name+"_{exp}_{name}.log"
        run:
            r = next((r for r in CONF_RULES if r["name"] == rule), None)
            indir  = replace_params(r["indir"])
            outdir = replace_params(r["outdir"])+"/"+wildcards.exp+"/"+wildcards.name
            optrep = {
                "labeltags":   INDATA[wildcards.exp]["names"][wildcards.name]["ratio_num"],
                "controltags": INDATA[wildcards.exp]["names"][wildcards.name]["ratio_den"]
            }
            execute_methods(r["methods"], indir, outdir, log, optrep=optrep)

rule_name = "aljamia_cat"
r = next((r for r in CONF_RULES if r["name"] == rule_name), None)
if r and r["enabled"]:
    rule aljamia_cat:
        '''
        Concatenate aljamia outputs
        '''
        threads: r["threads"]
        message: "Executing '{rule}' with {threads} threads"
        input:
            replace_params(r["indir"])+"/{exp}/{name}/"+fname for fname in r["inputs"]
        output:
            replace_params(r["outdir"])+"/{exp}/{name}/"+fname for fname in r["outputs"]
        log:
            LOG_OUTDIR+"/"+rule_name+"_{exp}_{name}.log"
        run:
            r = next((r for r in CONF_RULES if r["name"] == rule), None)
            indir  = replace_params(r["indir"])+"/"+wildcards.exp+"/"+wildcards.name
            outdir = replace_params(r["outdir"])+"/"+wildcards.exp+"/"+wildcards.name
            execute_methods(r["methods"], indir, outdir, log)

rule_name = "scan2peptide"
r = next((r for r in CONF_RULES if r["name"] == rule_name), None)
if r and r["enabled"]:
    rule scan2peptide:
        '''
        SanXoT method: scan to peptide
        '''
        threads: r["threads"]
        message: "Executing '{rule}' with {threads} threads"
        input:
            replace_params(r["indir"])+"/{exp}/{name}/"+fname for fname in r["inputs"]
        output:
            replace_params(r["outdir"])+"/{exp}/{name}/"+fname for fname in r["outputs"]
        log:
            LOG_OUTDIR+"/"+rule_name+"_{exp}_{name}.log"
        run:
            r = next((r for r in CONF_RULES if r["name"] == rule), None)
            indir  = replace_params(r["indir"])+"/"+wildcards.exp+"/"+wildcards.name
            outdir = replace_params(r["outdir"])+"/"+wildcards.exp+"/"+wildcards.name
            # tmpdir = replace_params(r["outdir"])+"/"+wildcards.exp+"/"+wildcards.name+"/tmp"
            tmpdir = None
            execute_methods(r["methods"], indir, outdir, log, tmpdir=tmpdir)

rule_name = "peptide2protein"
r = next((r for r in CONF_RULES if r["name"] == rule_name), None)
if r and r["enabled"]:
    rule peptide2protein:
        '''
        SanXoT method: peptide to protein
        '''
        threads: r["threads"]
        message: "Executing '{rule}' with {threads} threads"
        input:
            replace_params(r["indir"])+"/{exp}/{name}/"+fname for fname in r["inputs"]
        output:
            replace_params(r["outdir"])+"/{exp}/{name}/"+fname for fname in r["outputs"]
        log:
            LOG_OUTDIR+"/"+rule_name+"_{exp}_{name}.log"
        run:
            r = next((r for r in CONF_RULES if r["name"] == rule), None)
            indir  = replace_params(r["indir"])+"/"+wildcards.exp+"/"+wildcards.name
            outdir = replace_params(r["outdir"])+"/"+wildcards.exp+"/"+wildcards.name
            execute_methods(r["methods"], indir, outdir, log)

rule_name = "protein2category"
r = next((r for r in CONF_RULES if r["name"] == rule_name), None)
if r and r["enabled"]:
    rule protein2category:
        '''
        SanXoT method: protein to category
        '''
        threads: r["threads"]
        message: "Executing '{rule}' with {threads} threads"
        input:
            replace_params(r["indir"])+"/{exp}/{name}/"+fname for fname in r["inputs"]
        output:
            replace_params(r["outdir"])+"/{exp}/{name}/"+fname for fname in r["outputs"]
        log:
            LOG_OUTDIR+"/"+rule_name+"_{exp}_{name}.log"
        run:
            r = next((r for r in CONF_RULES if r["name"] == rule), None)
            indir  = replace_params(r["indir"])+"/"+wildcards.exp+"/"+wildcards.name
            outdir = replace_params(r["outdir"])+"/"+wildcards.exp+"/"+wildcards.name
            execute_methods(r["methods"], indir, outdir, log)

rule_name = "peptide2all"
r = next((r for r in CONF_RULES if r["name"] == rule_name), None)
if r and r["enabled"]:
    rule peptide2all:
        '''
        SanXoT method: peptide to all
        '''
        threads: r["threads"]
        message: "Executing '{rule}' with {threads} threads"
        input:
            replace_params(r["indir"])+"/{exp}/{name}/"+fname for fname in r["inputs"]
        output:
            replace_params(r["outdir"])+"/{exp}/{name}/"+fname for fname in r["outputs"]
        log:
            LOG_OUTDIR+"/"+rule_name+"_{exp}_{name}.log"
        run:
            r = next((r for r in CONF_RULES if r["name"] == rule), None)
            indir  = replace_params(r["indir"])+"/"+wildcards.exp+"/"+wildcards.name
            outdir = replace_params(r["outdir"])+"/"+wildcards.exp+"/"+wildcards.name
            execute_methods(r["methods"], indir, outdir, log)

rule_name = "protein2all"
r = next((r for r in CONF_RULES if r["name"] == rule_name), None)
if r and r["enabled"]:
    rule protein2all:
        '''
        SanXoT method: protein to all
        '''
        threads: r["threads"]
        message: "Executing '{rule}' with {threads} threads"
        input:
            replace_params(r["indir"])+"/{exp}/{name}/"+fname for fname in r["inputs"]
        output:
            replace_params(r["outdir"])+"/{exp}/{name}/"+fname for fname in r["outputs"]
        log:
            LOG_OUTDIR+"/"+rule_name+"_{exp}_{name}.log"
        run:
            r = next((r for r in CONF_RULES if r["name"] == rule), None)
            indir  = replace_params(r["indir"])+"/"+wildcards.exp+"/"+wildcards.name
            outdir = replace_params(r["outdir"])+"/"+wildcards.exp+"/"+wildcards.name
            execute_methods(r["methods"], indir, outdir, log)

rule_name = "category2all"
r = next((r for r in CONF_RULES if r["name"] == rule_name), None)
if r and r["enabled"]:
    rule category2all:
        '''
        SanXoT method: category to all
        '''
        threads: r["threads"]
        message: "Executing '{rule}' with {threads} threads"
        input:
            replace_params(r["indir"])+"/{exp}/{name}/"+fname for fname in r["inputs"]
        output:
            replace_params(r["outdir"])+"/{exp}/{name}/"+fname for fname in r["outputs"]
        log:
            LOG_OUTDIR+"/"+rule_name+"_{exp}_{name}.log"
        run:
            r = next((r for r in CONF_RULES if r["name"] == rule), None)
            indir  = replace_params(r["indir"])+"/"+wildcards.exp+"/"+wildcards.name
            outdir = replace_params(r["outdir"])+"/"+wildcards.exp+"/"+wildcards.name
            execute_methods(r["methods"], indir, outdir, log)

rule_name = "collector"
r = next((r for r in CONF_RULES if r["name"] == rule_name), None)
if r and r["enabled"]:
    rule collector:
        '''
        Merge the results of SanXoT nodes
        '''
        threads: r["threads"]
        message: "Executing '{rule}' with {threads} threads"
        input:
            "{indir}/{exp}/{name}/{fname}".format(indir=replace_params(r["indir"]), exp=e, name=n, fname=f) for e in INDATA for n in INDATA[e]["names"] for f in r["inputs"]
        output:
            "{outdir}/"+fname for fname in r["outputs"]
        run:
            r = next((r for r in CONF_RULES if r["name"] == rule), None)
            indir  = replace_params(r["indir"])
            outdir = replace_params(r["outdir"])
            log = "{}/{}.log".format(LOG_OUTDIR,rule) # variable log file
            execute_methods(r["methods"], indir, outdir, log)

rule_name = "sanxot"
rul = [r for r in CONF_RULES if r["name"] == rule_name]
for r in rul:
    if r and r["enabled"]:
        rule:
            '''
            Execute SanXoT methods within 'flexilble' output directory (the sub-directory is in the output file name)
            '''
            threads: r["threads"]
            message: "Executing '{rule}' with {threads} threads"
            input:
                replace_params(r["indir"])+"/"+fname for fname in r["inputs"]
            output:
                replace_params(r["outdir"])+"/"+fname for fname in r["outputs"]
            run:
                r = extract_method("sanxot", output) # extract the rule configuration from the outputs
                indir  = replace_params(r["indir"])
                outdir = replace_params(r["outdir"])                
                log = "{}/{}.{}.log".format(LOG_OUTDIR,"sanxot",rule) # variable log file
                execute_methods(r["methods"], indir, outdir, log)
