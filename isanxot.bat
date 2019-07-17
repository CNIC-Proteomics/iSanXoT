@ECHO OFF

:: check env varibles are defined
IF "%ISANXOT_SRC_HOME%"==""  GOTO :EndProcess1
IF "%ISANXOT_NODE_PATH%"=="" GOTO :EndProcess2

:: go to home
CD "%ISANXOT_SRC_HOME%"

:: execute application
ECHO ** running iSanXoT
CMD /C " "%ISANXOT_NODE_PATH%/electron/dist/electron.exe" app "

:: finish
GOTO :EndProcess




:: checking "functions" ------------
:EndProcess1
    ECHO ISANXOT_SRC_HOME env. variable is NOT defined
    GOTO :EndProcess
:EndProcess2
    ECHO ISANXOT_NODE_PATH env. variable is NOT defined
    GOTO :EndProcess
:EndProcess
    :: wait to Enter => Good installation
    REM SET /P DUMMY=The application has been closed. Hit ENTER to continue...
