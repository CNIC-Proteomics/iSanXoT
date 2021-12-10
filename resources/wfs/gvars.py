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
ISANXOT_PYTHON_HOME       = os.environ['ISANXOT_PYTHON_HOME']
ISANXOT_PYTHON_EXEC       = os.environ['ISANXOT_PYTHON_EXEC']
ISANXOT_SRC_HOME          = os.environ['ISANXOT_SRC_HOME']

if plat == 'Windows':   
    ISANXOT_SNAKEMAKE_EXEC    = f"{ISANXOT_PYTHON_HOME}/Scripts/snakemake.exe"

    ISANXOT_LIB_COMMON        = f"{ISANXOT_RESOURCES}/src/cmds/libs/"
    ISANXOT_JAVA_EXEC         = f"{ISANXOT_RESOURCES}/exec/java/bin/java.exe"
    ISANXOT_DOT_EXEC          = f"{ISANXOT_RESOURCES}/exec/graphviz/bin/dot.exe"

    ISANXOT_STATS_GETVAR_PY   = f"{ISANXOT_SRC_HOME}/stats/getVariances.py"

elif plat == 'Darwin':
    ISANXOT_SNAKEMAKE_EXEC    = f"{ISANXOT_PYTHON_HOME}/bin/snakemake"

    ISANXOT_LIB_COMMON        = f"{ISANXOT_RESOURCES}/src/cmds/libs/"
    ISANXOT_JAVA_EXEC         = f"{ISANXOT_RESOURCES}/exec/java/bin/java"
    ISANXOT_DOT_EXEC          = f"{ISANXOT_RESOURCES}/exec/graphviz/bin/dot"
    
    ISANXOT_STATS_GETVAR_PY   = f"{ISANXOT_SRC_HOME}/stats/getVariances.py"

elif plat == 'Linux':
    ISANXOT_SNAKEMAKE_EXEC    = f"{ISANXOT_PYTHON_HOME}/bin/snakemake"

    ISANXOT_LIB_COMMON        = f"{ISANXOT_RESOURCES}/src/cmds/libs/"
    ISANXOT_JAVA_EXEC         = f"{ISANXOT_RESOURCES}/exec/java/bin/java"
    ISANXOT_DOT_EXEC          = f"{ISANXOT_RESOURCES}/exec/graphviz/bin/dot"
    
    ISANXOT_STATS_GETVAR_PY   = f"{ISANXOT_SRC_HOME}/stats/getVariances.py"
