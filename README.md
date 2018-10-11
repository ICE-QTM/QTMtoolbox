# QTM Toolbox
This repository holds the Python QTM Toolbox that can be used for transport measurements with equipment as used in the QTM/ICE research group. 

## Contents
The repository contains different files and folders, organised in the following manner:
* **Measurement_script.py** is the main file of the project and is the starting point of each experiment. For every new experiment, create a new copy of this file and change it to reflect your current measurement setup.
* **functions** contains the QTMlab.py script that contains basic functions such as _move_, _sweep_, _measure_. 
* **instruments** contains definitions for all instruments that can be used during measurements. 
* **Manual** is a PDF file containing detailed information about how to use this Toolbox.


_The .gitignore file tells GitLab that certain files / folder should not be uploaded to this repository (such as personal configuration files) and can be ignored._