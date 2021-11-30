# Steps how to work with iSanXoT

# Requierements

Building wheels for collected packages: datrie
  Building wheel for datrie (pyproject.toml): started
  Building wheel for datrie (pyproject.toml): finished with status 'error'
  ERROR: Command errored out with exit status 1:
   command: 'C:\Users\jmrodriguezc\Desktop\iSanXoT_forBuild\resources\exec\python\Scripts\python.exe' 'C:\Users\jmrodriguezc\Desktop\iSanXoT_forBuild\resources\exec\python\lib\site-packages\pip\_vendor\pep517\in_process\_in_process.py' build_wheel 'C:\cygwin64\tmp\tmp5rb7uhkw'
       cwd: C:\cygwin64\tmp\pip-install-1pjjafgm\datrie_2d08a4c497604c7f95ede5ef6da99f84
  Complete output (5 lines):
  running bdist_wheel
  running build
  running build_clib
  building 'datrie' library
  error: Microsoft Visual C++ 14.0 or greater is required. Get it with "Microsoft C++ Build Tools": https://visualstudio.microsoft.com/visual-cpp-build-tools/
  ----------------------------------------
  ERROR: Failed building wheel for datrie



# Create the frontend environment, create the python environment, and create the backend environment
## for windows

```
cd resources/env

./com.env.win.bat "{WRITE THE PYTHON EXECUTABLE}" "{WRITE THE FRONTEND PATH FOR ENV}"  "{WRITE THE BACKENDEND PATH FOR ENV}"
 <!-- set %PATH%=%PATH%;C:\Users\jmrodriguezc\iSanXoT\env\node&& ./com.env.win.bat "S:/U_Proteomica/UNIDAD/DatosCrudos/jmrodriguezc/projects/iSanXoT/env/python-3.9.7-win-x64/python.exe" "C:/Users/jmrodriguezc/iSanXoT/env" "S:/U_Proteomica/UNIDAD/DatosCrudos/jmrodriguezc/projects/iSanXoT/resources/exec"
 set %PATH%=%PATH%;C:\Users\jmrodriguezc\iSanXoT\env\node&& ./com.env.win.bat "S:/U_Proteomica/UNIDAD/DatosCrudos/jmrodriguezc/projects/iSanXoT/env/python-3.9.7-win-x64/python.exe" "C:/Users/jmrodriguezc/iSanXoT/env" "S:/U_Proteomica/UNIDAD/DatosCrudos/jmrodriguezc/projects/iSanXoT/resources/exec" -->


```
## for Mac

```
cd resources/env

./com.env.darwin.sh "{WRITE THE PYTHON EXECUTABLE}" "{WRITE THE FRONTEND PATH FOR ENV}"  "{WRITE THE BACKENDEND PATH FOR ENV}"
export PATH=/Users/proteomica/iSanXoT/env/node/bin:$PATH && ./com.env.darwin.sh /Users/proteomica/Desktop/iSanXoT_forBuild/env/python-3.9.7-darwin-x64/python3.9  /Users/proteomica/iSanXoT/env  /Users/proteomica/Desktop/iSanXoT_forBuild/resources/exec
```

## for Linux
```
cd resources/env

./com.env.linux.sh "{WRITE THE PYTHON EXECUTABLE}" "{WRITE THE FRONTEND PATH FOR ENV}"  "{WRITE THE BACKENDEND PATH FOR ENV}"
export PATH=/home/jmrc/iSanXoT/env/node/bin:$PATH && ./com.env.linux.sh /usr/local/bin/python3.9 /home/jmrc/iSanXoT/env /home/jmrc/projects/iSanXoT/resources/exec
```

# Package iSanXoT for ONLINE mode

## Package iSanXoT

## for Windows

Add the Node path into environment variable
```
Open CMD
SETX PATH %PATH%;C:\Users\jmrodriguezc\iSanXoT\env\node
Close CMD
```

Build iSanXoT
```
Open New CMD
"C:/Users/jmrodriguezc/iSanXoT/env/node/electron-builder"
```

## for Mac
{WRITE THE FRONTEND PATH FOR ENV}/node/bin/electron-builder
/Users/proteomica/iSanXoT/env/node/bin/electron-builder

## for Linux
{WRITE THE FRONTEND PATH FOR ENV}/node/bin/electron-builder
/home/jmrc/iSanXoT/env/node/bin/electron-builder


# Execute iSanXoT in debuging

## for windows
Open CMD
SET ISANXOT_MODE=debug&& "C:/Users/jmrodriguezc/iSanXoT/env/node/npm" start
IMPORTANT!! You have to write in this way:
=debug&& (without space)

## for Mac
export ISANXOT_MODE=debug && export PATH=/Users/proteomica/iSanXoT/env/node/bin:$PATH && /Users/proteomica/iSanXoT/env/node/bin/npm start 

## for Linux
export ISANXOT_MODE=debug && export PATH=/home/jmrc/iSanXoT/env/node/bin:$PATH && /home/jmrc/iSanXoT/env/node/bin/npm start


 git push origin refs/heads/0.4.0:refs/heads/0.4.0

