.. :changelog:

.. _KeepAChangelog: http://keepachangelog.com/
.. _SemanticVersioning: http://semver.org/

Change Log
----------

All notable changes to this project will be documented in this file.

The format is based on KeepAChangelog_ and this project adheres to SemanticVersioning_.


[1.0.0] - 2020-05-28
++++++++++++++++++++

Added
~~~~~
* Added maintainability badge
* Added translations
* Added email attachment link

Changed
~~~~~~~
* `django-webix` min version v1.2.0
* Better invoice area
* Optimized count with exists

Removed
~~~~~~~
* Removed old skebby gateway

Fixed
~~~~~
* Fixed gateway utils without set sender as django app
* Fixed filters
* Fixed python3 compatibility
* Fixed multiselect split
* Fixed sender window typology autocomplete


[0.3.6] - 2019-04-19
++++++++++++++++++++

* Added and/or in list filters


[0.3.5] - 2019-04-05
++++++++++++++++++++

* Fixed parametric send method


[0.3.4] - 2019-03-29
++++++++++++++++++++

* Fixed kwargs in `send_mixin`
* Added parametric sms functionality


[0.3.3] - 2019-03-28
++++++++++++++++++++

* Split send function


[0.3.2] - 2019-03-28
++++++++++++++++++++

* Fix migration 0003


[0.3.1] - 2019-02-27
++++++++++++++++++++

* Fix Django 2.0 templatetags
* Added support to model `select_related`, `prefetch_related` and `filter` of sender querysets


[0.1.0] - 2018-08-XX
++++++++++++++++++++

* First release on PyPI.
