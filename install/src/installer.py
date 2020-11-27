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
dbs_url = 'https://www.cnic.es/nextcloud/s/tbwyEbYwzaz2bET/download?path=%2F'
dbsdir = f"{lib_home}/dbs"
samples_url = 'https://www.cnic.es/nextcloud/s/iMtCEZCQBDxmzde/download?path=%2F'
spdir = f"{lib_home}/samples"



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

def download_databases(manager):
    try:
        # local library
        import core
        # handle manager file
        version = manager.replace('$DATABASES=','')
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
        version = manager.replace('$SAMPLES=','')
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
        sys.exit(f"ERROR!! downloading databases: {manager}\n{exc}")

def create_report_requirements(file):
    '''
    Create dictionary with the manager and its required packages
    '''
    report,database,samples = {},{},{}
    if os.path.isfile(file):
        f = open(file)
        lines = f.read().splitlines()
        pk,db,sp = None,None,None
        for line in lines:
            line = line.rstrip()
            if line.startswith('$MANAGER='): # package manager line
                pk,db,sp = line,None,None
                report[pk] = {}
            elif line.startswith('$DATABASES='): # database manager line
                pk,db,sp = None,line,None
                database[db] = {}
            elif line.startswith('$SAMPLES='): # samples manager line
                pk,db,sp = None,None,line
                samples[sp] = {}
            elif not line.startswith('#') and pk is not None: # package line
                s = re.split(r'\t+', line)
                iparams = s[0]
                pkg = s[1] if len(s) > 1 else ''
                report[pk][pkg] = iparams
        f.close()
    return report,database,samples

def create_str_requirements(req):
    '''
    Create string with the manager and its required packages
    '''
    cont = ''
    for manager,packages in req.items():
        cont += f"{manager}\n"
        for pkg,iparams in packages.items():
            cont += f"{iparams}\t{pkg}\n"
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
    req_new,db_new,sp_new = create_report_requirements(requirement_new_file)
    req_loc,db_loc,sp_loc = create_report_requirements(requirement_loc_file)

    # new installation of libraries
    if not req_loc:

        # look through the new requirements ---
        print("-- install packages")
        for manager,packages in req_new.items():
            # install package manager
            iok = install_pkg_manager(manager)
            req_loc[manager] = {}
            # install package's
            for pkg,iparams in packages.items():
                write_ok = install_package(manager, iparams, pkg)
                # save the new required package
                if write_ok:
                    req_loc[manager][pkg] = iparams
        
        # look through the new requirements for the databases ---
        print("-- install databases")
        for manager,packages in db_new.items():
            # download databases
            iok = download_databases(manager)
            # save the database in the local requirements 
            req_loc[manager] = {}

        # look through the new requirements for the samples ---
        print("-- look through the new samples")
        for manager,packages in sp_new.items():
            # download samples
            iok = download_samples(manager)
            # save the database in the local requirements 
            req_loc[manager] = {}

        # write string with the new requiremens into local file ---
        if req_loc:
            cont = create_str_requirements(req_loc)
            if cont != '':
                with open(requirement_loc_file, "w") as file:
                    file.write(cont)
    

    # upgrade the library
    else:
        
        # look through the new requirements ---
        print("-- upgrade packages")
        for manager,packages in req_new.items():
            # check if the new package manager is already installed
            if not manager in req_loc:
                # install package manager
                iok = install_pkg_manager(manager)
                req_loc[manager] = {}
            # install package's
            for pkg,iparams in packages.items():
                # check if the new package is already installed
                if not manager in req_loc or not pkg in req_loc[manager]:
                    write_ok = install_package(manager, iparams, pkg)
                    # save the new required package
                    if write_ok:
                        req_loc[manager][pkg] = iparams

        # look through the new requirements for the databases ---
        print("-- upgrade databases")
        for manager,packages in db_new.items():
            # check if the new database version is already downloaded
            if not manager in db_loc:
                # download databases
                iok = download_databases(manager)
           # save the database in the local requirements 
            req_loc[manager] = {}
        
        # look through the new requirements for the databases ---
        print("-- upgrade samples")
        for manager,packages in sp_new.items():
            # check if the new database version is already downloaded
            if not manager in sp_loc:
                # download databases
                iok = download_samples(manager)
           # save the database in the local requirements 
            req_loc[manager] = {}

        # write string with the new requiremens into local file ---
        if req_loc:
            cont = create_str_requirements(req_loc)
            if cont != '':
                with open(requirement_loc_file, "w") as file:
                    file.write(cont)

     
    
if __name__ == '__main__':
    main()