#! /bin/bash

# set -x

[ -z "${MIN_PYTHON_VERSION}" ] && {
    echo "FATAL: no minimal python version set with: MIN_PYTHON_VERSION" >&2
    exit 101
}

[ -z "${PACKAGE_TEST_INSTALL}" ] && {
    echo "FATAL: no package given to install with: PACKAGE_TEST_INSTALL" >&2
    exit 101
}

[ -z ${ENV_FILE} ] && {
    echo "FATAL: no ENV_FILE specified in makefile" >&2
    exit 101
}

[ -z "$*" ] && {
    echo "FATAL: no arguments specified: i cannot work that way" >&2
    exit 101
}

# eval is currently needed as source cannot directly use a variable
eval source ${ENV_FILE}

[ -z ${VENV} ] && {
    echo "FATAL: no VENV path specified in the makefile" >&2
    exit 101
}

rm -rf "${VENV}" downloads-2024*


ddd="downloads-$( date +%Y%m%d-%H%M%S )"
mkdir -p "${ddd}"

${MIN_PYTHON_VERSION} -m venv ${VENV}

source ./${VENV}/bin/activate
pip3 install ${PACKAGE_TEST_INSTALL}

export LOG_LEVEL="DEBUG"

ARGS="--autoAdaptToThrottle --downloadPath=./${ddd} --project=mbootTestProject --package=myPackage"

case $1 in
t[0-9].py)
    export LOG_LEVEL="INFO"
    export ENVIRONMENT="TESTING"
    ARGS="" # args now via config.json
    ;;
esac

python3 $1 $ARGS
exit $?

