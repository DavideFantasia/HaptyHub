# HaptyGraph
The aim is producing an active 3D print representation of a diagram or a map, that can be used in the context of formal teaching or in the context of accessibility to clinical care by people with visual impairment: using LLM and Computer Vision.

## Installation
To install and launch the software you have to install `python` and clone the repository as:
```bash
git clone git@github:DavideFantasia/HaptyGraph
cd ./HaptyGraph
```

### Linux
Once cloned the repo, you can install all the requirements in a virtual enviroments as:
```bash
source venv/bin/activate
pip3 install -r requirements.txt
```
In order to execute all the software's dependencies, it is required to have installed `libxcb-cursor0` 
to let PyQt read the cursor informations:
```
sudo apt install libxcb-cursor0
```

### Windows
Once cloned the repo, you can install all the requirements in a virtual enviroments as:
```bash
venv\bin\activate
pip3 install -r requirements.txt
```
