@ECHO OFF

:: local variables  ----------------------
SET  INSTALL_HOME="%~dp0"
SET  INSTALL_HOME=%INSTALL_HOME:"=%
SET  INSTALL_HOME=%INSTALL_HOME:~0,-1%

:: type of installation ----------------------
SET  TYPE_INSTALLER=%1
IF "%TYPE_INSTALLER%"=="initInstallation"     GOTO :initInstallation
IF "%TYPE_INSTALLER%"=="updateInstallation"   GOTO :updateInstallation


:: --------------- ::
:: Local Functions ::
:: --------------- ::

:: ------------------------------------------------
:initInstallation
:: Declare variables for the initialization of installer

    :: get input parameter
    SET  LIB_VERSION=%2

    :: previous requirement
    ECHO **
    ECHO ** IMPORTANT NOTE!!
    ECHO ** "Microsoft Visual C++ 14.0" is required.
    ECHO ** Windows Python needs Visual C++ libraries installed via the SDK to build code.
    ECHO **
    SET  /p FINIH_BATCH="'Microsoft Visual C++ 14.0' is installed (Y/N)? "
    IF "%FINIH_BATCH%"=="N" GOTO :VisualCNotInstalled
    IF "%FINIH_BATCH%"=="n" GOTO :VisualCNotInstalled

    :: ask about the library path
    ECHO **
    ECHO ** Starts the installation
    SET  MODE="production"
    SET  LIB_NAME=iSanXoT
    SET  LIB_PATH="%HOMEDRIVE%%HOMEPATH%/%LIB_NAME%"
    SET  /p LIB_PATH="Enter the path where %LIB_NAME% libraries will be saved (by default %LIB_PATH%): "
    SET  LIB_PATH=%LIB_PATH:"=%
    SET  ISANXOT_LIB_HOME=%LIB_PATH%/%LIB_VERSION%

    :: create library folder
    ECHO **
    ECHO ** create library directory
    ECHO %ISANXOT_LIB_HOME%
    IF NOT EXIST "%ISANXOT_LIB_HOME%" MD "%ISANXOT_LIB_HOME%"

    :: starts the installer
    GOTO :execInstaller


:: ------------------------------------------------
:updateInstallation
:: Declare variables for the upgrade of installer

    :: get input parameter
    SET  ISANXOT_LIB_HOME=%2
    :: starts the installer
    GOTO :execInstaller



:: ------------------------------------------------
:execInstaller
:: Starts the installer (from the beggining or an upgrade of libraries)

    :: local variables
    ECHO **
    ECHO ** declare variables
    SET  PYTHON3x_VERSION=3.6.7
    REM SET  PYTHON3x_HOME=%ISANXOT_LIB_HOME%/python
    SET  PYTHON3x_HOME="%ISANXOT_LIB_HOME%/python.%PYTHON3x_VERSION%"
    SET  PYTHON3x_HOME=%PYTHON3x_HOME:"=%

    :: install the 'python' executable if it does not exist
    SET PYTHON3x_SCRIPT=%PYTHON3x_HOME%/tools/python.exe
    IF NOT EXIST "%PYTHON3x_SCRIPT%" (
        ECHO **
        ECHO ** install the 'python'
        CMD /C " "%INSTALL_HOME%/win/nuget.exe"  install python -Version "%PYTHON3x_VERSION%" -OutputDirectory "%ISANXOT_LIB_HOME%" "
        REM CMD /C " "%INSTALL_HOME%/win/nuget.exe"  install python -Version "%PYTHON3x_VERSION%" -OutputDirectory "%ISANXOT_LIB_HOME%/tmp" && REN "%ISANXOT_LIB_HOME%/tmp/python.%PYTHON3x_VERSION%" ../python"
        :: if everything was fine or not
        IF NOT "%ERRORLEVEL%"=="0" GOTO :wrongProcess
    )

    :: upgrade library
    ECHO **
    ECHO ** upgrade library
    CMD /C " "%PYTHON3x_HOME%/tools/python" "%INSTALL_HOME%/src/installer.py" "%INSTALL_HOME%"  "%ISANXOT_LIB_HOME%" "
    :: if everything was fine or not
    IF NOT "%ERRORLEVEL%"=="0" GOTO :wrongProcess

    :: everything was fine
    GOTO :successProcess


:: ------------------------------------------------
:VisualCNotInstalled
:: Out of program because Microsoft Visual C++ is not installed
    ECHO   Please, install it before
    ECHO   For more information:
    ECHO   https://www.scivision.co/python-windows-visual-c++-14-required
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
:: save the library home in a environment variables
    ECHO **
    ECHO ** save environment variables
    IF "%ISANXOT_MODE%"=="" SETX ISANXOT_MODE "production"
    SETX ISANXOT_LIB_HOME "%ISANXOT_LIB_HOME%"
    ECHO **
    ECHO ** The installation has been successfully completed!!
    GOTO :EndProcess


:: ------------------------------------------------
:EndProcess
:: Installation has finished
    REM SET /P DUMMY=End of installation. Hit ENTER to continue...
