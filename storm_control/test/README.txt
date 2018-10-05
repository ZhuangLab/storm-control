
Some of the tests depend on the storm-analysis project.

The tests require the following modules:

1. pytest
2. pytest-forked
3. pytest-mock
4. pytest-qt

The following module is also recommened:

1. pytest-faulthandler


Running these tests in the standard way usually fails do to a
segmentation fault. My guess is that something is not getting
cleaned up properly at the end of a test, and this then messes
up the next test.

The tests should run successfully on a linux platform where it
is possible to run each test in it's own Python instance using
the command "py.test --forked".

Note also that you should probably run the tests in this directory
due to possible relative path issues.

$ cd storm-control/storm_control/test
$ py.test --forked


Getting more information on segmentation faults:
gdb -return-child-result -batch -ex r -ex bt --args python -m pytest
valgrind python -m pytest
