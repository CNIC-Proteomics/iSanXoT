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
cloud_url = 'https://www.cnic.es/nextcloud/s/cmWA4xZEBk2mjMZ/download?path=%2F'
exec_url = f"{cloud_url}install%2Fwindows%2F"
execdir = f"{lib_home}/exec"
dbs_url = f"{cloud_url}dbs%2F"
dbsdir = f"{lib_home}/dbs"
samples_url = f"{cloud_url}samples%2F"
spdir = f"{lib_home}/samples"



###################
# Local functions #
###################

# Create directories recursively, if they don't exist
def prepare_workspace(dirs):
    if not os.path.exists(dirs):
        try:
            os.makedirs(dirs)
        except:
            sys.exit("ERROR!! preparing the workspace")

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

def install_exec_manager(manager, url, odir):
    try:
        # local library
        import core
        print("-- create builder")
        c = core.builder(tmpdir)
        print("-- download files: "+url+" > "+tmpdir)
        file = c.download_url(url, outdir=tmpdir)
        print("-- unzip files: "+file+" > "+tmpdir)
        c.unzip_file(file,  tmpdir)
        print("-- move files to outdir")
        c.move_files(tmpdir, odir)
        print("-- remove tmpdir")
        c.remove_dir(tmpdir)
        # if everything was fine
        return True

    except Exception as exc:
        sys.exit(f"ERROR!! downloading exec program: {manager}\n{exc}")

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
        manager = "{}/{}".format(lib_home, manager)
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

def download_databases(manager):
    try:
        # local library
        import core
        # handle manager file
        version = manager
        print("-- create builder")
        c = core.builder(dbsdir)
        print("-- create url")
        db_url = dbs_url + version
        print("-- download files: "+db_url+" > "+dbsdir)
        file = c.download_url(db_url, outdir=dbsdir)
        print("-- unzip files: "+file+" > "+dbsdir)
        c.unzip_file(file,  dbsdir)
        # if everything was fine
        return True
    except Exception as exc:
        sys.exit(f"ERROR!! downloading databases: {manager}\n{exc}")

def download_samples(manager):
    try:
        # local library
        import core
        # handle manager file
        version = manager
        print("-- create builder")
        c = core.builder(spdir)
        print("-- create url")
        sp_url = samples_url + version
        print("-- download files: "+sp_url+" > "+spdir)
        file = c.download_url(sp_url, outdir=spdir)
        print("-- unzip files: "+file+" > "+spdir)
        c.unzip_file(file,  spdir)
        # if everything was fine
        return True
    except Exception as exc:
        sys.exit(f"ERROR!! downloading samples: {manager}\n{exc}")

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
    # look through the new requirements
    for manager,packages in req_new[trep].items():
        # extract the optional parameter
        man = re.split(r'[\s|\t]+', manager)
        if man:
            manager = man[0]
            # check if the new package manager is already installed
            if (not trep in req_loc) or (not manager in req_loc[trep]):
                if trep == 'EXEC':
                    print("-- install executors")
                    man_dir = man[1] if len(man) > 1 else manager # get the name of output dir. By default, the given file
                    iok = install_exec_manager(manager, f"{exec_url}/{manager}", f"{execdir}/{man_dir}")
                if trep == 'MANAGER':
                    print("** install packages")
                    iok = install_pkg_manager(manager)
                elif trep == 'DATABASES':
                    print("** install databases")
                    iok = download_databases(manager)
                elif trep == 'SAMPLES':
                    print("** install samples")
                    iok = download_samples(manager)
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
    # preapare workspace
    prepare_workspace(node_home)
    prepare_workspace(execdir)
    prepare_workspace(dbsdir)
    prepare_workspace(spdir)
    
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

     
    
if __name__ == '__main__':
    main()