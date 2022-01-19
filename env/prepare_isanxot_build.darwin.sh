#!/bin/bash

# get the isanxot path from the local folder
SRC_HOME=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
ISANXOT_HOME=${SRC_HOME}/..

# go to isanxot home
cd ${ISANXOT_HOME}


echo "** cleaning the app-resources folders..."
rm -rf "${ISANXOT_HOME}/app/resources/env"
rm -rf "${ISANXOT_HOME}/app/resources/exec"


echo "** preparing the app-resources environment folders..."
mkdir -p "${ISANXOT_HOME}/app/resources/exec"


echo "** re-install python..."
cd ${ISANXOT_HOME}/env/python/Python-3.9.7 && make install

