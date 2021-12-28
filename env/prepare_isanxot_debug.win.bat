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
MKDIR "%ISANXOT_HOME%\app\resources\env"
MKDIR "%ISANXOT_HOME%\app\resources\env\python\packages\win-x64"
MKDIR "%ISANXOT_HOME%\app\resources\env\exec"


ECHO ** copying the cached folder of python...
XCOPY /E /I /Y  "%ISANXOT_HOME%\env\python\Python-3.9.7"  "%ISANXOT_HOME%\app\resources\exec\python-3.9.7-win-x64"


ECHO ** copying the scripts that create the backend environment...
COPY   "%ISANXOT_HOME%\env\installer.py" "%ISANXOT_HOME%\app\resources\env\."
COPY   "%ISANXOT_HOME%\env\core.py"      "%ISANXOT_HOME%\app\resources\env\."


ECHO ** copying the python packages...
COPY "%ISANXOT_HOME%\env\python\pip-21.3.1.tar.gz"                "%ISANXOT_HOME%\app\resources\env\python\."
COPY "%ISANXOT_HOME%\env\python\setuptools-59.6.0.tar.gz"         "%ISANXOT_HOME%\app\resources\env\python\."
COPY "%ISANXOT_HOME%\env\python\requirements_python_win-x64.txt"  "%ISANXOT_HOME%\app\resources\env\python\."
XCOPY /E /I /Y  "%ISANXOT_HOME%\env\python\packages\win-x64"  "%ISANXOT_HOME%\app\resources\env\python\packages\win-x64\."


ECHO ** copying the files for the exec environment...
COPY  "%ISANXOT_HOME%\env\exec\windows_10_msbuild_Release_graphviz-2.50.0-win32.zip" "%ISANXOT_HOME%\app\resources\env\exec\."
COPY  "%ISANXOT_HOME%\env\exec\requirements_exec_win-x64.txt"                        "%ISANXOT_HOME%\app\resources\env\exec\."



:: everything was fine
GOTO :successProcess


:: ------------------------------------------------
:addISANXOThome
:: Add parameter
    ECHO   Please, give the isanxot home
    GOTO :EndProcess
:: ------------------------------------------------
:successProcess
:: Installation has finished successfully
    ECHO **
    ECHO ** The process has been successfully completed!!
    GOTO :EndProcess
:: ------------------------------------------------
:EndProcess
    @REM SET /P DUMMY=End of execution. Hit ENTER to exit...
