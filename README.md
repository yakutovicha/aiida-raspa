[![Build Status](https://github.com/yakutovicha/aiida-raspa/workflows/ci/badge.svg)](https://github.com/yakutovicha/aiida-raspa/actions)
[![Coverage Status](https://coveralls.io/repos/github/yakutovicha/aiida-raspa/badge.svg?branch=develop)](https://coveralls.io/github/yakutovicha/aiida-raspa?branch=develop)
[![PyPI version](https://badge.fury.io/py/aiida-raspa.svg)](https://badge.fury.io/py/aiida-raspa)

# AiiDA RASPA
[AiiDA](http://www.aiida.net/) plugin for [RASPA2](https://github.com/iRASPA/RASPA2).

Designed to work with with RASPA 2.0.37 or later.

# Documentation
The documentation for this package can be found on [Read the Docs](https://aiida-raspa.readthedocs.io/en/latest/).


# Installation
If you use ``pip``, you can install it as:
```
pip install aiida-raspa
```

If you want to install the plugin in an editable mode, run:
```
git clone https://github.com/yakutovicha/aiida-raspa
cd aiida-raspa
pip install -e .  # Also installs aiida, if missing (but not postgres/rabbitmq).
```

In case the plugin does not appear in the output of `verdi plugin list aiida.calculations`,
run `reentry scan` and try again.


# Examples
See `examples` folder for complete examples of setting up a calculation or a work chain.

## Simple calculation
```shell
cd examples/simple_calculations
verdi run example_base.py <code_label> --submit          # Submit example calculation.
verdi process list -a -p1                                # Check status of calculation.
```

## Work chain
```shell
cd examples/workchains
verdi run example_base_restart_timeout.py  <code_label>  # Submit test calculation.
verdi process list -a -p1                                # Check status of the work chain.
```


# License
MIT

# Contact
yakutovicha@gmail.com


# Acknowledgements
This work is supported by:
* the [MARVEL National Centre for Competency in Research](http://nccr-marvel.ch) funded by the [Swiss National Science Foundation](http://www.snf.ch/en);
* the [MaX European Centre of Excellence](http://www.max-centre.eu/) funded by the Horizon 2020 EINFRA-5 program, Grant No. 676598;
* the [swissuniversities P-5 project "Materials Cloud"](https://www.materialscloud.org/swissuniversities).

<img src="miscellaneous/logos/MARVEL.png" alt="MARVEL" style="padding:10px;" width="150"/>
<img src="miscellaneous/logos/MaX.png" alt="MaX" style="padding:10px;" width="250"/>
<img src="miscellaneous/logos/swissuniversities.png" alt="swissuniversities" style="padding:10px;" width="250"/>
