# sets the env. variables from input parameters ----------------------
# sets the env. variables from input parameters:

# ECHO **
# SET  SRC_HOME="%~dp0"
# SET  SRC_HOME=%SRC_HOME:"=%
# SET  SRC_HOME=%SRC_HOME:~0,-1%

# ECHO **
# SET  MODE="production"
# SET  LIB_NAME=iSanXoT
# SET  LIB_VERSION=%1
# SET  LIB_PATH="%HOMEDRIVE%%HOMEPATH%/%LIB_NAME%"
# SET  /p LIB_PATH="** Enter the path where %LIB_NAME% libraries will be saved (by default %LIB_PATH%): "
# SET  LIB_PATH=%LIB_PATH:"=%
# SET  LIB_HOME=%LIB_PATH%/%LIB_VERSION%

# ECHO %LIB_HOME%

# ECHO **
# SET  PYTHON3x_VERSION=3.6.7
# SET  PYTHON3x_HOME="%LIB_HOME%/python.%PYTHON3x_VERSION%"
# SET  PYTHON3x_HOME=%PYTHON3x_HOME:"=%

# ECHO **
# SET  NODE_HOME=%LIB_HOME%/node
# SET  NODE_PATH=%NODE_HOME%/node_modules

# :: Stablish this env variable for the git python
# SETX GIT_PYTHON_REFRESH quiet


# :: create library directory ----------------------
# IF NOT EXIST "%LIB_HOME%" MD "%LIB_HOME%"


# install the 'python' ----------------------
#  https://www.python.org/ftp/python/3.6.7/Python-3.6.7.tgz

# Build Instructions
# ------------------

# On Unix, Linux, BSD, macOS, and Cygwin::

#     ./configure
#     make
#     make test
#     sudo make install

# This will install Python as ``python3``.

# You can pass many options to the configure script; run ``./configure --help``
# to find out more.  On macOS and Cygwin, the executable is called ``python.exe``;
# elsewhere it's just ``python``.

