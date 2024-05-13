========
Overview
========

.. start-badges

.. list-table::
    :stub-columns: 1

    * - docs
      - |docs|

    * - build
      - |github-actions| |codecov|

    * - package
      - | |license| |version| |wheel| |supported-versions|
        | |commits-since|

.. |docs| image:: https://readthedocs.org/projects/porkbun-api-cli/badge/?style=flat
    :target: https://porkbun-api-cli.readthedocs.io/
    :alt: Documentation Status

.. |github-actions| image:: https://github.com/breezerider/porkbun-api-cli/actions/workflows/github-actions.yml/badge.svg
    :alt: GitHub Actions Build Status
    :target: https://github.com/breezerider/porkbun-api-cli/actions

.. |codecov| image:: https://codecov.io/gh/breezerider/porkbun-api-cli/branch/main/graphs/badge.svg?branch=main
    :alt: Coverage Status
    :target: https://app.codecov.io/github/breezerider/porkbun-api-cli

.. |license| image:: https://img.shields.io/badge/license-BSD-green?style=flat
    :alt: PyPI Package license
    :target: https://test.pypi.org/project/porkbun-api-cli

.. |version| image:: https://img.shields.io/badge/test.pypi-v0.1.0-informational?style=flat
    :alt: PyPI Package latest release
    :target: https://test.pypi.org/project/porkbun-api-cli

.. |wheel| image:: https://img.shields.io/badge/wheel-yes-success?style=flat
    :alt: PyPI Wheel
    :target: https://test.pypi.org/project/porkbun-api-cli

.. |supported-versions| image:: https://img.shields.io/badge/python-3.8_|_3.9_|_3.10|_3.11-informational?style=flat
    :alt: Supported Python versions
    :target: https://test.pypi.org/project/porkbun-api-cli

.. |commits-since| image:: https://img.shields.io/github/commits-since/breezerider/porkbun-api-cli/v0.1.0.svg
    :alt: Commits since latest release
    :target: https://github.com/breezerider/porkbun-api-cli/compare/v0.1.0...main

.. end-badges

CLI client for managing domain DNS records through calls to Porkbun API.
It can create, edit and list DNS records following a configuration
provided in a YAML file. The client is flexible and can restrict
its operations to only a subset choosen by the user by supporting
several operation modes:

* append -- only new entries are created preserving existing entries unchanged
* replace -- replace all existing entries with user configuration
* update -- only update existing entries without creating or removing entries that are not listed in the configuration
* upgrade -- create new entries or update exising but do not remove entries that are not listed in the configuration

It depends on other common packages:

* click
* pyyaml
* requests

Installation
============

Get latest released version from `PyPI <https://pypi.org/>`_::

    pip install porkbun-api-cli

You can also install the in-development version with::

    pip install https://github.com/breezerider/porkbun-api-cli/archive/main.zip


Documentation
=============


https://porkbun-api-cli.readthedocs.io/


License
=======

- Source code: `BSD-3-Clause <https://choosealicense.com/licenses/bsd-3-clause/>`_ license unless noted otherwise in individual files/directories
- Documentation: `Creative Commons Attribution-ShareAlike 4.0 <https://creativecommons.org/licenses/by-sa/4.0/>`_ license


Development
===========

To run all the tests issue this command in a terminal::

    tox
