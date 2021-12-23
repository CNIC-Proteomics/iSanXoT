# Steps how to create an environment for iSanXoT

This documentation is for iSanXoT developers.


## Clone the repository

1) Clone the iSanXoT repository
```
git clone https://github.com/CNIC-Proteomics/iSanXoT.git
```
2) Access to folder
```
cd iSanXoT
```

## Execute iSanXoT in debug mode for Windows distribution

### Create the python environment: Install just python in the resource folder

1) Create python folder
```
mkdir "S:\U_Proteomica\UNIDAD\DatosCrudos\jmrodriguezc\projects\iSanXoT\env\python\Python-3.9.7"
```

2) Install just python in the resource folder

  2.1) Customize installation:

![Customize installation](../docs/env/images/python_installation_1.png "Customize installation")
    
  2.2) Optional features:
  Without documentation, tck, ONLY pip

![Optional features](../docs/env/images/python_installation_2.png "Optional features")

  2.3) Choose the path:
  Do it in "env/python-3.9.7-win-x64"

![Choose the path](../docs/env/images/python_installation_3.png "Choose the path")

3) Copy the cached installation of python
```
cp -r env/python/Python-3.9.7  app/resources/exec/python-3.9.7-win-x64
```

### Create the frontend environment

1) Execute:
```
cd env
set %PATH%=%PATH%;C:\Users\jmrodriguezc\iSanXoT\env\node&& com.env.win.bat "S:\U_Proteomica\UNIDAD\DatosCrudos\jmrodriguezc\projects\iSanXoT\resources\exec\python-3.9.7-win-x64\python.exe" "C:\Users\jmrodriguezc\iSanXoT\env"
```
Note: You have to write in this way:
...\env\node&& (without space)
Note: The frontend folder (node) has to be in local because otherwise the "OpenDevTools" does not work.

4) Add the Node path into environment variable:
Open CMD
```
setx PATH "%PATH%;C:\Users\jmrodriguezc\iSanXoT\env\node"
```
Close CMD

### Build iSanXoT
1) Copy the cached installation of python
```
cp -r env/python/Python-3.9.7  app/resources/exec/python-3.9.7-win-x64
```
Important note: You have to remove the previous release; otherwise the new release will be too big
```
rm -rf releases
```
2) Build iSanXoT
```
cd "S:\U_Proteomica\UNIDAD\DatosCrudos\jmrodriguezc\projects\iSanXoT"

"C:\Users\jmrodriguezc\iSanXoT\env\node\electron-builder"
```

### Execute iSanXoT in debug mode
Open CMD
```
set ISANXOT_MODE=debug&& set ISANXOT_DEV=local&& "C:\Users\jmrodriguezc\iSanXoT\env\node\npm" start
```
Note: You have to write in this way:
=debug&& (without space)

### In the case there are new python packages: Download the Python packages
1) Extract the Python packages
```
"S:\U_Proteomica\UNIDAD\DatosCrudos\jmrodriguezc\projects\iSanXoT\app\resources\exec\python-3.9.7-win-x64\Scripts\pip3.9.exe" freeze > app/resources/env/packages/win-x64/requirements.txt

cd app/resources/env/packages/win-x64
"S:\U_Proteomica\UNIDAD\DatosCrudos\jmrodriguezc\projects\iSanXoT\app\resources\exec\python-3.9.7-win-x64\Scripts\pip3.9.exe" download -r requirements.txt

ls -1 > requirements_local.txt
```


---


## for MacOS distribution

### Create the python environment: Install just python in the resource folder

1) Install just python in the resource folder

    2.1) Uncompress python
    ```
    cd env/python
    tar -xvf Python-3.9.7.tgz
    cd Python-3.9.7
    ```
    2.2) Configure python to install in user folder
    ```
    ./configure --prefix=/Users/proteomica/projects/iSanXoT/app/resources/exec/python-3.9.7-darwin-x64
    ```
    2.2) Make
    ```
    make
    ```
    2.3) Make install
    ```
    make install
    ```

### Create the frontend environment

1) Execute program that creates the frontend enviroment
```
cd env
export PATH=/Users/proteomica/projects/iSanXoT/env/node/node-darwin-x64/bin:$PATH && ./com.env.darwin.sh /Users/proteomica/projects/iSanXoT/app/resources/exec/python-3.9.7-darwin-x64/bin/python3  /Users/proteomica/projects/iSanXoT/env/node
```

### Build iSanXoT

1) Clean folders
```
rm -rf app/env app/exec
```

2) Re-install python
```
cd env/python/Python-3.9.7
make install
```

3) Execute the program that builds the packages
```
cd app
export PATH=/Users/proteomica/projects/iSanXoT/env/node/node-darwin-x64/bin:$PATH && /Users/proteomica/projects/iSanXoT/env/node/node-darwin-x64/bin/electron-builder
```

### Execute iSanXoT in debug mode

1) Copy the files to create the backend environment
```
mkdir app/resources/env && cp -r env/installer.py env/core.py env/packages/pip-21.3.1.tar.gz env/packages/setuptools-59.6.0.tar.gz env/packages/requirements_backend_darwin-x64.txt app/resources/env/.

mkdir app/resources/env/packages && cp -r env/packages/darwin-x64 app/resources/env/packages/.
```

2) Execute iSanXoT in debug mode
```
cd app
export ISANXOT_MODE=debug && export ISANXOT_DEV=local && export PATH=/Users/proteomica/projects/iSanXoT/env/node/node-darwin-x64/bin:$PATH && /Users/proteomica/projects/iSanXoT/env/node/node-darwin-x64/bin/npm start 
```

Note: Open iSanXoT application in debug mode
```
cd /Applications
export ISANXOT_MODE=debug && open -a "iSanXoT.app"
```

### In the case there are new python packages: Download the Python packages

1) Extract the Python packages
```
/Users/proteomica/projects/iSanXoT/resources/exec/python-3.9.7-darwin-x64/bin/pip3 freeze > resources/env/packages/darwin-x64/requirements.txt

cd resources/env/packages/darwin-x64
/Users/proteomica/projects/iSanXoT/resources/exec/python-3.9.7-darwin-x64/bin/pip3 download -r requirements.txt

ls -1 > requirements_local.txt
```


---


## for Linux distribution

### Create the python environment: Install just python in the resource folder

1) Install just python in the resource folder

    1.1) Uncompress python
    ```
    cd env/python
    tar -xvf Python-3.9.7.tgz
    cd Python-3.9.7
    ```
    1.2) Configure python to install in user folder
    ```
    ./configure --prefix=/home/jmrc/projects/iSanXoT/app/resources/exec/python-3.9.7-linux-x64
    ```
    1.2) Make
    ```
    make
    ```
    1.3) Make install
    ```
    make install
    ```

### Create the frontend environment

1) Execute program that creates the frontend enviroment
```
cd env
export PATH=/home/jmrc/projects/iSanXoT/env/node/node-linux-x64/bin:$PATH && ./com.env.linux.sh /home/jmrc/projects/iSanXoT/app/resources/exec/python-3.9.7-linux-x64/bin/python3 /home/jmrc/projects/iSanXoT/env/node
```

### Build iSanXoT
1) Clean folders
```
rm -rf app/env app/exec
```

2) Re-install python
```
cd env/python/Python-3.9.7
make install
```

3) Execute the program that builds the packages
```
/home/jmrc/projects/iSanXoT/env/node/node-linux-x64/bin/electron-builder
```

### Execute iSanXoT in debug mode

1) Copy the files to create the backend environment
```
mkdir app/resources/env && cp -r env/installer.py env/core.py env/packages/pip-21.3.1.tar.gz env/packages/setuptools-59.6.0.tar.gz env/packages/requirements_backend_linux-x64.txt app/resources/env/.

mkdir app/resources/env/packages && cp -r env/packages/linux-x64 app/resources/env/packages/.
```

2) Execute iSanXoT in debug mode
```
cd app
export ISANXOT_MODE=debug && export ISANXOT_DEV=local && export PATH=/home/jmrc/projects/iSanXoT/env/node/node-linux-x64/bin:$PATH && /home/jmrc/projects/iSanXoT/env/node/node-linux-x64/bin/npm start
```

### In the case there are new python packages: Download the Python packages

1) Extract the Python packages
```
/Users/proteomica/projects/iSanXoT/resources/exec/python-3.9.7-linux-x64/bin/pip3 freeze > resources/env/packages/linux-x64/requirements.txt

cd resources/env/packages/linux-x64
/Users/proteomica/projects/iSanXoT/resources/exec/python-3.9.7-linux-x64/bin/pip3 download -r requirements.txt

ls -1 > requirements_local.txt
```
