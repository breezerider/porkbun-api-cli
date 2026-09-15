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

.. |version| image:: https://img.shields.io/badge/test.pypi-v0.2.0-informational?style=flat
    :alt: PyPI Package latest release
    :target: https://test.pypi.org/project/porkbun-api-cli

.. |wheel| image:: https://img.shields.io/badge/wheel-yes-success?style=flat
    :alt: PyPI Wheel
    :target: https://test.pypi.org/project/porkbun-api-cli

.. |supported-versions| image:: https://img.shields.io/badge/python-3.11_|_3.12_|_3.13|_3.14-informational?style=flat
    :alt: Supported Python versions
    :target: https://test.pypi.org/project/porkbun-api-cli

.. |commits-since| image:: https://img.shields.io/github/commits-since/breezerider/porkbun-api-cli/v0.2.0.svg
    :alt: Commits since latest release
    :target: https://github.com/breezerider/porkbun-api-cli/compare/v0.2.0...main

.. end-badges

CLI client for managing domain DNS records through calls to Porkbun API.
It creates, updates, and lists DNS records from a YAML configuration file.
The client supports several operation modes:

* append  -- only create new entries, preserve existing unchanged
* replace -- not implemented, use 'upgrade'
* update  -- only update existing entries, do not create or remove
* upgrade -- create new or update existing, do not remove

Before any changes are made, a structured plan is printed showing what
would happen (``NEW`` / ``UPD`` / ``OK`` rows per record). A per-domain
summary line reports the outcome after execution. Output is colored on
terminals that support it and respects ``NO_COLOR``.

Example
-------

Create a YAML config (e.g. ``config.yml``) describing the desired records
for ``example.org`` and several subdomains:

.. code-block:: yaml

    api:
      endpoint: https://api.porkbun.com/api/json/v3
      apikey: pk1_your_api_key
      secretapikey: sk1_your_secret_key

    domains:
      - name: example.org
        records:
          - {name: "",        type: A,    content: 192.0.2.1}
          - {name: "www",     type: A,    content: 192.0.2.1}
          - {name: "git",     type: A,    content: 192.0.2.2}
          - {name: "mail",    type: MX,   content: mail.example.org, prio: 10}
          - {name: "",        type: TXT,  content: "v=spf1 -all"}

Run a dry run to preview what would change::

    porkbun-api-cli config.yml --mode upgrade --dry-run -vv

First run (all records are new):

::

    dry run requested, enable verbose output
    IP address reported by API '203.0.113.42'
    - querying records for 'example.org' .. done
    Plan for example.org (upgrade mode):
      NEW  A example.org 192.0.2.1
      NEW  A www.example.org 192.0.2.1
      NEW  A git.example.org 192.0.2.2
      NEW  MX example.org mail.example.org
      NEW  TXT example.org v=spf1 -all
    dry run requested, skipping execution

Second run after changing the config (``git`` IP updated, ``www`` already
in sync, ``docs`` is new):

::

    dry run requested, enable verbose output
    IP address reported by API '203.0.113.42'
    - querying records for 'example.org' .. done
    Plan for example.org (upgrade mode):
      OK   A example.org 192.0.2.1
      OK   A www.example.org 192.0.2.1
      UPD  A git.example.org 192.0.2.3
      OK   MX example.org mail.example.org
      OK   TXT example.org v=spf1 -all
      NEW  A docs.example.org 192.0.2.1
    dry run requested, skipping execution

Apply the changes, skipping the confirmation prompt::

    porkbun-api-cli config.yml --mode upgrade --yes

Sample output (second config):

::

    IP address reported by API '203.0.113.42'
    - querying records for 'example.org' .. done
    Plan for example.org (upgrade mode):
      UPD  A git.example.org 192.0.2.3
      NEW  A docs.example.org 192.0.2.1
    Summary for example.org: 1 created, 1 updated, 5 matched, 0 failed

Command-line options
--------------------

::

    porkbun-api-cli [OPTIONS] CONFIG_FILE

Options:

* ``-m, --mode [append|replace|update|upgrade]`` — Operation mode (default: append). ``replace`` is not implemented, use ``upgrade``.
* ``-n, --dry-run`` — Perform a trial run without any changes; exits non-zero (code 3) if any changes would be needed.
* ``-y, --yes`` — Skip confirmation prompt.
* ``-v, --verbose`` — Increase output verbosity (``-vv`` for match rows).
* ``-V, --version`` — Print tool version and exit.

Exit codes
----------

* ``0`` — success (with or without changes); dry-run in sync.
* ``1`` — pre-execution failure (API auth, config load).
* ``2`` — usage error (invalid mode, conflicting flags).
* ``3`` — dry-run with planned changes.
* ``4`` — at least one operation failed during execution.

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
