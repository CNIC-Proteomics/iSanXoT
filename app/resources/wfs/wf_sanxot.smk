# include the main functions and the global variables
# include the rules executors
include: "inc/main.smk"

# default target rule
rule all:
    '''
    Load the config file
    '''
    input:
        load_inputs(config)
