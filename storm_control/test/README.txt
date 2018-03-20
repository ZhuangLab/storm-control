
Some of the tests depend on the storm-analysis project. This
requires the following modules:

1. pytest
2. pytest-mock
3. pytest-qt


Running these tests in the standard way may fail, perhaps due
the creation of so many QApplications?

What works, but is linux specific is to use this module:
https://pypi.python.org/pypi/pytest-xdist

And run the tests with:
py.test --boxed

So that each test gets run in it's own Python instance.

Note also that you should probably run the tests in this directory
due to possible relative path issues.

$ cd storm-control/storm_control/test
$ py.test --boxed


Getting more information on segmentation faults:
gdb -return-child-result -batch -ex r -ex bt --args python -m pytest
