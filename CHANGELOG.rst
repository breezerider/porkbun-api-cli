
Changelog
=========

0.2.0 (2026-09-15)
------------------

* Structured plan output: a clear per-domain plan (``NEW``/``UPD``/``OK`` rows)
  is printed before any changes are made
* Per-domain summary line after execution showing counts of created, updated,
  matched, and failed records
* New ``--yes`` / ``-y`` flag to skip the confirmation prompt
* ``--dry-run`` now exits with code 3 when changes are pending (code 0 when
  in sync), so it can be used as a CI drift check
* Descriptive exit codes: ``0`` success, ``1`` pre-execution failure,
  ``2`` usage error, ``3`` dry-run with changes, ``4`` execution failure
* ``replace`` mode is now explicitly disabled with a clear error message;
  use ``upgrade`` instead
* Colored output on terminals that support it; respects ``NO_COLOR``
* Fixed help text formatting — operation modes now appear on separate lines

0.1.2 (2026-09-14)
------------------

* Maintenance release, no user facing changes
* Floor Python version at 3.11

0.1.1 (2024-05-13)
------------------

* Fixup the package

0.1.0 (2024-05-12)
------------------

* Initial release on PyPI.
* Support only creation of new and update of existing DNS records
