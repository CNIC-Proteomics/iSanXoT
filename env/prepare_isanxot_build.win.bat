@ECHO OFF


:: get the isanxot path from the local folder
SET SRC_HOME="%~dp0"
SET SRC_HOME=%SRC_HOME:"=%
SET SRC_HOME=%SRC_HOME:~0,-1%
SET ISANXOT_HOME=%SRC_HOME%\..

:: go to isanxot home
CD "%ISANXOT_HOME%"


ECHO ** cleaning the app-resources environment folders...
RMDIR /S /Q "%ISANXOT_HOME%\app\resources\env"
RMDIR /S /Q "%ISANXOT_HOME%\app\resources\exec"


ECHO ** preparing the app-resources environment folders...
MKDIR "%ISANXOT_HOME%\app\resources\exec"


ECHO ** copying the cached folder of python...
XCOPY /E /I /Y  "%ISANXOT_HOME%\env\python\Python-3.9.7"  "%ISANXOT_HOME%\app\resources\exec\python-3.9.7-win-x64"


:: everything was fine
GOTO :successProcess


:: ------------------------------------------------
:successProcess
:: Installation has finished successfully
    ECHO **
    ECHO ** The process has been successfully completed!!
    GOTO :EndProcess
:: ------------------------------------------------
:EndProcess
    @REM SET /P DUMMY=End of execution. Hit ENTER to exit...
