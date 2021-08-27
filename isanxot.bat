@ECHO OFF

:: create env variable with the local directory
SET  SRC_HOME="%~dp0"
SET  SRC_HOME=%SRC_HOME:"=%
SET  SRC_HOME=%SRC_HOME:~0,-1%


:: go to home
CD "%SRC_HOME%"


:: check env varibles are defined
:: get the lib version version
FOR /f "tokens=2 delims=: " %%l in ('FINDSTR /r "version" "%SRC_HOME%\\app\\package.json" ') do SET ISANXOT_VERSION=%%l
SET ISANXOT_VERSION=%ISANXOT_VERSION:"=%
FOR /f "tokens=1,2 delims=." %%a in (^"%ISANXOT_VERSION:"=.%^") do SET LIB_VERSION=%%a.%%b


:: install the packages or not, that the question
IF "%ISANXOT_LIB_HOME%"==""  SET r=true
FOR %%f in (%ISANXOT_LIB_HOME%) do SET LIB_VERSION_C=%%~nxf
IF NOT "%LIB_VERSION%"=="%LIB_VERSION_C%"  SET r=true

:: the library path is empty or the version is different
IF "%r%" == "true" GOTO :installPackages
:: the library path does not exist
IF NOT EXIST "%ISANXOT_LIB_HOME%" GOTO :installPackages


:: update packages if apply
GOTO :updatePackages





:: --------------- ::
:: Local Functions ::
:: --------------- ::


:: ------------------------------------------------
:installPackages
:: if library path is not defined, then install the packages
    ECHO ** install iSanXoT packages
    CALL "install/install_win64.bat" initInstallation %LIB_VERSION%
    :: if everything was fine or not
    IF NOT "%ERRORLEVEL%"=="0" GOTO :wrongProcess
    :: everything was fine
    GOTO :executeISANXOT


:: ------------------------------------------------
:updatePackages
:: if library path is defined, then update the packages
    ECHO ** update iSanXoT packages
    CALL "install/install_win64.bat" updateInstallation "%ISANXOT_LIB_HOME%"
    :: if everything was fine or not
    IF NOT "%ERRORLEVEL%"=="0" GOTO :wrongProcess
    :: everything was fine
    GOTO :executeISANXOT


:: ------------------------------------------------
:executeISANXOT
:: execute application in background
    ECHO ** execute iSanXoT
    SET  ISANXOT_LIB_HOME=%ISANXOT_LIB_HOME:"=%
    START "iSanXoT" "%ISANXOT_LIB_HOME%/exec/node/node_modules/electron/dist/electron.exe" --trace-warnings "%SRC_HOME%/app"
    :: if everything was fine or not
    IF NOT "%ERRORLEVEL%"=="0" GOTO :wrongProcess
    :: everything was fine
    GOTO :EndProcess


:: ------------------------------------------------
:wrongProcess
:: Process was not completed
    ECHO **
    ECHO ** ERROR: The execution was not completed successfully!!
    SET /P DUMMY=End of execution. Hit ENTER to exit...
    GOTO :EndProcess


:: ------------------------------------------------
:EndProcess
:: Execution has finished
    REM SET /P DUMMY=End of execution. Hit ENTER to exit...