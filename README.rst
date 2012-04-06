sandboxie is a Python interface to `Sandboxie <http://sandboxie.com>`_.


Quickstart
----------

::

    >>> import sandboxie
    >>> sbie = sandboxie.Sandboxie()

Create a sandbox::

    >>> sbie.create_sandbox(box='foo', options={'Enabled': 'yes'})

Start a sandboxed process::

    >>> sbie.start('notepad.exe', box='foo', wait=False)

Get sandboxed processes::

    >>> for pid in sbie.running_processes(box='foo'):
    >>>     print(pid)
    3
    15688
    5716
    26916

Terminate sandboxed processes::

    >>> sbie.terminate_processes(box='foo')

Delete the contents of a sandbox::

    >>> sbie.delete_contents(box='foo')

Destroy a sandbox::

    >>> sbie.destroy_sandbox(box='foo')


Installation
------------

The preferred way is to use pip_::

    $ pip install sandboxie

You can also use ``easy_install``, but it's discouraged.

.. _pip: http://pip-installer.org


Supported Python versions
~~~~~~~~~~~~~~~~~~~~~~~~~

Python 2.7 and 3.2 are currently supported from a single codebase, without 2to3
translation.


Contribute
----------

The code repository is on GitHub: https://github.com/gg/sandboxie-py.

To contribute:

#. Work on an `open issue`_ or submit a new issue to start a discussion around
   a bug or feature request.

    * When submitting a bug, ensure your description includes the following:
        - the version of ``sandboxie`` used
        - any relevant system information, such as your operating system
        - steps to produce the bug (so others could reproduce it)

#. Fork `the repository`_ and add the bug fix or feature to the **develop**
   branch.
#. Write tests that demonstrate the bug was fixed or the feature works as
   expected.
#. Submit a pull request and bug the maintainer until your contribution gets
   merged and published :-) You should also add yourself to AUTHORS_.

.. _the repository: https://github.com/gg/sandboxie-py
.. _open issue: https://github.com/gg/sandboxie-py/issues
.. _AUTHORS: https://github.com/gg/sandboxie-py/blob/develop/AUTHORS.rst


Running the Tests
~~~~~~~~~~~~~~~~~

tox_ is used to run unit and integration tests in each of the supported Python
environments.

First install tox::

    $ pip install tox

Then run tox from the project root directory::

    $ tox

*Note: the integration tests require Sandboxie to be installed on your
machine.*

.. _tox: http://tox.testrun.org/


Coding Style
~~~~~~~~~~~~

Ensure that your contributed code complies with `PEP 8`_. The test runner
``tox`` also checks for PEP 8 compliance.

.. _PEP 8: http://www.python.org/dev/peps/pep-0008/
