@ECHO OFF

:: create env variable with the local directory
SET  SRC_HOME="%~dp0"
SET  SRC_HOME=%SRC_HOME:"=%
SET  SRC_HOME=%SRC_HOME:~0,-1%


:: go to home
CD "%SRC_HOME%"


:: check env varibles are defined
:: get the lib version version
FOR /f %%i in ('CALL "%SRC_HOME%/install/win/jsonextractor.bat" app/package.json version') do SET ISANXOT_VERSION=%%i
SET ISANXOT_VERSION=%ISANXOT_VERSION:"=%
FOR /f "tokens=1,2 delims=." %%a in (^"%ISANXOT_VERSION:"=.%^") do SET LIB_VERSION=%%a.%%b


:: install the packages or not, that the question
:: check env varibles are defined
:: check the version of current library
IF "%ISANXOT_NODE_PATH%"=="" SET r=true
IF "%ISANXOT_LIB_HOME%"==""  SET r=true
FOR %%f in (%ISANXOT_LIB_HOME%) do SET LIB_VERSION_C=%%~nxf
IF not "%LIB_VERSION%"=="%LIB_VERSION_C%"  SET r=true
IF "%r%" == "true" (
    GOTO :installPackages
)


:: execute application in background
GOTO :executeISANXOT





:: Local Functions ------------

:: if library path is not defined, then install the packages
:installPackages
    ECHO ** install iSanXoT packages
    CALL install/install_win64.bat %LIB_VERSION%
    GOTO :executeISANXOT

:: execute application in background
:executeISANXOT
    ECHO ** running iSanXoT
    START "iSanXoT" "%ISANXOT_NODE_PATH%/electron/dist/electron.exe" "%SRC_HOME%/app"
    GOTO :EndProcess


:EndProcess
    :: wait to Enter => Good installation
    SET /P DUMMY=The application has been closed. Hit ENTER to continue...
