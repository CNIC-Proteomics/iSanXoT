# ------------------ #
# Executors of rules #
# ------------------ #
def run_rule(input, output, log, params,wildcards):
    def get_dirname(files):
        if files:
            f = list(files)[0]
            d = os.path.dirname(f)
        else:
            d = ''
        return d
    # extract the rule configuration from the name and the outputs
    r = extract_method(params["name"], output)
    # get the dirname from the list of files
    indir  = get_dirname(input)
    outdir  = get_dirname(output)
    # create params for method
    optrep,optparam = create_ad_hoc_params(r["name"], wildcards)
    # execute command line
    execute_methods(r["methods"], indir, outdir, log, optrep=optrep, optparam=optparam)


rul = [r for r in CONF_RULES]
for r in rul:

    # rule that works on the directories:
    # from "SOMEWHERE INDIR" => OUTDIR
    if r["enabled"] and r["executor"] == "indir_to_outdir":
        rule:
            '''
            Execute rules with one input directory
            '''
            threads: r["threads"]
            message: "{}: executing with {} threads".format(r["name"], "{threads}")
            params:
                name=r["name"]
            output:
                OUTDIR+"/"+fname for fname in r["outputs"]
            log:
                LOG_OUTDIR+"/"+r["name"]+".log"
            run:
                run_rule(input, output, log, params,wildcards)


    # rule that works on the directories:
    # from "SOMEWHERE INDIR" => TMPDIR
    if r["enabled"] and r["executor"] == "indir_to_tmpdir":
        rule:
            '''
            Execute rules with one input directory
            '''
            threads: r["threads"]
            message: "{}: executing with {} threads".format(r["name"], "{threads}")
            params:
                name=r["name"]
            output:
                "{indir}/{exp}/{fname}".format(indir=TMP_OUTDIR, exp=e, fname=f) for e in INDATA for f in r["outputs"]
            log:
                LOG_OUTDIR+"/"+r["name"]+".log"
            run:
                run_rule(input, output, log, params,wildcards)


    # rule that works on the directories:
    # from "SOMEWHERE INDIR" => RSTDIR
    if r["enabled"] and r["executor"] == "indir_to_rstdir":
        rule:
            '''
            Execute rules with one input directory
            '''
            threads: r["threads"]
            message: "{}: executing with {} threads".format(r["name"], "{threads}")
            params:
                name=r["name"]
            output:
                RST_OUTDIR+"/"+fname for fname in r["outputs"]
            log:
                LOG_OUTDIR+"/"+r["name"]+".log"
            run:
                run_rule(input, output, log, params,wildcards)


    # rule that works on the directories:
    # from "SOMEWHERE INFILES" => OUTDIR
    if r["enabled"] and r["executor"] == "infiles_to_outdir":
        rule:
            '''
            Rules for the cases: accepts input and output files without the modification of directories
            '''
            threads: r["threads"]
            message: "{}: executing with {} threads".format(r["name"], "{threads}")
            params:
                name=r["name"]
            input:
                replace_params(r["indir"])+"/"+fname for fname in r["inputs"]
            output:
                OUTDIR+"/"+fname for fname in r["outputs"]
            log:
                LOG_OUTDIR+"/"+r["name"]+".log"
            run:
                run_rule(input, output, log, params,wildcards)


    # rule that works on the directories:
    # from OUTDIR => OUTDIR
    if r["enabled"] and r["executor"] == "on_outdir":
        rule:
            '''
            Execute rules that work over the experiment directory
            '''
            threads: r["threads"]
            message: "{}: executing with {} threads".format(r["name"], "{threads}")
            params:
                name=r["name"]
            input:
                OUTDIR+"/"+fname for fname in r["inputs"]
            output:
                OUTDIR+"/"+fname for fname in r["outputs"]
            log:
                LOG_OUTDIR+"/"+r["name"]+".log"
            run:
                run_rule(input, output, log, params,wildcards)


    # rule that works on the directories:
    # from TMPDIR => TMPDIR
    if r["enabled"] and r["executor"] == "on_tmpdir":
        rule:
            '''
            Execute rules that work over the experiment directory
            '''
            threads: r["threads"]
            message: "{}: executing with {} threads".format(r["name"], "{threads}")
            params:
                name=r["name"]
            input:
                TMP_OUTDIR+"/{exp}/{name}/"+fname for fname in r["inputs"]
            output:
                TMP_OUTDIR+"/{exp}/{name}/"+fname for fname in r["outputs"]
            log:
                LOG_OUTDIR+"/"+r["name"]+"_{exp}_{name}.log"
            run:
                run_rule(input, output, log, params,wildcards)


    # rule that works on the directories:
    # from RSTDIR => RSTDIR
    if r["enabled"] and r["executor"] == "on_rstdir":
        rule:
            '''
            Execute rules that work over the experiment directory
            '''
            threads: r["threads"]
            message: "{}: executing with {} threads".format(r["name"], "{threads}")
            params:
                name=r["name"]
            input:
                RST_OUTDIR+"/"+fname for fname in r["inputs"]
            output:
                RST_OUTDIR+"/"+fname for fname in r["outputs"]
            log:
                LOG_OUTDIR+"/"+r["name"]+".log"
            run:
                run_rule(input, output, log, params,wildcards)


    # rule that works on the directories:
    # from TMPDIR => TMPDIR
    if r["enabled"] and r["executor"] == "tmpdir_to_tmpdir":
        rule:
            '''
            Execute rules that work over the experiment directory
            '''
            threads: r["threads"]
            message: "{}: executing with {} threads".format(r["name"], "{threads}")
            params:
                name=r["name"]
            input:
                TMP_OUTDIR+"/{exp}/"+fname for fname in r["inputs"]
            output:
                # "{indir}/{exp}/{name}/{fname}".format(indir=TMP_OUTDIR, exp=e, name=n, fname=f) for e in INDATA for n in INDATA[e]["names"] for f in r["outputs"]
                TMP_OUTDIR+"/{exp}/{name}/"+fname for fname in r["outputs"]
            log:
                LOG_OUTDIR+"/"+r["name"]+"_{exp}_{name}.log"
            run:
                run_rule(input, output, log, params,wildcards)


    # rule that works on the directories:
    # from OUTDIR => TMPDIR
    if r["enabled"] and r["executor"] == "outdir_to_tmpdir":
        rule:
            '''
            Execute the rule for most of scripts of SanXoT
            '''
            threads: r["threads"]
            message: "{}: executing with {} threads".format(r["name"], "{threads}")
            params:
                name=r["name"]
            input:
                OUTDIR+"/"+fname for fname in r["inputs"]
            output:
                TMP_OUTDIR+"/{exp}/{name}/"+fname for fname in r["outputs"]
            log:
                LOG_OUTDIR+"/"+r["name"]+"_{exp}_{name}.log"
            run:
                run_rule(input, output, log, params,wildcards)


    # rule that works on the directories:
    # from OUTDIR => RSTDIR
    if r["enabled"] and r["executor"] == "outdir_to_rstdir":
        rule:
            '''
            Execute the rule for most of scripts of SanXoT
            '''
            threads: r["threads"]
            message: "{}: executing with {} threads".format(r["name"], "{threads}")
            params:
                name=r["name"]
            input:
                OUTDIR+"/"+fname for fname in r["inputs"]
            output:
                RST_OUTDIR+"/"+fname for fname in r["outputs"]
            log:
                LOG_OUTDIR+"/"+r["name"]+".log"
            run:
                run_rule(input, output, log, params,wildcards)

    # rule that works on the directories:
    # from TMPDIR => RSTDIR
    if r["enabled"] and r["executor"] == "tmpdir_to_rstdir":
        rule:
            '''
            Execute the rule for most of scripts of SanXoT
            '''
            threads: r["threads"]
            message: "{}: executing with {} threads".format(r["name"], "{threads}")
            params:
                name=r["name"]
            input:
                "{indir}/{exp}/{name}/{fname}".format(indir=TMP_OUTDIR, exp=e, name=n, fname=f) for e in INDATA for n in INDATA[e]["names"] for f in r["inputs"]
            output:
                RST_OUTDIR+"/"+fname for fname in r["outputs"]
            log:
                LOG_OUTDIR+"/"+r["name"]+".log"
            run:
                run_rule(input, output, log, params,wildcards)
