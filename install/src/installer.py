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



####################
# Global variables #
####################

# get input arguments
requirement_new_file = "{}/{}".format(sys.argv[1],'requirements.txt')
requirement_loc_file = "{}/{}".format(sys.argv[2],'requirements.txt')

dirname = os.path.dirname(__file__)
lib_home = os.path.dirname(requirement_loc_file)
python_exec = sys.executable
node_url = 'https://nodejs.org/dist/v10.14.2/node-v10.14.2-win-x64.zip'
node_home = f"{lib_home}/node"
tmpdir = f"{lib_home}/tmp"




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

def install_pkg_manager_pip():
    exec_command(f'{python_exec} {dirname}/get-pip.py --no-warn-script-location')

def install_pkg_manager_npm(manager):
    try:
        # local library
        import core
        # print("-- create builder")
        c = core.builder(tmpdir)
        # print("-- download files: "+node_url+" > "+tmpdir)
        file = c.download_url(node_url, outdir=tmpdir)
        # print("-- unzip files: "+file+" > "+tmpdir)
        c.unzip_file(file,  tmpdir)
        # print("-- move files to node_home")
        c.move_files(tmpdir, node_home)
        # print("-- remove tmpdir")
        c.remove_dir(tmpdir)
        # if everything was fine
        return True
    except Exception as exc:
        sys.exit(f"ERROR!! installing manager: {manager}\n{exc}")

def install_pkg_manager(manager):
    try:
        # handle manager file
        manager = "{}/{}".format(lib_home, manager.replace('$MANAGER=',''))
        # check if package manager is installed
        if not (os.path.isfile(manager) or os.path.isfile(manager+'.exe')):
            if 'pip' in manager:
                print(f"-- install package manager {manager}")
                install_pkg_manager_pip()
            elif 'npm' in manager:
                print(f"-- install package manager {manager}")
                install_pkg_manager_npm(manager)
        # if everything was fine
        return True
    except Exception as exc:
        sys.exit(f"ERROR!! installing manager: {manager}\n{exc}")
                
def install_package(manager, iparams, pkg):
    try:
        # handle manager file
        manager = "{}/{}".format(lib_home, manager.replace('$MANAGER=',''))
        # create command
        cmd = f'{manager} {iparams} {pkg}'
        print(f'-- exec: {cmd}')
        crun = subprocess.call(cmd, shell=True)
        # if everything was fine
        if crun == 0:
            return True
        else:
            sys.exit(f"ERROR!! installing the package: {cmd}")
    except Exception as exc:
        sys.exit(f"ERROR!! installing the package: {cmd}\n{exc}")

def create_report_requirements(file):
    '''
    Create dictionary with the manager and its required packages
    '''
    report = {}
    if os.path.isfile(file):
        f = open(file)
        lines = f.read().splitlines()
        for line in lines:
            line = line.rstrip()
            if line.startswith('$MANAGER='): # package manager line
                manager = line
                report[manager] = {}
            elif not line.startswith('#'): # package line
                s = re.split(r'\t+', line)
                iparams = s[0]
                pkg = s[1] if len(s) > 1 else ''
                report[manager][pkg] = iparams
        f.close()
    return report


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

    # new installation of libraries
    if not req_loc:

        # look through the new requirements
        requirement_cont = '' # string with the new requirments
        for manager,packages in req_new.items():
            # install package manager
            iok = install_pkg_manager(manager)
            requirement_cont += f"{manager}\n"
            # install package's
            for pkg,iparams in packages.items():
                write_ok = install_package(manager, iparams, pkg)
                # write into local requirement file
                if write_ok:
                    requirement_cont += f"{iparams}\t{pkg}\n"

        # write into local requirement file
        if requirement_cont != '':
            with open(requirement_loc_file, "a") as file:
                file.write(requirement_cont)
    

    # upgrade the library
    else:
        
        # look through the new requirements
        requirement_cont = '' # string with the new requirments
        for manager,packages in req_new.items():
            # check if the new package manager is already installed
            if not manager in req_loc:
                # install package manager
                iok = install_pkg_manager(manager)
                requirement_cont += f"{manager}\n"
            # install package's
            for pkg,iparams in packages.items():
                # check if the new package is already installed
                if not manager in req_loc or not pkg in req_loc[manager]:
                    write_ok = install_package(manager, iparams, pkg)
                    # write into local requirement file
                    if write_ok:
                        requirement_cont += f"{iparams}\t{pkg}\n"

        # write into local requirement file
        if requirement_cont != '':
            with open(requirement_loc_file, "a") as file:
                file.write(requirement_cont)


# TODO!!! ADD THE EXECUTION OF THIS PYTHON SCRIPT!!
# REM :: download databases ----------------------
# REM ECHO **
# REM ECHO **
# REM ECHO ** download databases
# REM SET  DB_URL=https://www.cnic.es/nextcloud/index.php/s/Pm6AJ65XQjeBM5G/download
# REM CMD /C " "%PYTHON3x_HOME%/tools/python" "%SRC_HOME%/src/download_dbs.py" "%DB_URL%" "%SRC_HOME%/../dbs" "

     
    
if __name__ == '__main__':
    main()