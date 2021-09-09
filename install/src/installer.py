# -*- coding: utf-8 -*-
#!/usr/bin/python

# Module metadata variables
__author__ = ["Jose Rodriguez"]
__credits__ = ["Jose Rodriguez", "Jesus Vazquez"]
__license__ = "Creative Commons Attribution-NonCommercial-NoDerivs 4.0 Unported License https://creativecommons.org/licenses/by-nc-nd/4.0/"
__version__ = "1.0.1"
__maintainer__ = "Jose Rodriguez"
__email__ = "jmrodriguezc@cnic.es"
__status__ = "Development"

import sys
import os
import subprocess
import re

# local library
import core


###################
# Local functions #
###################

def exec_command(cmd):
    try:
        print(f'-- exec: {cmd}')
        crun = subprocess.call(cmd, shell=True)
        if crun == 0:
            return True
        else:
            sys.exit(f"ERROR!! executing the command line:: {cmd}")
    except Exception as exc:
        sys.exit(f"ERROR!! executing the command line: {cmd}\n{exc}")

def install_exec_manager(url, odir):
    try:
        # local library
        # import core
        print("-- create builder")
        c = core.builder(tmpdir)
        print("-- download files: "+url+" > "+tmpdir)
        file = c.download_url(url, outdir=tmpdir)
        print("-- unzip files: "+file+" > "+tmpdir)
        c.unzip_file(file,  tmpdir)
        print("-- move files to "+odir)
        c.move_files(tmpdir, odir)
        print("-- remove tmpdir: "+tmpdir)
        c.remove_dir(tmpdir)
        # if everything was fine
        return True
    except Exception as exc:
        sys.exit(f"ERROR!! downloading exec program: {url}\n{exc}")

def install_pkg_manager_pip():
    exec_command(f'"{python_exec}"  "{local_dir}/get-pip.py"  --no-warn-script-location')

def install_pkg_manager(manager):
    try:
        # handle manager file
        manager = "{}/{}".format(lib_home, manager)
        # check if package manager is installed
        if not (os.path.isfile(manager) or os.path.isfile(manager+'.exe')):
            if 'pip' in manager:
                print(f"-- install package manager {manager}")
                install_pkg_manager_pip()            
        # if everything was fine
        return True
    except Exception as exc:
        sys.exit(f"ERROR!! installing manager: {manager}\n{exc}")
                
def install_package(manager, pkg):
    try:
        # handle manager file
        manager = "{}/{}".format(lib_home, manager)
        # create command
        cmd = f'{manager} {pkg}'
        print(f'-- exec: {cmd}')
        crun = subprocess.call(cmd, shell=True)
        # if everything was fine
        if crun == 0:
            return True
        else:
            sys.exit(f"ERROR!! installing the package: {cmd}")
    except Exception as exc:
        sys.exit(f"ERROR!! installing the package: {cmd}\n{exc}")

def download_data(url, odir):
    try:
        print("-- create builder")
        c = core.builder(odir)
        print("-- download files: "+url+" > "+odir)
        file = c.download_url(url, outdir=odir)
        print("-- unzip files: "+file+" > "+odir)
        c.unzip_file(file,  odir)
        f = f"{odir}/download"
        print("-- remove tmp file: "+f)
        c.remove_file(f)
        # if everything was fine
        return True
    except Exception as exc:
        sys.exit(f"ERROR!! downloading databases: {url}\n{exc}")

def create_report_requirements(file):
    '''
    Create dictionary with the manager and its required packages
    '''
    report = {}
    if os.path.isfile(file):
        f = open(file)
        lines = f.read().splitlines()
        key1,key2 = None,None
        for line in lines:
            line = line.rstrip()
            if line.startswith('$'): # compiler manager line
                key1,key2 = None,None
                l = re.findall('^\$([^\=]*)=(.*)', line)
                if (len(l) == 1 and len(l[0]) == 2):
                    key1 = l[0][0]
                    key2 = l[0][1]
                    if not key1 in report:
                        report[key1] = {}
                    report[key1][key2] = []
            elif not line.startswith('#') and key1 is not None and key2 is not None: # package line
                report[key1][key2].append(line)
        f.close()
    return report

def create_str_requirements(req):
    '''
    Create string with the manager and its required packages
    '''
    cont = ''
    for t, r in req.items():
        for manager,packages in r.items():
            cont += f"${t}={manager}\n"
            for pkg in packages:
                cont += f"{pkg}\n"            
    return cont

def install_report(trep, req_new, req_loc):
    # if apply, look through the new requirements
    if trep in req_new:
        for manager,packages in req_new[trep].items():
            # extract the optional parameter
            man = re.split(r'[\s|\t]+', manager)
            if man:
                # get the manager
                manager = man[0]
                # get the name of output dir and create it
                if len(man) > 1:
                    man_dir = f"{lib_home}/{man[1]}"
                    c = core.builder()
                    c.prepare_workspace(man_dir)
                # check if the new package manager is already installed
                if (not trep in req_loc) or (not manager in req_loc[trep]):
                    if trep == 'EXEC':
                        print("-- install executors")
                        iok = install_exec_manager(manager, man_dir)
                    if trep == 'MANAGER':
                        print("** install packages")
                        iok = install_pkg_manager(manager)
                    elif trep == 'DATABASES':
                        print("** install databases")
                        iok = download_data(manager, man_dir)
                    elif trep == 'SAMPLES':
                        print("** install samples")
                        iok = download_data(manager, man_dir)
                    # save modules in the req local
                    if iok:
                        if not trep in req_loc:
                            req_loc[trep] = {}
                        if not manager in req_loc[trep]:
                            req_loc[trep][manager] = []
                # install package's
                for pkg in packages:
                    # check if the new package is already installed
                    if not pkg in req_loc[trep][manager]:
                        iok = install_package(manager, pkg)
                        # save the new module
                        if iok:
                            req_loc[trep][manager].append(pkg)
    return req_loc


#################
# Main function #
#################

def main():
    '''
    Main function
    '''
    # create a dictionary with the package manager and its required packages
    # for the source (new) packages and for destinity (local) packages
    req_new = create_report_requirements(requirement_new_file)
    req_loc = create_report_requirements(requirement_loc_file)
    
    # look through the new requirements for the excutor ---
    req_loc = install_report('EXEC', req_new, req_loc)

    # look through the new requirements for the packages ---
    req_loc = install_report('MANAGER', req_new, req_loc)
            
    # look through the new requirements for the databases ---
    req_loc = install_report('DATABASES', req_new, req_loc)
    
    # look through the new requirements for the samples ---
    req_loc = install_report('SAMPLES', req_new, req_loc)
        
    # write string with the new requiremens into local file ---
    if req_loc:
        cont = create_str_requirements(req_loc)
        if cont != '':
            with open(requirement_loc_file, "w") as file:
                file.write(cont)

     
    
if __name__ == "__main__":
    
    ############################
    # Global variables/methods #
    ############################
    
    # get the executable file and folder
    python_exec = sys.executable
    
    # get local directory
    local_dir = '.' if os.path.dirname(__file__) == '' else os.path.dirname(__file__)
    
    # get input parameters
    if len(sys.argv) == 3:
        requirement_new_file = sys.argv[1]
        lib_home = sys.argv[2]
    # provide only the requierement file, then the lib to install is the executable python
    elif len(sys.argv) == 2:
        requirement_new_file = sys.argv[1]
        lib_home = os.path.dirname(python_exec)
    else:
        sys.exit('''
     Installs the package, modules and executable programas that are described in a requirment file
     Example:
         python installer.py "c:\\tmp\\requirements.txt"      "c:\\python\\"
    
     arguments:
         - requirement file (required)
         - directory where everything will be installed (optional). By default, it is the directory of executable python.
         
     error: the first argument is required
    
    ''')
    
    # get the local requirement file
    requirement_loc_file = "{}/{}".format(lib_home,'requirements.txt')
    
    # create temporal directory
    tmpdir = f"{lib_home}/tmp"
    c = core.builder()
    c.prepare_workspace(tmpdir)
    
    # main function    
    main()
    
    # remove temporal directory
    c.remove_dir(tmpdir)
