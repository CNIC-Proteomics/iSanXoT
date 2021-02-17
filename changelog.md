___
## 0.2.7
```
DATE: 2021_XX
```

### Highlights

+ TODO!! We can force the execution of some commands.

+ TODO??? Now, iSanXoT accepts inputs from the search engines: Comet, MSFragger, and MaxQuant.

### Changes in the Graphical User Interface

+ TODO!!! Include the column "output" in the workflow log table.

+ TODO!! Improve the refresh of log tables.

### Changes in the Code Workflow

+ TODO!! There is new programa which reports some information (variances, ...) for each integration.

+ TODO??? Now iSanXoT accepts inputs from the search engines: Comet, MSFragger, and MaxQuant (you have to include Ecoli species).

+ TODO!! There is new programa which reports some information (variances, ...) for each integration.

___
## 0.2.6
```
DATE: 2021_02
```

### Highlights

+ We have started to include some documentation.

+ We have included the "force" column that is a flag for the forced execution of command.

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


