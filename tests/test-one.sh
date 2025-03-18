#! /bin/bash

prep_params()
{
    local name=$(basename ${1} ".py")

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

    [ -z ${VENV} ] && {
        echo "FATAL: no VENV path specified in the makefile" >&2
        exit 101
    }

    echo ${PACKAGE_TEST_INSTALL}

    ddd="downloads/downloads-${name}-$( date +%Y%m%d-%H%M%S )"
    mkdir -p "${ddd}"
}

setup_venv()
{
    ${MIN_PYTHON_VERSION} -m venv ${VENV}
    source ./${VENV}/bin/activate
    pip3 -q \
        --require-virtualenv \
        --disable-pip-version-check \
        --no-color install --no-cache-dir ${PACKAGE_TEST_INSTALL}
}

run_test()
{
    set -x
    export LOG_LEVEL="DEBUG"
    export ENVIRONMENT="TESTING"

    # eval is currently needed as source cannot directly use a variable
    eval source ${ENV_FILE}

    ARGS="--autoAdaptToThrottle --downloadPath=./${ddd} --project=mbootTestProject --package=myPackage"

    python3 $1 ${ARGS}
    exit $?
}

main()
{
    prep_params "$@"
    setup_venv
    run_test "$@"
}

main "$@"
