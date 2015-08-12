LeBLEU - Quick start
===========================


Installation
------------

1) Create virtual environment

virtualenv --system-site-packages lebleu  
cd lebleu  
source bin/activate  

2) Clone repository

git clone https://github.com/Waino/LeBLEU.git lebleu  
cd lebleu  

3) Compile and install python-Levenshtein

git submodule init  
git submodule update  
cd python-Levenshtein  
python setup.py install  

4) Profit

lebleu itself is installed using setuptools library for Python.
To build and install the module and scripts to default paths, type

python setup.py install

For details, see http://docs.python.org/install/

Citing
------

If you use LeBLEU in a scientific publication, we ask you to cite

FIXME  


Documentation
-------------

FIXME

Contact
-------

Questions or feedback? Email: stig-arne.gronroos (at) aalto (dot) fi
