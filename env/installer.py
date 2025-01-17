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

def print_to_stdout(*a):
 
    # Here a is the array holding the objects
    # passed as the argument of the function
    print(*a, file=sys.stdout, flush=True)
    
def exec_command(cmd):
    try:
        # print_to_stdout(f'-- exec: {cmd}')
        crun = subprocess.call(cmd, shell=True, stdout=sys.stdout, stderr=sys.stderr)
        if crun == 0:
            return True
        else:
            sys.exit(f"ERROR!! executing the command line:: {cmd}")
            return False
    except Exception as exc:
        sys.exit(f"ERROR!! executing the command line: {cmd}\n{exc}")
        return False

def install_exec_manager(url, odir):
    try:
        # import core (local library)
        c = core.builder(tmpdir)
        if url.startswith('http'):
            print_to_stdout("-- download files: "+url+" > "+tmpdir)
            file = c.download_url(url, outdir=tmpdir)
        else:
            file = os.path.join(local_dir,url)
        print_to_stdout("-- unzip files: "+file+" > "+tmpdir)
        c.unzip_file(file,  tmpdir)
        print_to_stdout("-- move files to "+odir)
        c.move_files(tmpdir, odir)
        print_to_stdout("-- remove tmpdir: "+tmpdir)
        c.remove_dir(tmpdir)
        # if everything was fine
        return True
    except Exception as exc:
        sys.exit(f"ERROR!! downloading exec program: {url}\n{exc}")
        return False

def install_make_manager(file, odir):
    # get local folder
    man_dir = os.path.join( local_dir, os.path.basename(file).split('.tar.gz')[0])
    try:
        print_to_stdout("-- extract exec-manager")
        exec_command(f'cd {local_dir} && tar -xvf {file}')
        pass
    except Exception as exc:
        sys.exit(f"ERROR!! extracting the manager: {file}\n{exc}")
    try:
        print_to_stdout("-- configure exec-manager")
        exec_command(f'cd {man_dir} && ./configure --prefix={odir}')
        pass
    except Exception as exc:
        sys.exit(f"ERROR!! configuring the manager: {file}\n{exc}")
    try:
        print_to_stdout("-- make exec-manager")
        exec_command(f'cd {man_dir} && make')
        pass
    except Exception as exc:
        sys.exit(f"ERROR!! making the manager: {file}\n{exc}")
    try:
        print_to_stdout("-- install exec-manager")
        exec_command(f'cd {man_dir} && make install')
        pass
    except Exception as exc:
        sys.exit(f"ERROR!! installing the manager: {file}\n{exc}")
    try:
        print_to_stdout("-- remove tmpdir: "+man_dir)
        c = core.builder(man_dir)
        c.remove_dir(man_dir)
        # if everything was fine
        return True
    except Exception as exc:
        sys.exit(f"ERROR!! removing tmp dir: {man_dir}\n{exc}")
        return False

def install_pip_manager(url):
    try:
        # import core (local library)
        c = core.builder(tmpdir)
        file = os.path.join(local_dir,url)
        print_to_stdout("-- unzip files: "+file+" > "+tmpdir)
        c.unzip_file(file,  tmpdir)
        print_to_stdout("-- get filename")
        p = os.path.join( tmpdir, os.path.basename(file).split('.tar.gz')[0])
        print_to_stdout("-- setup python package")
        exec_command(f'cd "{p}" && "{python_exec}" setup.py install')
    except Exception as exc:
        sys.exit(f"ERROR!! downloading exec program: {url}\n{exc}")
    finally:
        print_to_stdout("-- remove tmpdir: "+tmpdir)
        c.remove_dir(tmpdir)
    # if everything was fine
    return True

def check_manager(manager):
    # handle manager file
    manager = os.path.join(lib_home, manager)
    # check if package manager is installed
    if not (os.path.isfile(manager) or os.path.isfile(manager+'.exe')):
        sys.exit(f"ERROR!! The manager file does not exit: {manager}")
    # if everything was fine
    return True

def install_package(manager, pkg):
    try:
        # handle manager file
        manager = os.path.join(lib_home, manager)
        # create command
        exec_command(f'cd "{local_dir}" && "{manager}" {pkg}')
        # if everything was fine
        return True
    except Exception as exc:
        sys.exit(f"ERROR!! installing the package: {pkg}\n{exc}")
        return False

def download_data(url, odir):
    print_to_stdout(f"** Downloading data: {url}")
    try:
        # import core (local library)
        c = core.builder(odir)
        print_to_stdout("-- download files: "+url+" > "+odir)
        file = c.download_url(url, outdir=odir)
        print_to_stdout("-- unzip files: "+file+" > "+odir)
        c.unzip_file(file,  odir)
        f = f"{odir}/download"
        print_to_stdout("-- remove tmp file: "+f)
        c.remove_file(f)
        # if everything was fine
        return True
    except Exception as exc:
        sys.exit(f"ERROR!! downloading databases: {url}\n{exc}")
        return False

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

    # if apply, look through the new requirements
    for trep in ['EXEC','MAKE','PIP','MANAGER','DATABASES','SAMPLES']:
        if trep in req_new:
            for manager,packages in req_new[trep].items():
                # check if the new package manager is already installed
                if ( trep in req_loc and manager in req_loc[trep] ):
                    print_to_stdout(f"** The manager was already installed: {manager}")
                    print_to_stdout("** The process was completed successfully")                    
                    # install package's
                    for pkg in packages:
                        print_to_stdout(f"** Installing collected package: {pkg.split()[-1]}")
                        # check if the new package is already installed
                        if not pkg in req_loc[trep][manager]:
                            iok = install_package(manager, pkg)
                            # save the new module
                            if iok:
                                req_loc[trep][manager].append(pkg)
                                print_to_stdout("** The process was completed successfully")
                        else:
                            print_to_stdout("** The process was completed successfully")
                # otherwise, install the manager
                else:
                    # extract the optional parameter
                    m = re.split(r'[\s|\t]+', manager)
                    if m:
                        # get the manager
                        man = m[0]
                        # get the name of output dir and create it
                        if len(m) > 1:
                            man_dir = os.path.join(lib_home, m[1])
                            c = core.builder()
                            c.prepare_workspace(man_dir)
                    if trep == 'EXEC':
                        print_to_stdout(f"** Installing exec manager: {man}")
                        iok = install_exec_manager(man, man_dir)
                        print_to_stdout("** The process was completed successfully")
                    if trep == 'MAKE':
                        print_to_stdout(f"** Installing make manager: {man}")
                        iok = install_make_manager(man, man_dir)
                        print_to_stdout("** The process was completed successfully")
                    if trep == 'PIP':
                        print_to_stdout(f"** Installing pip module: {man}")
                        iok = install_pip_manager(man)
                        print_to_stdout("** The process was completed successfully")
                    if trep == 'MANAGER':
                        print_to_stdout(f"** Installing pip module: {man}")
                        iok = check_manager(man)
                        print_to_stdout("** The process was completed successfully")
                    elif trep == 'DATABASES':
                        print_to_stdout(f"** Installing db manager: {man}")
                        iok = download_data(man, man_dir)
                    elif trep == 'SAMPLES':
                        print_to_stdout(f"** Installing samples manager: {man}")
                        iok = download_data(man, man_dir)
                    # save modules in the req local
                    if iok:
                        if not trep in req_loc:
                            req_loc[trep] = {}
                        if not manager in req_loc[trep]:
                            req_loc[trep][manager] = []
                    # install package from the manager (pip, npm, etc)
                    for pkg in packages:
                        print_to_stdout(f"** Installing collected package: {pkg.split()[-1]}")
                        # check if the new package is already installed
                        iok = install_package(manager, pkg)
                        # save the new module
                        if iok:
                            req_loc[trep][manager].append(pkg)
                            print_to_stdout("** The process was completed successfully")

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
    # provide only the requierement file
    elif len(sys.argv) == 2:
        requirement_new_file = sys.argv[1]
        lib_home = os.path.dirname(python_exec) # the lib to install is the directory of python exec
        # lib_home = local_dir # the lib to install is the local directory
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
    
    # check input files
    if ( not os.path.isfile(requirement_new_file) ):
        sys.exit(f"ERROR!! requirement input file is not exists: {requirement_new_file}")
    
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
