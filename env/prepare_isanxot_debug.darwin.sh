
# get the isanxot path from the local folder
SRC_HOME${PWD}
ISANXOT_HOME=${SRC_HOME}/..

# go to isanxot home
CD ${ISANXOT_HOME}


echo "** cleaning the app-resources folders..."
rm -rf "${ISANXOT_HOME}/app/resources/env"
rm -rf "${ISANXOT_HOME}/app/resources/exec"


echo "** preparing the app-resources environment folders..."
mkdir -p "${ISANXOT_HOME}/app/resources/env"
mkdir -p "${ISANXOT_HOME}/app/resources/env/python/packages/darwin-x64"
mkdir -p "${ISANXOT_HOME}/app/resources/env/exec"


echo "** copying the cached folder of python..."
cp -r "${ISANXOT_HOME}/env/python/Python-3.9.7"  "${ISANXOT_HOME}/app/resources/exec/python-3.9.7-darwin-x64"


echo "** copying the scripts that create the backend environment..."
cp -r "${ISANXOT_HOME}/env/installer.py" "${ISANXOT_HOME}/app/resources/env/."
cp -r "${ISANXOT_HOME}/env/core.py"      "${ISANXOT_HOME}/app/resources/env/."


echo "** copying the python packages..."
cp -r "${ISANXOT_HOME}/env/python/pip-21.3.1.tar.gz"                   "${ISANXOT_HOME}/app/resources/env/python/."
cp -r "${ISANXOT_HOME}/env/python/setuptools-59.6.0.tar.gz"            "${ISANXOT_HOME}/app/resources/env/python/."
cp -r "${ISANXOT_HOME}/env/python/requirements_python_darwin-x64.txt"  "${ISANXOT_HOME}/app/resources/env/python/."
cp -r "${ISANXOT_HOME}/env/python/packages/darwin-x64"                 "${ISANXOT_HOME}/app/resources/env/python/packages/."


echo "** copying the files for the exec environment..."
cp -r "${ISANXOT_HOME}/env/exec/graphviz-2.50.0.tar.gz"            "${ISANXOT_HOME}/app/resources/env/exec/."
cp -r "${ISANXOT_HOME}/env/exec/requirements_exec_darwin-x64.txt"  "${ISANXOT_HOME}/app/resources/env/exec/."
