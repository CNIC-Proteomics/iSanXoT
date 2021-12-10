# Steps how to create an environment for iSanXoT

This documentation is for iSanXoT developers.



## Create the frontend environment, create the python environment, and create the backend environment
### for windows


1) Install Python

  1.1) Customize installation:

![Customize installation](../docs/env/images/python_installation_1.png "Customize installation")
    
  1.2) Optional features:
  Without documentation, tck, ONLY pip

![Optional features](../docs/env/images/python_installation_2.png "Optional features")

  1.3) Choose the path:
  Do it in "env/python-3.9.7-win-x64"

![Choose the path](../docs/env/images/python_installation_3.png "Choose the path")

2) Execute:
```
cd env
set %PATH%=%PATH%;C:\Users\jmrodriguezc\iSanXoT\env\node&& com.env.win.bat "S:/U_Proteomica/UNIDAD/DatosCrudos/jmrodriguezc/projects/iSanXoT/env/python-3.9.7-win-x64/python.exe" "S:/U_Proteomica/UNIDAD/DatosCrudos/jmrodriguezc/projects/iSanXoT/env/node" 
```

### for Mac

1) Install Python in the path. Without documentation, tck, ONLY pip => env/python-3.9.7-darwin-x64
2)
```
cd env
export PATH=/Users/proteomica/iSanXoT/env/node/bin:$PATH && ./com.env.darwin.sh /Users/proteomica/Desktop/iSanXoT_forBuild/env/python-3.9.7-darwin-x64/python3.9  /Users/proteomica/iSanXoT/env
```

### for Linux

1) Install Python in the path. Without documentation, tck, ONLY pip => env/python-3.9.7-linux-x64
2)
```
cd env
export PATH=/home/jmrc/iSanXoT/env/node/bin:$PATH && ./com.env.linux.sh /usr/local/bin/python3.9 /home/jmrc/iSanXoT/env
```

## Build iSanXoT

### for Windows

Add the Node path into environment variable.
1) Open CMD
2)
```
SETX PATH %PATH%;C:\Users\jmrodriguezc\iSanXoT\env\node
```
3) Close CMD
4) Open New CMD
```
"C:/Users/jmrodriguezc/iSanXoT/env/node/electron-builder"
```

### for Mac
{WRITE THE FRONTEND PATH FOR ENV}/node/bin/electron-builder
/Users/proteomica/iSanXoT/env/node/bin/electron-builder

### for Linux
{WRITE THE FRONTEND PATH FOR ENV}/node/bin/electron-builder
/home/jmrc/iSanXoT/env/node/bin/electron-builder


## Execute iSanXoT in debug mode

### for windows
1) Open CMD
2)
```
SET ISANXOT_MODE=debug&& "C:/Users/jmrodriguezc/iSanXoT/env/node/npm" start
```
Note: You have to write in this way:
=debug&& (without space)

### for Mac
1)
```
export ISANXOT_MODE=debug && export PATH=/Users/proteomica/iSanXoT/env/node/bin:$PATH && /Users/proteomica/iSanXoT/env/node/bin/npm start 
```

### for Linux
1)
```
export ISANXOT_MODE=debug && export PATH=/home/jmrc/iSanXoT/env/node/bin:$PATH && /home/jmrc/iSanXoT/env/node/bin/npm start
```

