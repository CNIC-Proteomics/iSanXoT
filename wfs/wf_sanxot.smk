# include the main functions and the global variables
include: "inc/main.smk"

# include the functions for workflow methods
include: "inc/sanxot.smk"

# include the rules executors
include: "inc/rules.smk"

# default target rule
rule all:
    '''
    Config the output files
    '''
    input:
        setup_outfiles_from_indata()
