# -*- coding: utf-8 -*-

# Module metadata variables
__author__ = "Jose Rodriguez"
__credits__ = ["Jose Rodriguez", "Jesus Vazquez"]
__license__ = "Creative Commons Attribution-NonCommercial-NoDerivs 4.0 Unported License https://creativecommons.org/licenses/by-nc-nd/4.0/"
__version__ = "0.0.1"
__maintainer__ = "Jose Rodriguez"
__email__ = "jmrodriguezc@cnic.es"
__status__ = "Development"

#########################
# Import global modules #
#########################
import os
import platform

####################
# Global variables #
####################

plat = platform.system()

# get the environment variables
ISANXOT_RESOURCES         = os.environ['ISANXOT_RESOURCES']
ISANXOT_PYTHON_EXEC       = os.environ['ISANXOT_PYTHON_EXEC']
ISANXOT_SRC_HOME          = os.environ['ISANXOT_SRC_HOME']
ISANXOT_WFS_HOME          = os.environ['ISANXOT_WFS_HOME']

# Important: We have ignore the warnings because in MacOS appears the followinf messages:
# UserWarning: Could not import the lzma module. Your installed Python is incomplete. Attempting to use lzma compression will result in a RuntimeError.
ISANXOT_PYTHON_PARAMS     = "-Wignore"


if plat == 'Windows':   
    ISANXOT_LIB_COMMON        = f"{ISANXOT_RESOURCES}/src/libs/"
    ISANXOT_JAVA_EXEC         = f"{ISANXOT_RESOURCES}/exec/java/bin/java.exe"
    ISANXOT_DOT_EXEC          = f"{ISANXOT_RESOURCES}/exec/graphviz-2.50.0/bin/dot.exe"

elif plat == 'Darwin':
    ISANXOT_LIB_COMMON        = f"{ISANXOT_RESOURCES}/src/libs/"
    ISANXOT_JAVA_EXEC         = f"{ISANXOT_RESOURCES}/exec/java/bin/java"
    ISANXOT_DOT_EXEC          = f"{ISANXOT_RESOURCES}/exec/graphviz-2.50.0/bin/dot"
    
elif plat == 'Linux':
    ISANXOT_LIB_COMMON        = f"{ISANXOT_RESOURCES}/src/libs/"
    ISANXOT_JAVA_EXEC         = f"{ISANXOT_RESOURCES}/exec/java/bin/java"
    ISANXOT_DOT_EXEC          = f"{ISANXOT_RESOURCES}/exec/graphviz-2.50.0/bin/dot"
    