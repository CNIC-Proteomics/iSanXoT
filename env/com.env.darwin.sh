#/usr/bin/bash

# local variables  ----------------------
ENV_HOME=${PWD}

# check input parameters ----------------------
if [[ $#<2 ]]
then
    # add the output parameter
    echo "Please, add the whole parameters:
    1. Path to python executable
    2. Path to install the frontend modules"
    exit
fi

# get the python executable ----------------------
PYTHON_EXEC=${1}
if [[ ${PYTHON_EXEC} == "" ]]
then
    # add the output parameter
    echo "Please, python executable"
    exit
fi
INSTALLER_SCRIPT=${ENV_HOME}/../env/installer.py
REQUIREMENTS_FRONTEND_ENV=${ENV_HOME}/node/requirements_frontend_darwin-x64.txt
REQUIREMENTS_BACKEND_PYTHON=${ENV_HOME}/node/requirements_backend_darwin-x64.txt


# get the frontend home for the installation of modules ----------------------
ISANXOT_FRONTEND_HOME=${2}
if [[ ${ISANXOT_FRONTEND_HOME} == "" ]]
then
    # add the output parameter
    echo "Please, add the frontend folder"
    exit
fi


# create the frontend environment: node, node modules, electron, etc. ----------------------
echo "**"
echo "** creating the frontend environment: node, node modules, electron..."
${PYTHON_EXEC} ${INSTALLER_SCRIPT} ${REQUIREMENTS_FRONTEND_ENV}  ${ISANXOT_FRONTEND_HOME}


# # update pip ----------------------
# echo "**"
# echo "** updating pip..."
# ${PYTHON_EXEC} -m pip install  --no-warn-script-location  --upgrade pip


# # create the backend environment: python venv, packages, etc. ----------------------
# echo "**"
# echo "** creating the backend environment: python venv, packages..."
# ${PYTHON_EXEC} ${INSTALLER_SCRIPT} ${REQUIREMENTS_BACKEND_PYTHON}
