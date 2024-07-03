___
## 1.2.13
```
DATE: 2024_07
```

### Highlights

+ New version for the ProteinAssigner (v5). In this version, the changes are:
	- The parameter file has been transformed to INI format. This change was made because the ProteinAssigner is integrated into the PTM-workflow, and a consensus parameter file with the same format is required.
	- A preliminary filter for redundant proteins identified has been developed. This filter is applied before any other operation by the ProteinAssigner.

+ New version of klibrate (v1.20):
	- Savitzky-Golay algortihm for smoothing has been included.

+ Fixing a bug in the mz extraction for experiments with high resolution (greater than 30K), in the Quant package.

### Changes in the Graphical User Interface

+ Updated documentation.

+ Modify the CNIC adapter to accept the new version of ProteinAssigner, which includes the preliminary filter.
	A new parameter has been added: *"Preliminary Regex filter before any operation"*, applicable in both FASTA and column modes.

### Changes in the Code Workflow

+ Fixing a bug in reporter:
	- The X'inf and Winf variable are retrieved correctly.
	- Possible bug caused by dictionaries in Python.

+ Fixing a bug in the mz extraction for experiments with high resolution (greater than 30K), in the Quant package.

+ New version of klibrate (v1.20) has been developed:
	- Savitzky-Golay algortihm for smoothing has been applied. New parameters have been added:
```
   -S, --no-smoothing  Do not apply the Savitzky-Golay smoothing algorithm. It 
                       is applied by default.
   -t, --smoothing-window
                       The window size for the Savitzky-Golay smoothing 
                       algorithm. A larger window size will result in stronger 
                       smoothing. The window length must be less than or equal 
                       to the size of input. By default is length of integrated elements.
   -T, --smoothing-polynomial
                       The polynomial order for the Savitzky-Golay smoothing 
                       algorithm to fit the samples. A higher polynomial order 
                       can capture more complex patterns but may also introduce 
                       more artifacts.
```


___
## 1.2.12
```
DATE: 2023_12
```

### Highlights

+ Fixing a bug in the 'New Project' window: The modal parameter for ElectronJS does not work in MacOSX version.

+ Customize the context menu as the Copy and Paste commands do not work correctly in the MacOSX version.

+ Open the processed project from the 'Project logs' table.

### Changes in the Graphical User Interface

+ Updated documentation.


### Changes in the Code Workflow


___
## 1.2.11
```
DATE: 2023_09
```

### Highlights

+ *sanxotsieve* has a new algorithm for tagging outliers based on a percentage. By default, the 20%.

### Changes in the Graphical User Interface


### Changes in the Code Workflow

+ Fixing a bug in createLevels: If the experiment header does not exist in the ID-q, then report a message log and retrieve an empty dataframe. If the task-table does not contain an experiment value, then do not filter.

+ Fixing a bug in createRels: All the columns read in the table files should be treated as 'string' data type. It does not accept float or integer columns.

___
## 1.2.10
```
DATE: 2023_08
```

### Highlights

+ Fixing a bug calling the *sanxotsieve*

### Changes in the Graphical User Interface


### Changes in the Code Workflow


___
## 1.2.9
```
DATE: 2023_07
```

### Highlights

+ *sanxotsieve* has a new algorithm for tagging outliers based on a percentage.

### Changes in the Graphical User Interface

+ The parameter "by-percentage" mode in *sanxotsieve* has been added in the iSanXoT modules.

### Changes in the Code Workflow

+ Bug fixed: The input files from the createRels and createLevels programs weren't cached correctly.

+ The selection of the type of search engine is now not mandatory. If the search engine is not detected, then we won't preprocess any columns.

+ Accept any type of experiment (iTRAQ4, iTRAQ8); however, there is no correction.

+ The one-to-one mode from *sanxotsieve* has been deprecated.

+ *sanxotsieve* has a new algorithm for tagging outliers based on a percentage.
In each cycle, the outliers are removed based on a given percentage of each higher element (with outliers).

+ The "one-per-higher" mode in *sanxotsieve* has been redeveloped.

___
## 1.2.8
```
DATE: 2023_05
```

### Highlights

+ iSanXoT accepts projects with a huge number of experiments.

+ The CNIC adaptor also includes the ProteinAssigner using the FASTA mode with the complete params (regex, len option, etc).

+ The addQuantification module of CNIC adaptor accepts more types of TMTs (TMT16 and TMT18) for the isotopic correction.

+ The REPORT module can filter OR conditions and it also merges multiple report tables at the same time.

+ New documentation for the workflow samples.

### Changes in the Graphical User Interface


### Changes in the Code Workflow

___
## 1.2.7
```
DATE: 2023_01
```

### Highlights

+ Improve the User Guide documentation in the iSanXoT help:
	- Update the documentation.
	- Divide by sections the documentation in multiple files.

+ Update the iSanXoT Wiki:
	- Add the user guide files.
 	- Add the Case studies.
	- Add the adaptor cases.

+ NORCOMBINE:
	- Changes in the output file names.
	- Cardenio will recognize the experiment by the name of sample.

### Changes in the Graphical User Interface

+ Improve the User Guide documentation in the iSanXoT help.
		renamed:    app/app/User_Guide.html -> app/app/User_Guide.htm
		modified:   app/app/User_Guide_files/image002.jpg
		modified:   app/app/User_Guide_files/image003.png
		modified:   app/app/User_Guide_files/image004.jpg
		modified:   app/app/User_Guide_files/image005.png
		modified:   app/app/User_Guide_files/image006.png
		modified:   app/app/User_Guide_files/image007.png
		modified:   app/app/User_Guide_files/image009.png
		modified:   app/app/User_Guide_files/image010.png
		modified:   app/app/User_Guide_files/image013.png
		modified:   app/app/User_Guide_files/image014.png
		modified:   app/app/User_Guide_files/image019.png
		modified:   app/app/User_Guide_files/image020.png
		modified:   app/app/User_Guide_files/image023.png
		modified:   app/app/User_Guide_files/image024.png
		modified:   app/app/User_Guide_files/image027.png
		modified:   app/app/User_Guide_files/image029.png
		modified:   app/app/User_Guide_files/image031.png
		modified:   app/app/User_Guide_files/image033.png
		modified:   app/app/User_Guide_files/image036.png
		modified:   app/app/User_Guide_files/image039.png
		modified:   app/app/User_Guide_files/image040.png
		modified:   app/app/User_Guide_files/image041.png
		modified:   app/app/User_Guide_files/image044.png
		modified:   app/app/User_Guide_files/image045.png
		modified:   app/app/User_Guide_files/image046.png
		modified:   app/app/User_Guide_files/image047.png
		modified:   app/app/User_Guide_files/image048.png
		modified:   app/app/User_Guide_files/image049.png
		modified:   app/app/User_Guide_files/image050.png
		modified:   app/app/User_Guide_files/image051.png
		modified:   app/app/renderer-process/imports.js
		deleted:    app/app/sections/helps/help_cmds.html
		deleted:    app/app/sections/helps/help_get-started.html
		deleted:    app/app/sections/helps/help_intro.html
		deleted:    app/app/sections/helps/help_wf-basic.html
		deleted:    app/app/sections/helps/help_wf-lblfree.html
		deleted:    app/app/sections/helps/help_wf-ptm.html

+ LEVEL_CREATOR: Accepts the following operation for the ratio denominator: IS = if( or(count(a1…a4)=0, count(b1…b4)=0), '', Average(average(a1…a4), average(b1…b4)))
	[Intensity A_01 , Intensity A_02 , Intensity A_03 , Intensity A_04] , [Intensity B_01 , Intensity B_02 , Intensity B_03 , Intensity B_04]
		modified:   app/resources/src/cmds/createLevels.py

### Changes in the Code Workflow

+ Come back in the 'problem': Fix a problem in ProteinAssigner when the pandas does not interpreted the Protein Accessions column as string.
		renamed:    app/resources/src/cmds/extractQuant.py -> app/resources/src/cmds/extractquant.py
		modified:   app/resources/src/cmds/ProteinAssigner_v3.py

+ Reducing the path in the log report.
		modified:   app/resources/wfs/table2cfg.py

+ NORCOMBINE:
	- Changes in the file names.
		modified:   app/resources/wfs/tpl_commands/norcombine.yaml
	- Cardenio will recognize the experiment by the name of sample.
		modified:   app/resources/src/cmds/createCardenioTags.py

+ Add the option to have multiple samaples in the inputs and the outpus.
		modified:   app/resources/wfs/table2cfg.py


___
## 1.2.6-cnic
```
DATE: 2022_10
```

### Highlights

+ iSanXoT is multiprocessing when the '*' (asterisk) is within task table.

+ Improve the log tables.

+ Important!! The REPORT module has changed. Now the module discards levels that we don't want to show. The new column called 'Headers of columns to eliminate'.

### Changes in the Graphical User Interface

+ Improve the log tables:
    	modified:   app/app/renderer-process/logger.js

+ Include (again) the killed button in the Process page:
		modified:   app/app/assets/css/main.css
		modified:   app/app/processes.html
		modified:   app/app/renderer-process/executor.js
		modified:   app/app/renderer-process/imports.js
		modified:   app/app/renderer-process/logger.js
		modified:   app/app/renderer-process/processor.js
		modified:   app/app/renderer-process/sessioner.js

+ REPORT: Now the module discards levels that we don't want to show. The new column called 'Headers of columns to eliminate'.
		modified:   app/resources/src/cmds/reporter.py
		modified:   app/resources/wfs/commands.json
		modified:   app/resources/wfs/tpl_commands/report.yaml

+ LOG: Display in the project log table the step that gets the variance statistics.

### Changes in the Code Workflow

+ iSanXoT is multiprocessing when the '*' (asterisk) is within task table:
		modified:   app/resources/src/libs/common.py
		modified:   app/resources/wfs/commands.json
		modified:   app/resources/wfs/mysnake.py
		modified:   app/resources/wfs/table2cfg.py
		modified:   app/resources/wfs/tpl_commands/create_idq.yaml
		modified:   app/resources/wfs/tpl_commands/get_idstats.yaml
		modified:   app/resources/wfs/tpl_commands/integrate.yaml
		modified:   app/resources/wfs/tpl_commands/level_calibrator.yaml
		modified:   app/resources/wfs/tpl_commands/level_creator.yaml
		deleted:    app/resources/wfs/tpl_commands/level_creator_wpp_sbt.yaml
		deleted:    app/resources/wfs/tpl_commands/level_creator_wppg_sbt.yaml
		deleted:    app/resources/wfs/tpl_commands/level_creator_wspp_sbt.yaml
		deleted:    app/resources/wfs/tpl_commands/level_creator_wsppg_sbt.yaml
		modified:   app/resources/wfs/tpl_commands/norcombine.yaml
		modified:   app/resources/wfs/tpl_commands/ratios_int.yaml
		modified:   app/resources/wfs/tpl_commands/rels_creator.yaml
		modified:   app/resources/wfs/tpl_commands/report.yaml
		modified:   app/resources/wfs/tpl_commands/sanson.yaml
		modified:   app/resources/wfs/tpl_commands/sbt.yaml
		modified:   app/resources/wfs/tpl_commands/wpp_sbt.yaml
		modified:   app/resources/wfs/tpl_commands/wppg_sbt.yaml
		modified:   app/resources/wfs/tpl_commands/wspp_sbt.yaml
		modified:   app/resources/wfs/tpl_commands/wsppg_sbt.yaml
		modified:   app/app/renderer-process/projector.js

+ REPORT: The REPORT module has changed. Now the module discards levels that we don't want to show. The new column called 'Headers of columns to eliminate'.
		modified:   app/resources/src/cmds/reporter.py
		modified:   app/resources/wfs/commands.json
		modified:   app/resources/wfs/tpl_commands/report.yaml

+ Allow that tabs could be visibles or not.
		modified:   app/app/renderer-process/bodied.js
		modified:   app/resources/wfs/commands.json


___
## 1.2.5-cnic
```
DATE: 2022_10
```

### Highlights


### Changes in the Graphical User Interface

+ RATIOS_INT:
	- Rename column names.

### Changes in the Code Workflow

+ reporter.py:
	- Fixing the concatenation of REL columns.
	- Fixing a problem getting the maximum number per integration for the 'n_' columns.

___
## 1.2.4-cnic
```
DATE: 2022_09
```

### Highlights

+ Change the license to **Creative Commons Attribution-NoDerivatives 4.0 International (CC BY-ND 4.0) License**

+ The modules: WSPP-SBT, WSPPG-SBT, WPP-SBT, and WPPG-SBT are not compatible with older versiones.

+ The CNIC adaptor is not compatible with older versiones.

### Changes in the Graphical User Interface

+ LEVEL_CREATOR: Comments from Jesús: Experiment column. The program should work when nothing is put in Experiment, taking all the data from the table. Ideally, there should not even need to be an experiment column when you only work with one experiment, so that if the program does not find the column, it works with the whole file and that's it. The reason for this is that when there is no experiment column the file contains only one experiment and therefore there is no need for that column.

+ WSPP-SBT: discard the integration; peptide2peptideall.

+ WSPPG-SBT: discard the integration; peptide2peptideall, protein2proteinall.

+ WPP-SBT: discard the integration; peptide2peptideall.

+ WPPG-SBT: discard the integration; peptide2peptideall, protein2proteinall.

+ Remove the carriage return from the columns in the cnic adaptor.

+ The creation of 'Experiment' column is not mandatory in the CNIC adaptor.

+ The 'addQuant' of CNIC adaptor works pairing the 'Spectrum File' and the 'mzML'. The file name has to be equal. Therefore, the 'Spectrum_File' column is required to obtain the quantification from the mzML files.

### Changes in the Code Workflow

+ createIDq: Now the adaptors works on the IDq provided by the user.

+ getKlibrateVals: Uncomment a debugging sentence.

+ createLevels: Improved the program to accept the whole task-table, read one time the input file, and then, execute each row in parallel internally.
  The program should work when nothing is within Experiment column.

+ createRels:
	- Improve the program to accept the whole task-table, read one time the input file, and then, execute each row in parallel internally.
	- Discard 'nan' values one one row has the Third column empty.
	- Take into account only the two first columns to check NaN values.

+ Tpl_Commands:
	- The name of log files have changed:
		- SanxotSieve log name changes to '_infoSSieve.txt'
		- SanXoT (the second) log name changes to '_infoSanXoT.txt'		
		Note: the first SanXoT still reporting the varaince and log in the '_variance.txt'
		- Klibrate log name changes to '_infoK.txt'

+ getIntegrationVals:
	- Get the number of excluded elements from the 'excluded' value in the FDR column.

+ reporter:
	- Drop rows when the tags contains the 'out' word.
	- If the 'n_' columns exist, get the maximum number per integration.
	- Fixing the concatenation of REL columns.

+ We have created some case studies to ilustrade the type of workflows:
	- WSPP_NORCOMBINE_RATIOS_SBT: Work by González-Amor M, et al. Cardiovasc Res. 2021
		* Report using the asterisk (the jack of all trades)
			- Npep2prot_Quanprot: Zq, FDRq, Nq(npeptides/prot)
		* Report using the asterisk (the jack of all trades) (1 sample)
			- Npep2prot_Quanprot: Zq, FDRq, Nq(npeptides/prot)
			- Nprot2cat_Quancat: Zc, FDRc, Nc(nprots/cat)
			- Zprot2cat_Quanprot_Quancat: Zq, Zc
		* Report produced by the merge of the sample reports with the ratios sample report (SBT)
	- WSPP-SBT: Work by García-Marqués F, et al. Mol Cell Proteomics. 2016:
		* Biology Systems: WSPP-SBT
		* Report using the asterisk (the jack of all trades)
			- Npep2prot_Quanprot: Zq, FDRq, Nq(npeptides/prot)
			- Nprot2cat_Quancat: Zc, FDRc, Nc(nprots/cat)
	- WSPP_PTM: Work by Bonzon-Kulichenko E, et al. J Proteomics. 2020
		* WSPP step by step using asterisks (the jack of all trades)
		* Report using the asterisk (the jack of all trades)
			- Npep2prot_Quanprot: Zq,  FDRq, Nq(npeptides/prot)
			- Npep2prot_Quanprot: Zpq, FDRpq, Ns(nscans/pep)
	- WSPP_LabelFree: Work by ProteoRed and Navarro , et al. Nature Biotech. 2016
		* WSPP step by step without asterisks (the jack of all trades)
		* Report:
			- Npep2prot_Quanprot: Zq, Nq(npeptides/prot)

___
## 1.0.2
```
DATE: 2022_05
```

### Changes in the Graphical User Interface

+ Adaptor: Bug fixed: the window in the adaptor was not displayed correctly.

+ Adaptor: Allow the read of large files size.

### Changes in the Code Workflow

+ RELS_CREATOR: Now the delimiter in category files is '//'.

___
## 1.0.1
```
DATE: 2022_05
```

### Highlights

+ New general adapter to handle the results from proteomics pipelines: TPP, FragPipe, MaxQuant, Proteome Discoverer, etc.

+ New CNIC adapter to habdles the results from search engines and to calculate the pRatio, add the quantificacions, and calculate the most probable protein.

+ LEVEL_CALIBRATOR accepts the K-constant, the variance, and 'More params'

+ iSanXoT Wiki: https://github.com/CNIC-Proteomics/iSanXoT/wiki

### Changes in the Graphical User Interface

+ New General Adapter to handle the results from proteomics pipelines: TPP, FragPipe, MaxQuant, ProteomeDiscoverer, etc.

+ New CNIC adapter to habdles the results from search engines and to calculate the pRatio, add the quantificacions, and calculate the most probable protein.

+ We have created some case studies to ilustrade the type of workflows:
	- WSPP: Work by González-Amor M, et al. Cardiovasc Res. 2021
		* WSPP step by step without asterisks (the jack of all trades)
		* Report:
			- Npep2prot_Quanprot: Zq, Nq(npeptides/prot)
	- WSPP_NORCOMBINE_RATIOS_SBT: Work by González-Amor M, et al. Cardiovasc Res. 2021
		* Report using the asterisk (the jack of all trades)
			- Npep2prot_Quanprot: Zq, FDRq, Nq(npeptides/prot)
		* Report using the asterisk (the jack of all trades) (1 sample)
			- Npep2prot_Quanprot: Zq, FDRq, Nq(npeptides/prot)
			- Nprot2cat_Quancat: Zc, FDRc, Nc(nprots/cat)
			- Zprot2cat_Quanprot_Quancat: Zq, Zc
		* Report produced by the merge of the sample reports with the ratios sample report (SBT)
	- WSPP-SBT: Work by García-Marqués F, et al. Mol Cell Proteomics. 2016:
		* Biology Systems: WSPP-SBT
		* Report using the asterisk (the jack of all trades)
			- Npep2prot_Quanprot: Zq, FDRq, Nq(npeptides/prot)
			- Nprot2cat_Quancat: Zc, FDRc, Nc(nprots/cat)
			- Zprot2cat_Quanprot_Quancat: Zq, Zc
	- WSPP_PTM: Work by Bonzon-Kulichenko E, et al. J Proteomics. 2020
		* WSPP step by step using asterisks (the jack of all trades)
		* Report using the asterisk (the jack of all trades)
			- Npep2prot_Quanprot: Zq,  FDRq, Nq(npeptides/prot)
			- Npep2prot_Quanprot: Zpq, FDRpq, Ns(nscans/pep)

+ 'More params", the 'more params' has been improved.

+ LEVEL_CALIBRATOR accepts the K-constant, the variance, and 'More params'.

### Changes in the Code Workflow

+ TABLETOCFG:
	- Fixing the file that forces the variance in the integrations.
	- Print all processes but forced or not.

+ SANSON: Fixing a bug in the filter of SANSON. The filter needs the parenthsis:
	([FDR] < 0.05) & ([n_rel] >= 10) & ([n_rel] <= 100) 

+ Integrations: force the parameters and create a file with the variance when the vatiance has been forced by the user in the task-table.

+ RELS_CREATOR: Admits the ID-q.tsv files as default.

+ New general adapter to handle the results from proteomics pipelines: TPP, FragPipe, MaxQuant, Proteome Discoverer, etc.

+ Improved the program that reports the integrated variances.

+ New program that reports the K-constant and the graphs of calibration.

+ New program that retrieves the times of workflow execution.

+ Fixing a problem with the Linux and Mac distribution.

Comments:

+ In Create new project, in the first menu you should put Name of the Project Folder and the second Path to locate the Project Folder.

+ In Open Project, change to Open Project Folder.

+ In project logs table it should be indicated (press the process to see the workflow logs).

+ In workflow logs it should be indicated (press the command to see the command logs).

+ Instead of Start, put Save and Run.

+ Menu name to Project.

+ Change the 'Adapter' tab to 'Input File'.

+ The getVariances program will return "sample/integration/Variance/TotNElems/ElemExcluded/IntegratedNElems..."




___
## 0.4.4
```
DATE: 2022_02
```

### Highlights

+ PROTEIN_ASSIGNER is the new Module for CNIC Adaptors.

+ The REPORT module can retrieve the X'inf and Winf from the _lowerNormW files.

### Changes in the Graphical User Interface

+ We have included more details in the short description for the SBT module and RATIOS module.

+ Create general adaptors for the search engines: Proteome Discoverer, MSFragger, Comet and MaxQuant.

+ Fixing a minor problem loading the adaptors.

+ PROTEIN_ASSIGNER is the new Module for CNIC Adaptors.

### Changes in the Code Workflow

+ Minor changes: changes the descrioption of ratios command.

+ Now, the modules of adaptors are independent.

+ TABLE2CFG: fixing a problem with the unique function. We want the unique list but without sort.

+ General Adaptors for Proteome Discoverer, MSFragger, Comet, and MaxQuant:
	- These adaptors only create the columns: Experiment, Scan_Id, and Peptide_Id.
	- The calculation of Peptide_Id is without the DeltaMass forgetting the unimod file.

+ CNIC Specific Adaptors:
	- These adaptors have the FDR calculation including the cXCorr (for PD).
	- There is a new Module for CNIC Adaptors: ProteinAssigner 

+ KLIBRATE: When the number of cycles in calibrate is exceeded, we can use k=600, var=0.04 by default. This is based on the values from PESA project:
<img src="docs/images/changelog/k_v_PESA.png">

+ REPORT:
	- Bug fixed: the program does not retrieve the Xsup value.
	- The program can retrieve the X'inf and Winf from the _lowerNormW files.

___
## 0.4.3
```
DATE: 2022_02
```

### Changes in the Code Workflow

+ Force the execution of Main-Input adaptor.

+ Mysnake: we have developed a new way to obtain the list of processes.

___
## 0.4.2
```
DATE: 2022_01
```

### Highlights


### Changes in the Graphical User Interface

+ The Adaptors tab has been renamed to 'Adaptor'.

+ Fixing a bug in Comet Adaptor.

+ Approximation to fix the problem when the administrator wants to install iSanXoT.

+ Discard the close search words.

+ Add list of scores that will use the FDR module adaptors by default.

+ New validation of the workflow schema:
	Check if the input files exit in the table2cfg.

### Changes in the Code Workflow

+ Include some shell/batch scripts that prepares the environment for the build packages.

+ Fixing a bug in the function that retrieves the folder name of jobs


___
## 0.4.1
```
DATE: 2021_12
```

### Highlights

+ Added more documentation.

### Changes in the Graphical User Interface

+ Rename 'Output folder' to 'Output Sample folder'.

+ Modify a little bit the color style.

+ Change the label of input adaptors.

+ Add 'Roboto' fonts for offline mode.

### Changes in the Code Workflow

+ Added more documentation:
	- Installation.

+ Adaptor-Comet:
	- The list of descriptions has to be separated by commas.
	- Bug fixed: the get_stats is redundacy in the tpl_commnds of masterq

+ Some programs moved from SanXoT folder to cmd.

+ Add version in the release build.

+ New implementation for the installation. We have to included the Python packages for each distribution.

+ GETVARIANCES: fixing the function that gets the job name.

+ Move stats script into "cmds" folder.

+ REPORT: 
	- Add values from RT checking first the lowr_level and then, the higher_level
	- For the momento, don't sort the columns

+ We have discarded snakemake because "datrie" packages has problems with the three distributions. 

+ Discards the title.

+ Discard the open search adaptors.

___
## 0.4.0
```
DATE: 2021_11
```

### Highlights

+ iSanXoT distribution for Windows, Mac, and Linux in x64:
	+ **Windows 10 Pro** (x64)
	+ **MacOs High Sierra** (10.13.6)
	+ **Ubuntu 20.04** (x64)


+ More documentation.

### Changes in the Graphical User Interface

+ Adaptor Open MSF:
	- Bug fixed: it needs the masterq process.

### Changes in the Code Workflow

+ LEVEL_CREATOR: fix a problem with "-w" parameter.


___
## 0.3.4
```
DATE: 2021_11
```

### Highlights

+ Create a windows for the documentation.

+ REPORT: Bug fixed sorting the columns.

### Changes in the Graphical User Interface

+ Adaptor Input PD: The button of Input folder has been fixed.

+ The following adaptors have been included:
	- Adaptor for Comet Input (Close search).
	- Adaptor for Comet-PTM Input (Close search).

### Changes in the Code Workflow

+ REPORT:
	- Bug fixed sorting the columns.
	- It doesn't increase the rows when we add information from Relation Table. It uses only the keys from the Report table.

+ TPL_COMMANDS:
	- Correct the relate tables in the compounds commands.

+ TABLE2CFG:
	- Replace "\" to "/" to accepts paths within "More_params"; otherwise the JSON crashes.

___
## 0.3.3
```
DATE: 2021_10
```

### Highlights

+ REPORT: Comment the code lines that sort the columns because it is not working correctly.

### Changes in the Graphical User Interface

### Changes in the Code Workflow

+ REPORT: Comment the code lines that sort the columns because it is not working correctly.

___
## 0.3.2
```
DATE: 2021_10
```

### Highlights

+ CNIC Adaptors in Close search for PD and MSF have been included.

+ The RELS_CREATOR command retrieves the column names of Relation Tables (RT) with the same names that the levels indicated by the user.

+ The REPORT command merge the Report Table (RPT) with multiple external tables. The only condition is the external tables have to contain a unique column name like the lower level of RPT.

+ Bug fixed and more improvementshave been implemented.

### Changes in the Graphical User Interface

+ INSTALL: The "installer" program has been modified to fix the problem with spaces in the path.

+ Update of column names and the description of modules.

+ Rename KLIBRATE to LEVEL_CALIBRATOR. Modify this task-table.

+ If the task-table is empty and the task-table file exists, now it deletes the task-table file for the updating.

+ Update the sidebar of commands when the task-table is full.

+ The commands: LEVEL_CALIBRATOR, INTEGRATE, SBT, SANSON accept a list of inputs. In that case, the cmds REPORT and NORCOMBINE have changed the input column.

+ RELS_CREATOR: The columns 'sup_infiles', 'thr_infiles', and 'filter' have been discarded for the momment.

+ WSPP_SBT, WSPPG_SBT, WPP_SBT, WPPG_SBT accept the "Identifier column header".

+ Fixing the project-workflow log table.

+ Problems with the Force execution have been fixed.

### Changes in the Code Workflow

+ REPORTER:
	- Fixing bug: Now, it extracts the low level matching the first number 2 from the name file of relation table.
	- It retreives the current report table altought the merge with another report tables doesn't work.
	- Sort the columns from the given sample list.
	- The Relation Table could be external of project.
	- The reported_variables is optional and it create a report only with levels.

+ RELS_CREATOR:
	- Rename the column headers based on the name of output file.

+ TABLE2CFG:
	- Fixed a bug: Now, the "merge with report table" parameter accepts external files.
	- The "Merge relate table" in REPORT cmd accepts a full path of RT file and a RT name that is in the rels folder of project.

+ TPL_COMMANDS:
	- Fixed a bug in the variant assignation. The variants have to be assigned in the sanxot1 and sanxotsieve.

+ FDR and MASTERQ (FDR_Q):
	- The masterq function (retrieves the first sorted protein alphanumerically) has been included in the FDR program.



___
## 0.3.1
```
DATE: 2021_09
```

### Highlights

+ Some "bugs"has been fixed for the WF-PTM

### Changes in the Graphical User Interface

+ INSTALL: The "installer" program has been modified to be more general.

+ The number of columns in the task-tables are always equal than the expected.

+ TABLE2CFG: Fixing a bug when there is '**' in the path. We have to disable a function that sustitutes the '**' by the current files (with glob) because otherwise the last part of program that replaces the '**' with the outputs, doesn't work.

### Changes in the Code Workflow

+ CREATERELS: The delimiter that divides the categories of a protein, has changed from ";" to "||" (iSanXot-dbscripts v2.5). For this reason, this program has been updated.

___
## 0.3.0
```
DATE: 2021_08
```

### Highlights

+ Basic workflow.

+ New design for the projects and workflows.

### Changes in the Graphical User Interface

+ Add number of threads from the loading proyects.

+ It is not requiered the version in the .cfg files.

+ The logs for each command processes is shown in a modal window.

+ The process panel also shows the logs of opened project.

+ New panel of inputs that allows to insert any file into iSanXoT.

+ Add short description for the modules.

+ TODO!!! ARREGLAR LOS PORCENTAJES DE LOS LOGS.

+ TODO!! PONER EL AVERAGE EN LOS RATIOS.

### Changes in the Code Workflow

+ NodeJs updated to version.

+ ElectroJs updated to 13.1.2 version.

+ CREATEIDQUANT: Discards the comment lines starting with '#'.

+ REPORTER:
	- Gets the name of 'experiment' until the root folder.
	- Bug fixed: The NaN values are taked into account in the output converting into empty values.

+ NORCOMBINE: The analysis name has changed. It includes the 'comb' prefix.

+ The sigmoides are distinguished from the first sanxot and the second sanxot in an integration.

+ STATS: get the link to sigmoide... Important: The sigmoide with outliers (first sanxot).

___
## 0.2.12
```
DATE: 2021_05
```

### Highlights


### Changes in the Graphical User Interface

+ Fixed bug. The optional columns for the commands don't appears when they are fill it.

+ Fixed bug: Loading a project from the "processes" page.


### Changes in the Code Workflow

+ WSPP_SBT: The "key-words:" Scan, Peptide, Protein, and Category have been established. The key-word "SequenceMod" has changed to "Peptide"

+ The quantification program (createIDQuant) accepts files with the "Ion Distribution".

+ RATIOS:
  - Remove leading and trailing whitespaces.
  - Remove whitespaces.

+ TABLE2CFG:
  - Removes whitespaces before/after comma
  - Replace "," to "-"



___
## 0.2.11
```
DATE: 2021_05
```

### Highlights


### Changes in the Graphical User Interface

+ The parameters of RATIOS command (Tag, FDR and Var(x)) have been deleted because they weren't needed.

+ The prefix '__MAIN_INPUTS_' has been deleted in the constant names.

+ Remove the Category file section from 'Databases' tab.

### Changes in the Code Workflow

+ The prefix "__MAIN_INPUTS_" has been deleted in the constant names.

+ The folder "preSanXoT" has been renamed to "adaptors".

+ REPORT program accepts multiple relationship files. It is only necessary to add the relationship name in the REPORT task-table.

+ PD, MSF and Comet now include 'Protein_Descriptions' column based on their own columns.

+ 'ID.tsv' from MaxQuant results now include the 'Protein_Description' column getting the first value.

+ MASTERQ: The FASTA input parameter is OBSOLETE. Now, we use only the 'Protein_Description' from the results of search engines.

+ CREATEIDQUANT: The columns need to recognize the search engine have changed.

+ STATS programs: Two programs have been included in the workflow. A program which gets the ID statistics, and other that gets the variances with the sigmoide image for each integration.

+ SANXOT v2.20: retrieves the error message using the sys.exit().

+ SANSON v1.14: retrieves new error message when the higherElement file is empty.

+ TABLE2CFG and MYSNAKE: the global variables have been included in a different module.

+ RATIOS: Trace log has been added when the tags are not available in the data.

+ MYSNAKE: The program, which creates the report of variances, has been added.

+ CREATERELS:
	- Adds new function that replaces the 'Protein' column by the new xref column name, if it is applicable.
	- New design in the algorithm to reduce the time/memory in the execution.
	- Filter section has been included.

+ TPL_COMMANDS:
	- Some variances in the WSPPG_SBT have changed.
	- The "_outStats" file from sanxot1 has been renamed to distinguish from sanxot2 

+ Common library for the scripts has been created.

+ SANSON:
	- New program has been developed that filter the third column.
	- Joiner program has been added to the command.





___
## 0.2.10
```
DATE: 2021_04
```

### Highlights

+ The "REPORT" program has been improved.

+ The parameters for the third column has been revised.

### Changes in the Graphical User Interface

+ The GUI includes the CREATE_IDQUANT command but it is a preliminar implementation.

### Changes in the Code Workflow

+ There is a preliminar implementation of CREATE_IDQUANT program that accepts the identifications from the search engines: PD, Comet and MSFragger. It is not ready yet!!

+ In the case of duplicated scans for Comet results, we take the scans with the best cXCorr and then, with the duplicated, we get the first one.

+ masterQ: The "Description" is removed if the value is not created.

+ createRes: The program has been simplified. The third column is retrieved correctly.

+ The Database task-table has changed. The filter columns has been deleted.

+ The "REPORT" program has been improved:
	- It accepts any kind of level name.
	- It merges all the columns from the inpu "relationship" file.
	- It filters by multiple columns or single column.

+ The filename of logs has changed.

+ The parameters for the third column has been revised.

+ Include all outputs for each sanxot-sanxotsieve-sanxot in the INTEGRATION and SBT commands.



___
## 0.2.9
```
DATE: 2021_03
```

### Highlights

+ The Basic PTM workflow is optimised.

### Changes in the Graphical User Interface

+ Open correctly the dialog to load the input files in a PTM workflow.

+ Style changes.

+ Load correctly the "input file" table.

### Changes in the Code Workflow

+ The createRels program admits the ':' delimter for the join of columns.

+ The REPORT program shows the level without relationship with the high-level. For example, it shows the protein without descriptions or it shows the protein without genes.

+ Filtering correctly the file used by SANSON program.


___
## 0.2.8
```
DATE: 2021_03
```

### Highlights

+ Pre-release of PTM workflow.

### Changes in the Graphical User Interface

+ PTM workflow has been included. It is a preliminar version.

+ The interface accepts the input files for the PTM workflow.

+ Add an auto overflow for worlflow log table.

+ The identifier of HTML elements for the inputs have changed.

### Changes in the Code Workflow

+ Scan Id column has been added in the ID.tsv files. The value is "[Spectrum_File]-[Scan]-[Charge]" for the search engines: PD, MSFragger and Commet. 
Therefore, the WSPP_SBT will accept that column values.

+ The samples files will have a version prefix.

+ The keys for the inputs: indir, outdir, catfile, etc. have changed.

+ The Default parameters for the "createSansonLevel" are included in the "tpl_commands".

+ "stats" file in "sanxot" program: Fix the bug when the given list is empty.

___
## 0.2.7
```
DATE: 2021_03
```

### Highlights

+ Improvements in the REPORT command.

+ The installation module has been improved.

+ The image of Sanson diagram is reported.

### Changes in the Graphical User Interface

+ The appareance of worked-out examples has changed.

+ The structure of workflow config file has changed.

+ The Mar. 2021 database has been added.

+ Improvements in the log tables of processes.

+ The REPORT command has new colummns.

### Changes in the Code Workflow

+ Improvements in the REPORT program:
	+ New way to propvide the "description" info for the given level.
	+ There is a new parameter 'show_leves' that allows us to say which levels we want in the report file.
	+ Merge the given intermediate report using the union of keys from both frames.

+ The installation module has been improved. Now, it install another programas like "java", "dot", etc. The installation of forced modules has been disabled.

+ The image of Sanson diagram is reported.

+ Bug fixed: In some cases, the report program needed the files "gene2description" and "category2description". Now, these files are created in the Database table.


___
## 0.2.6
```
DATE: 2021_02
```

### Highlights

+ We have started to include some documentation.

+ Due we have included a "force" column for each tasktable. For this reason, *this version is not compatible with projects executed by iSanXoT's with lower versions*.

### Changes in the Graphical User Interface

+ There is some documentation.

+ Gramatical changes.

+ The internal files of the application have been restructured.

+ We have included the "force" column that is a flag for the forced execution of command.

+ We have included the "gene2description" relationship file in the table.

+ Bug fixed: exporting the tasktable of databases section.

### Changes in the Code Workflow

+ Bug fixed - createRels:
	- There were a problem reporting the category2categoryall files when the input database came from two or more species. In the reindex of dataframe.
	- there were empty cells.

+ Now, the table "Select input files" accepts a filename and the path of file for the column "Infile".

+ The NextCloud url where the databases and samples are saved, have changed.

+ report:
	- We include the 'gene' column to the correct report.
	- we delete the all columns correctly. 

+ installer: Now, we force the installation of some parts of requirements.

___
## 0.2.5
```
DATE: 2021_02
```

### Highlights

+ We have changed the visualization of Log panels of GUI.

### Changes in the Graphical User Interface

+ We have fixed the filter of REPORT command.

+ Bug fixed: When you create a workflow from the scratch, there is a conflict with the relationship tables (CatDB and CatFile). Both tables are created. Then, two processes create the same relationship file.

+ The table of sanson command needs another Norm column: Lower norm and Higher norm.

+ If at least one cell of optinal parameters is filled, then the "advanced parameters" is shown.

### Changes in the Code Workflow

+ Bug fixed: The filter function was not working correctly in the REPORT command. The pandas "eval" function did not filter correctly.

___
## 0.2.4
```
DATE: 2021_01
```

### Highlights

+ We have changed the workflow managment system. Now we have developed "mysnake"

### Changes in the Graphical User Interface

+ The GUI executes the new workflow managment system (MySnake).

+ The validation menu has been deprecated.

### Changes in the Code Workflow

+ We have created "mysnake" workflow managment system but we still use "snakemake" to know the list of processes for the workflow.

+ We have changed the config file of workflow. Now, the rows of tables represents the commands.
For that, there are a list of commands and each command is composed by list of rules (programs).

+ We have changed some internal programs of workflow. First, they save the results in temporal file and then, they rename to the final file name.

___
## 0.2.3
```
DATE: 2021_01
```

### Highlights

+ We have included a new condition for sanxot program.

### Changes in the Graphical User Interface

+ tpl_commands.yaml: The "-m 600" parameter has been added into all the firsts comands of sanxot.

### Changes in the Code Workflow

+ sanxot: The "emergencyvariance" has been changed.
In the case the maximum iterations are reached (see -m), force the provided variance by the user. Default 0.0

___
## 0.2.2
```
DATE: 2021_01
```

### Highlights

+ We have included the WSPPG-SBT command in the basic workflow.

### Changes in the Graphical User Interface

+ We have included the WSPPG-SBT command in the basic workflow.
+ We include the commands only by the configuration file (workflow.json)
+ We merge common functions for the programs: table2cfg, ratios, create_id

### Changes in the Code Workflow


___
## 0.2.1
```
DATE: 2020_12
```

### Highlights

+ The use of UniProtKB database to create the relationship files.

### Changes in the Graphical User Interface

+ We have divided the interface that create the relationship files. Now, it accepts the protein-category file and the database version of UniProtKB.


### Changes in the Code Workflow


