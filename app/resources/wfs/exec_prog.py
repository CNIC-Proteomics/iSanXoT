#!/usr/bin/python

# Module metadata variables
__author__ = "Jose Rodriguez"
__credits__ = ["Jose Rodriguez", "Jesus Vazquez"]
__license__ = "Creative Commons Attribution-NonCommercial-NoDerivs 4.0 Unported License https://creativecommons.org/licenses/by-nc-nd/4.0/"
__version__ = "0.0.1"
__maintainer__ = "Jose Rodriguez"
__email__ = "jmrodriguezc@cnic.es"
__status__ = "Development"

#########################
# Import global modules #
#########################
import os
import sys
import yaml
import shlex

###################
# Local functions #
###################
def read_param_file(file):
    params = None
    if os.path.isfile(file):
        try:
            with open(file, 'r') as r:
                arg_str = r.read()
                params = shlex.split(arg_str)
        except Exception as exc:
            sms = "ERROR!! Reading the file with the script params: {}".format(exc)
            raise Exception(sms)
    else:
        sms = "ERROR!! Parameter file does not exit"
        raise Exception(sms)
    return params

#################
# Main function #
#################
def main(argv):
    
    # ------
    # get the input parameters
    if len(argv) > 1:
        script = argv.pop(0)
        params_file = argv.pop()
    else:
        sys.exit("EXEC_PROG_ERROR: providing the parameters correctly")
    
    # ------
    # import script: create a class from the module.
    script_dir = os.path.dirname(script)
    script_name = os.path.splitext(os.path.basename(script))[0]
    sys.path.append(script_dir)
    mod = __import__(script_name, fromlist=[script_dir])
    
    # ------    
    # read the file with the script params
    argv_params = read_param_file(params_file)    

    # ------    
    # extend the previous parameters with the parameters saved in the input file
    argv.extend(argv_params)

    # ------
    # execute the main for the given module
    mod.main(argv)

if __name__ == '__main__':

    main(sys.argv[1:])
    