
Some of the tests depend on the storm-analysis project.

Running these tests in the standard way may fail, perhaps due
the creation of so many QApplications?

What works, but is linux specific is to use this module:
https://pypi.python.org/pypi/pytest-xdist

And run the tests with:
py.test --boxed

So that each test gets run in it's own Python instance.
