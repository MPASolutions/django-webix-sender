Django Webix Sender
===================


.. image:: https://badge.fury.io/py/django-webix-sender.svg
    :target: https://badge.fury.io/py/django-webix-sender
    :alt: Version

.. image:: https://travis-ci.org/MPASolutions/django-webix-sender.svg?branch=master
    :target: https://travis-ci.org/MPASolutions/django-webix-sender
    :alt: Build

.. image:: https://codecov.io/gh/MPASolutions/django-webix-sender/branch/master/graph/badge.svg
    :target: https://codecov.io/gh/MPASolutions/django-webix-sender
    :alt: Codecov

.. image:: https://api.codeclimate.com/v1/badges/7ed5002646a1b41957e5/maintainability
   :target: https://codeclimate.com/github/MPASolutions/django-webix-sender/maintainability
   :alt: Maintainability

.. image:: https://img.shields.io/github/issues/MPASolutions/django-webix-sender.svg
    :target: https://github.com/MPASolutions/django-webix-sender/issues
    :alt: Issues

.. image:: https://img.shields.io/pypi/pyversions/django-webix-sender.svg
    :target: https://img.shields.io/pypi/pyversions/django-webix-sender.svg
    :alt: Py versions

.. image:: https://img.shields.io/badge/license-MIT-blue.svg
    :target: https://raw.githubusercontent.com/MPASolutions/django-webix-sender/master/LICENSE
    :alt: License

Documentation
-------------

The full documentation is at https://django-webix-sender.readthedocs.io.

Quickstart
----------

Install Django Webix Sender:

.. code-block:: bash

    $ pip install django-webix-sender

Add ``django-webix-sender`` to your ``INSTALLED_APPS``

.. code-block:: python

    INSTALLED_APPS = [
        # ...
        'django_webix_sender',
        # ...
    ]

Add ``django-webix-sender`` URLconf to your project ``urls.py`` file

.. code-block:: python

    from django.conf.urls import url, include

    urlpatterns = [
        # ...
        url(r'^django-webix-sender/', include('django_webix_sender.urls')),
        # ...
    ]


Running Tests
-------------

Does the code actually work?

.. code-block:: bash

    $ source <YOURVIRTUALENV>/bin/activate
    $ (myenv) $ pip install tox
    $ (myenv) $ tox
