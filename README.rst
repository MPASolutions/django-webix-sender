Django Webix Sender
===================

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
