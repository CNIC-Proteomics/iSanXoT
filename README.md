# iSanXoT

This repository contains the source code and the distribution files for the iSanXoT application.

This application executes several kind of workflows for **quantitative high-throughput proteomics**, **systems biology** and the **statistical analysis**, **integration and comparison of experiments**.

iSanXoT was developed by the Cardiovascular Proteomics Lab/Proteomic Unit at **The National Centre for Cardiovascular Research** (CNIC, [https://www.cnic.es](https://www.cnic.es/)).

This application is licensed under a **Creative Commons Attribution-NonCommercial-NoDerivs 4.0 Unported License**
https://creativecommons.org/licenses/by-nc-nd/4.0/ (for more detail, read the [LICENSE](LICENSE.md) file).


## Download 

The multiple releases are available in the "release" section, located in the following link:

https://github.com/CNIC-Proteomics/iSanXoT/releases


## Installation

### Available operating systems

iSanXoT maintains the following operating systems and architectures and may add additional ones in the future:

+ **Windows 10 Pro** (x64)
+ **MacOs High Sierra** (10.13.6)
+ **Ubuntu 20.04** (x64)

For more details, read the [INSTALL](INSTALL.md) file.

### Windows distribution

#### Requirements for Windows distribution

iSanXoT uses Windows Python packages which needs via the SDK to build code. Thus, Microsoft Visual C++ 14.0 or greater is required. On Linux and Mac, the C++ libraries are installed with the compiler.

Get the "Microsoft C++ Build Tools" by one of these choices:

- from an offline installer: [vs_BuildTools.exe](env/vs_BuildTools.exe) (Recommended).
- from [Microsoft Build Tools for Visual Studio] (https://visualstudio.microsoft.com/thank-you-downloading-visual-studio/?sku=BuildTools&rel=16)

When the Microsoft Build Tools is opened, select:

    Workloads → Desktop development with C++
    
Then for Individual Components select only:

    - Windows 10 SDK
    - C++ x64/x86 build tools (MSVC - VS)

More references:

https://www.scivision.co/python-windows-visual-c++-14-required/

### Installation on Windows

The iSanXoT application for Windows distribution is packaged in a NSIS Launcher (exe file).

For more details, read the [Windows distribution](INSTALL.md#windows-distribution) section in the INSTALL file.

### MacOS distribution

The iSanXoT application for macOS distribution is packaged in a DMG container.

For more details, read the [macOS distribution](INSTALL.md#macos-distribution) section in the INSTALL file.

### Linux distribution

The iSanXoT application for Linux distribution is packaged in an AppImage container.

For more details, read the [linux distribution](INSTALL.md#linux-distribution) section in the INSTALL file.


# Get started

---

<!-- ### [⇐ Previous](README.md) | [Next ⇒](1-environment.md) -->
