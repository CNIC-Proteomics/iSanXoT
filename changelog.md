## 0.2.5
```
DATE: 2021_01
```

### Highlights

+ We have changed the visualization of Log panels of GUI.

### Changes in the Graphical User Interface

+ We have fixed the filter of REPORT command.

+ Bug fixed: When you create a workflow from the scratch, there is a conflict with the relationship tables (CatDB and CatFile). Both tables are created. Then, two processes create the same relationship file.

+ Bug fixed: the table of sanson command needs another Norm column.

### Changes in the Code Workflow

+ Bug fixed in the programa of Reports. The filter function was not working correctly. The pandas "eval" function does not filter.



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


