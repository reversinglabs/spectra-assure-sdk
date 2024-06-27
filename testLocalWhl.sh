#! /usr/bin/env bash

set -x

WHAT="spectra?assure?sdk"
VERSION_FILE="./spectra_assure_api_client/version.py"

get_version()
{
    # sets VERSION and PACKAGE_FILE
    export VERSION=$(
        cat "${VERSION_FILE}" |
        awk '
        /VERSION/ && /=/ {
            version=$NF;
            gsub(/"/,"", version);
            print version
        }
        '
    )

    echo "VERSION: ${VERSION}" >&2

    [ -z "${VERSION}" ] && {
        echo "FATAL: version is not found in '$VERSION_FILE'" >&2
        exit 101
    }

    export PACKAGE_FILE=$( ls dist/${WHAT}-${VERSION}-py3-none-any.whl)

    echo "Dist now contains:"
    ls -l "${PACKAGE_FILE}"

    [ ! -f "${PACKAGE_FILE}" ] && {
        echo "FATAL: cannot find the package file: ${PACKAGE_FILE}" >&2
        exit 101
    }
}

cleanupVenv()
{
    rm -rf ${VENV}
}

makeVenv()
{
    ${MIN_PYTHON_VERSION} -m venv ${VENV}
    source ./${VENV}/bin/activate
}

installFromDistWhl()
{
    ls -l "${PACKAGE_FILE}"

    which pip3 | grep "${VENV}" || {
        # verify we are using the pip3 from the virtual env
        echo "FATAL: we are not using the virtual env programs" >&2
        exit 101
    }

    pip3 install "${PACKAGE_FILE}"
    pip3 list # show the currently installed packages
}

main()
{
    get_version
    cleanupVenv
    makeVenv
    installFromDistWhl
}

main $@
