@ECHO OFF

:: sets the env. variables from input parameters ----------------------
ECHO **
ECHO **
ECHO ** sets the env. variables from input parameters:

ECHO **
SET  SRC_HOME="%~dp0"
SET  SRC_HOME=%SRC_HOME:"=%
SET  SRC_HOME=%SRC_HOME:~0,-1%

ECHO **
SET  MODE="production"
SET  LIB_NAME=iSanXoT
SET  LIB_VERSION=%1
SET  LIB_PATH="%HOMEDRIVE%%HOMEPATH%/%LIB_NAME%"
SET  /p LIB_PATH="** Enter the path where %LIB_NAME% libraries will be saved (by default %LIB_PATH%): "
SET  LIB_PATH=%LIB_PATH:"=%
SET  LIB_HOME=%LIB_PATH%/%LIB_VERSION%

ECHO %LIB_HOME%

ECHO **
SET  PYTHON3x_VERSION=3.6.7
SET  PYTHON3x_HOME="%LIB_HOME%/python.%PYTHON3x_VERSION%"
SET  PYTHON3x_HOME=%PYTHON3x_HOME:"=%

ECHO **
SET  NODE_HOME=%LIB_HOME%/node
SET  NODE_PATH=%NODE_HOME%/node_modules

:: Stablish this env variable for the git python
SETX GIT_PYTHON_REFRESH quiet


:: create library directory ----------------------
IF NOT EXIST "%LIB_HOME%" MD "%LIB_HOME%"


:: install the 'python' ----------------------
ECHO **
ECHO **
ECHO ** install the 'python'
CMD /C " "%SRC_HOME%/win/nuget.exe"  install python -Version "%PYTHON3x_VERSION%" -OutputDirectory "%LIB_HOME%" "


:: install the PIP package ----------------------
ECHO **
ECHO **
ECHO ** install the 'pip' package
CMD /C " "%PYTHON3x_HOME%/tools/python" "%SRC_HOME%/src/get-pip.py"  --no-warn-script-location "


:: install required packages ----------------------
ECHO **
ECHO **
ECHO ** install required packages
CMD /C " "%PYTHON3x_HOME%/tools/Scripts/pip3.exe" install numpy fsspec matplotlib scipy snakemake pandas pprint multiprocess times more-itertools concurrent-utils dask toolz cloudpickle distributed biopython --no-warn-script-location "


:: download and install npm ----------------------
ECHO **
ECHO **
ECHO ** download and install npm
SET  NODE_URL=https://nodejs.org/dist/v10.14.2/node-v10.14.2-win-x64.zip
CMD /C " "%PYTHON3x_HOME%/tools/python" "%SRC_HOME%/src/install_url_pkg.py" "%NODE_URL%" "%NODE_HOME%" "%LIB_HOME%/tmp" "


:: install electron package ----------------------
ECHO **
ECHO **
ECHO ** install electron package
CMD /C " "%NODE_HOME%/npm" config set scripts-prepend-node-path true"
REM CMD /C " "%NODE_HOME%/npm" install electron --save-dev --save-exact --global "
:: install the lastest version of 7.x.x
CMD /C " "%NODE_HOME%/npm" install electron@^7.0.0 --save-dev --save-exact --global "
CMD /C " "%NODE_HOME%/npm" install ps-tree --global "
CMD /C " "%NODE_HOME%/npm" install xlsx --global "
CMD /C " "%NODE_HOME%/npm" install js-yaml --global "
REM CMD /C " "%NODE_HOME%/npm" install fs-extra --global "


:: download databases ----------------------
ECHO **
ECHO **
ECHO ** download databases
SET  DB_URL=https://www.cnic.es/nextcloud/index.php/s/Pm6AJ65XQjeBM5G/download
CMD /C " "%PYTHON3x_HOME%/tools/python" "%SRC_HOME%/src/download_dbs.py" "%DB_URL%" "%SRC_HOME%/../dbs" "


:: TODO!!! ----- 
:: CAPTURE THE ERROR IN BATCH

GOTO :EndProcess

:: wait to Enter => Good installation
:EndProcess

    :: create env variables ----------------------
    ECHO **
    ECHO **
    ECHO ** create the env. variables
    ECHO %SRC_HOME%
    ECHO %LIB_HOME%
    ECHO %PYTHON3x_HOME%
    ECHO %NODE_HOME%
    ECHO %NODE_PATH%
    SETX ISANXOT_MODE "%MODE%"
    SETX ISANXOT_LIB_HOME "%LIB_HOME%"
    SETX ISANXOT_PYTHON3x_HOME "%PYTHON3x_HOME%"
    SETX ISANXOT_NODE_HOME "%NODE_HOME%"
    SETX ISANXOT_NODE_PATH "%NODE_PATH%"


    SET /P DUMMY=End of installation. Hit ENTER to continue...
