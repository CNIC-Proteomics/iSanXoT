# ---------------- #
# Pre-SanXoT rules #
# ---------------- #

rule_name = "converter"
r = next((r for r in CONF_RULES if r["name"] == rule_name), None)
if r and r["enabled"]:
    rule converter:
        '''
        Convert the result from MaxQuant (txt/evidences) to ID-q file: label-free
        '''
        threads: r["threads"]
        message: "Executing '{rule}' with {threads} threads"
        input:
            # expand(["{indir}/{fname}"], indir=replace_params(r["indir"]), fname=r["inputs"])
            replace_params(r["indir"])+"/"+fname for fname in r["inputs"]
        output:
            replace_params(r["outdir"])+"/"+fname for fname in r["outputs"]
        log:
            LOG_OUTDIR+"/"+rule_name+".log"
        run:
            r = next((r for r in CONF_RULES if r["name"] == rule), None)
            indir  = replace_params(r["indir"])
            outdir = replace_params(r["outdir"])
            execute_methods(r["methods"], indir, outdir, log)

rule_name = "pre_sanxot"
r = next((r for r in CONF_RULES if r["name"] == rule_name), None)
if r and r["enabled"]:
    rule pre_sanxot:
        '''
        Calculate the ratios
        '''
        threads: r["threads"]
        message: "Executing '{rule}' with {threads} threads"
        input:
            # expand(["{indir}/{fname}"], indir=replace_params(r["indir"]), fname=r["inputs"])
            replace_params(r["indir"])+"/"+fname for fname in r["inputs"]
        output:
            replace_params(r["outdir"])+"/"+fname for fname in r["outputs"]
        log:
            LOG_OUTDIR+"/"+rule_name+".log"
        run:
            r = next((r for r in CONF_RULES if r["name"] == rule), None)
            indir  = replace_params(r["indir"])
            outdir = replace_params(r["outdir"])
            execute_methods(r["methods"], indir, outdir, log)

