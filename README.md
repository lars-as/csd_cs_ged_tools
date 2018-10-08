# csd_ged_format_repair

Simple pretty printer and analysis for gene expression data format used by the C++ CSD-Software. 
The C++ CSD-Software is somewhat restrictive with regards to whitespace and suffers from poor error reporting. 
The purpose of this tool is to check for syntax errors and rewrite input files such that they are accepted by the CSD-Software.

Install: 

    Simply download project files into the same folder. Requires the Arpeggio parser generator which can be 
    installed using the python package manager "$ pip install Arpeggio".

Example: 

    The program is run from the commandline with the list of files to check.

    Assuming two files with gene expression data.

    $ ged_validate testm1.txt testm2.txt

    This will output two files fixed_testm1.txt and fixed_testm2.txt into the same folder as the input files.
