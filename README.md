LeBLEU - Quick start
===========================

LeBLEU **requires python2** (which is obsolete).
Running LeBLEU under python3 results in

    Segmentation fault (core dumped)

Installation
------------

1) Create python2 virtual environment

virtualenv --python=python2 lebleu  
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

Virpioja, S. and Grönroos, S.-A. (2015).  
LeBLEU: N-gram-based Translation Evaluation Score for Morphologically Complex Languages.  
In Proceedings of the Workshop on Machine Translation 2015.  
Lisbon, Portugal, September 17-18, Association for Computational Linguistics.  


Documentation
-------------

FIXME

Contact
-------

Questions or feedback? Email: stig-arne.gronroos (at) aalto (dot) fi
