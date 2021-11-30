#/usr/bin/bash

# local variables  ----------------------
ENV_HOME=${PWD}

# check input parameters ----------------------
if [[ $#<3 ]]
then
    # add the output parameter
    echo "Please, add the whole parameters:
    1. Path to python executable
    2. Path to install the frontend modules
    3. Path to install the backend packages"
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
INSTALLER_SCRIPT=${ENV_HOME}/../resources/env/installer.py
REQUIREMENTS_FRONTEND_ENV=${ENV_HOME}/requirements_frontend_linux-x64.txt
REQUIREMENTS_BACKEND_PYTHON=${ENV_HOME}/requirements_backend_linux-x64.txt


# get the frontend home for the installation of modules ----------------------
ISANXOT_FRONTEND_HOME=${2}
if [[ ${ISANXOT_FRONTEND_HOME} == "" ]]
then
    # add the output parameter
    echo "Please, add the frontend folder"
    exit
fi


# get the backend home for the installation of packages ----------------------
ISANXOT_BACKEND_HOME=${3}
if [[ ${ISANXOT_BACKEND_HOME} == "" ]]
then
    # add the output parameter
    echo "Please, add the backend folder"
    exit
fi
# set the python home
ISANXOT_BACKEND_HOME_PYTHON=${ISANXOT_BACKEND_HOME}/python
# overwrite the Python executable
PYTHON_ENV_EXEC=${ISANXOT_BACKEND_HOME_PYTHON}/bin/python


# create the frontend environment: node, node modules, electron, etc. ----------------------
echo "**"
echo "** creating the frontend environment: node, node modules, electron..."
${PYTHON_EXEC} ${INSTALLER_SCRIPT} ${REQUIREMENTS_FRONTEND_ENV}  ${ISANXOT_FRONTEND_HOME}


# create the python environment ----------------------
echo "**"
echo "** creating the Python environment..."
${PYTHON_EXEC} -m venv --upgrade-deps --copies  ${ISANXOT_BACKEND_HOME_PYTHON}


# create the backend environment: python venv, packages, etc. ----------------------
echo "**"
echo "** creating the backend environment: python venv, packages..."
${PYTHON_ENV_EXEC} ${INSTALLER_SCRIPT} ${REQUIREMENTS_BACKEND_PYTHON}  ${ISANXOT_BACKEND_HOME_PYTHON}
