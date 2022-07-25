Contributing
============

All contributions are welcomed and encouraged. Please open an issue first if you consider contributing big changes,
so we can discuss them beforehand and avoid unnecessary work on your part because someone is already working on a similar
feature or any other complication.
It is also advised to read the page entirely before starting to contribute.

Setting up the development environment
``````````````````````````````````````
The following assumes a Linux environment with Python 3 installed with the venv module.
The setup should be similar on other operating systems.
After you forked and cloned the repository, run the following commands from the root of the project.

.. code-block:: bash

    $ python -m venv venv           # Create the virtual env
    $ source venv/bin/activate      # Activate the virtual env
    (venv) $ python -m pip install -e .    # Install litemapy in editable mode in the virtual env, along with its dependencies
    (venv) $ python -m pip install pytest  # Install pytest so you can run the unittests

Code
````
You can contribute on `GitHub <https://github.com/SmylerMC/litemapy>`_ by forking the project and making a pull request.
Please follow the usual Python syntax convention, in particular:

* Module, method and variable names in snake_case
* Global constants in UPPER_SNAKE_CASE
* Class names in CamelCase
* Lines no longer than 80 characters
* Protected members should start with an underscore and private members with two underscores

Tests
`````
Tests are also appreciated, especially for complex features.
They should live in a test module with the same name as the module that contains
the feature that's being tested, but with the *test_* prefix added.
You can follow the pattern of existing tests if you need examples,
or read `the Pytest documentation <https://docs.pytest.org/en/7.1.x/>`_ for an in depth explanation.

Install pytest so you can run the tests (do so when working in the virtual env):

.. code-block:: bash

    (venv) $ python -m pip install pytest

You can then execute the tests and make sure they all pass:

.. code-block:: bash

    (venv) $ python -m pytest  # Run from the root of the project

If you are unsure about running the tests locally, they are run automatically when the code is pushed to GitHub.

Documentation and docstrings
````````````````````````````
You can also contribute to this documentation on `GitHub <https://github.com/SmylerMC/litemapy>`_
by making a pull request.

Docstrings are always appreciated when writing new functions or classes,
and required for your feature to appear in this documentation.
They should be written following
`the Sphinx format <https://sphinx-rtd-tutorial.readthedocs.io/en/latest/docstrings.html>`_.

To build the documentation locally, install sphinx and the read the docs theme in your virtual env:

.. code-block:: bash

    (venv) $ python -m pip install Sphinx sphinx-rtd-theme

You can then build the documentation:

.. code-block:: bash

    (venv) $ cd docs       # Change directory to the "docs" folder
    (venv) $ make html     # Build the docs, they will be in docs/build/html