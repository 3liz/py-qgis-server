SRCDIR=$(pwd) source tests/tests.env
export $(cut -d= -f1 tests/tests.env)
qgisserver
