# include the main functions and the global variables
include: "inc/main.smk"

# include the rules for the Pre-SanXoT section
include: "inc/pre_sanxot.smk"

# include the rules for the SanXoT section
include: "inc/sanxot.smk"

# default target rule
rule all:
    '''
    Config the output files
    '''
    input:
        setup_outfiles_from_indata()
