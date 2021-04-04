___
## 0.2.X
```
DATE: 2021_YY
```

### Highlights

+ TODO!! Documentation.

### Changes in the Graphical User Interface

+ TODO!! We have included more worked-out examples from MSFragger result and Comet.

+ TODO!!! Include the column "output" in the workflow log table.

### Changes in the Code Workflow

+ TODO!! New program that reports some information (variances, ...) for each integration.

+ TODO!! ARREGLAR CUANDO NO ABRE UN PROYECTO SI ESTAMOS EN LA PARTE DE LOGS"!!"

+ TODO!! ARREGLAR EL ERROR QUE CUANDO ESCRIBES UN OUTPUT DEL TIPO "Control_1_cArt/cQ" (subcarpeta), que se creen bien los "OUTPUTFILES" y no HAYA UN ERROR DE "output cyclic". Ejemplo con 
S:\U_Proteomica\LABS\LAB_ARR\MouseLDL-HighFattyDiet\PTMs\iSanXoT_029


___
## 0.2.10
```
DATE: 2021_04
```

### Highlights

+ Now iSanXoT extracts the quantification from mzML files.

+ iSanXoT accepts identifications from the search engines: PD, Comet and MSFragger.

+ Label-Free workflow.

+ We have include the Ecoli species.

### Changes in the Graphical User Interface

+ The GUI includes the CREATE_IDQUANT command.

+ Label-Free workflow.

### Changes in the Code Workflow

+ We have joined in a program the identification and quantification programs (createIDQuant).

+ In the case of duplicated scans for Comet results, we take the scans with the best cXCorr and then, with the duplicated, we get the first one.

+ createRes:
TODO!! WE HAVE TO IMPROVE THE CREATERELS PROGRAM!! SIMPLYFY THE CODE AND ADD THE THIRD COLUMN.





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


