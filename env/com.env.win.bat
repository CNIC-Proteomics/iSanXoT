@ECHO OFF

:: local variables  ----------------------
SET  ENV_HOME="%~dp0"
SET  ENV_HOME=%ENV_HOME:"=%
SET  ENV_HOME=%ENV_HOME:~0,-1%


:: check input parameters ----------------------
SET argC=0
FOR %%x in (%*) DO SET /A argC+=1
IF (%argC% LSS "2") (
    :: add the output parameter
    GOTO :addParameters
)


:: get the python executable ----------------------
SET  PYTHON_EXEC=%1
IF %PYTHON_EXEC%=="" (
    :: Add the output parameter
    GOTO :addPythonExecHome
)
:: remove "'s
SET  PYTHON_EXEC=%PYTHON_EXEC:"=%
SET  INSTALLER_SCRIPT=%ENV_HOME%/../resources/env/installer.py
SET  REQUIREMENTS_FRONTEND_ENV=%ENV_HOME%/requirements_frontend_win-x64.txt
SET  REQUIREMENTS_BACKEND_PYTHON=%ENV_HOME%/requirements_backend_win-x64.txt



:: get the frontend home for the installation of modules ----------------------
SET  ISANXOT_FRONTEND_HOME=%2
IF %ISANXOT_FRONTEND_HOME%=="" (
    :: Add the output parameter
    GOTO :addFrontEndHome
)
:: remove "'s
SET  ISANXOT_FRONTEND_HOME=%ISANXOT_FRONTEND_HOME:"=%


:: create the frontend environment: node, node modules, electron, etc. ----------------------
ECHO **
ECHO ** creating the frontend environment: node, node modules, electron...
CMD /C " "%PYTHON_EXEC%" "%INSTALLER_SCRIPT%" "%REQUIREMENTS_FRONTEND_ENV%"  "%ISANXOT_FRONTEND_HOME%" "
:: if everything was fine or not (error => 1 or more)
IF %ERRORLEVEL% GEQ 1 GOTO :wrongProcess


@REM :: update pip ----------------------
@REM ECHO **
@REM ECHO ** updating pip...
@REM CMD /C " "%PYTHON_EXEC%" -m pip install  --no-warn-script-location  --upgrade pip "
@REM :: if everything was fine or not (error => 1 or more)
@REM IF %ERRORLEVEL% GEQ 1 GOTO :wrongProcess


@REM :: create the backend environment: python venv, packages, etc. ----------------------
@REM ECHO **
@REM ECHO ** creating the backend environment: python venv, packages...
@REM CMD /C " "%PYTHON_EXEC%" "%INSTALLER_SCRIPT%" "%REQUIREMENTS_BACKEND_PYTHON%" "
@REM :: if everything was fine or not (error => 1 or more)
@REM IF %ERRORLEVEL% GEQ 1 GOTO :wrongProcess

:: everything was fine
GOTO :successProcess





:: ------------------------------------------------
:addParameters
:: Add the output parameter
    ECHO Please, add the whole parameters:
    ECHO   1. Path to python executable
    ECHO   2. Path to install the frontend modules
    GOTO :EndProcess
:: ------------------------------------------------
:addPythonExecHome
:: Add the output parameter
    ECHO   Please, python executable
    GOTO :EndProcess
:: ------------------------------------------------
:addFrontEndHome
:: Add the output parameter
    ECHO   Please, add the frontend folder
    GOTO :EndProcess
:: ------------------------------------------------
:addBackEndHome
:: Add the output parameter
    ECHO   Please, add the backend folder
    GOTO :EndProcess
:: ------------------------------------------------
:wrongProcess
:: Process was not completed
    ECHO **
    ECHO ** ERROR: The installation was not completed successfully!!
    GOTO :EndProcess
:: ------------------------------------------------
:successProcess
:: Installation has finished successfully
    ECHO **
    ECHO ** The installation has been successfully completed!!
    GOTO :EndProcess
:: ------------------------------------------------
:EndProcess
:: Installation has finished
