import os

# Load global variables need for workflow
TMP_OUTDIR         = config['tmpdir']
RST_OUTDIR         = config['rstdir']
LOG_OUTDIR         = config['logdir']

# ------------- #
# Local Methods #
# ------------- #
def load_inputs(config):
    '''
    Load the outputs of config file
    '''
    # apply the rule executors to rule (method)
    for cmd in config['commands']:
        for rules in cmd['rules']:
            for ir in range(len(rules)):
                crule = rules[ir]
                for f,files in crule['outfiles'].items():
                    for file in files.split(";"):
                        yield expand(["{file}"], file=file)

def load_rules(config):
    '''
    Return the list of rules from the config file
    '''
    o = []
    # apply the rule executors to rule (method)
    for cmd in config['commands']:
        for rules in cmd['rules']:
            for ir in range(len(rules)):
                crule = rules[ir]
                o.append( crule )
    return o

def run_rule(input, output, log, params, wildcards):
    '''
    Execute the command line for each rule
    '''
    cr = params['index']
    logfile = params['log']
    crule = CRULES[cr]
    # cmd = "{} >> \"{}\" 2>&1".format(crule['cline'], logfile)
    cmd = "{}".format(crule['cline'])
    # cmd = "touch "
    # for out in output:
    #     cmd += " \"{}\" ".format(out)
    # print( "CMD> "+str(cr)+">"+crule['name'])
    # print( "I> ",input )
    # print( "O> ",output )
    # print( "C> "+cmd)
    shell( cmd )

# extract the rules
CRULES = load_rules(config)

# prepare log space
os.makedirs(LOG_OUTDIR, exist_ok=True)

# ------------------ #
# Executors of rules #
# ------------------ #
for cr, crule in enumerate(CRULES):
    rule:
        '''
        Execute every rule
        '''
        # threads: int(config['ncpu'])
        message: "{}: executing!!!".format(crule["name"])
        params:
            index=cr,
            log=LOG_OUTDIR+"/"+crule["name"]+".log"
        input:
            "{file}".format(file=file) for i,files in crule["infiles"].items() for file in files.split(";")
        output:
            "{file}".format(file=file) for i,files in crule["outfiles"].items() for file in files.split(";")
        run:
            run_rule(input, output, log, params, wildcards)