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

    export PACKAGE_FILE=$(
        ls dist/${WHAT}-${VERSION}-py3-none-any.whl
    )

    echo "Dist now contains:"
    ls -l "${PACKAGE_FILE}"

    [ ! -f "${PACKAGE_FILE}" ] && {
        echo "FATAL: cannot find the package file: ${PACKAGE_FILE}" >&2
        exit 101
    }
}


makeVenv()
{
    rm -rf ${VENV}
    ${MIN_PYTHON_VERSION} -m venv ${VENV}
    source ./${VENV}/bin/activate
}

installFromDistWhl()
{
    ls -l "${PACKAGE_FILE}"

    which pip3 |
    grep "${VENV}" || {
        # verify we are using the pip3 from the virtual env
        echo "FATAL: we are not using the virtual env programs" >&2
        exit 101
    }

    pip3 \
        --require-virtualenv \
        --disable-pip-version-check \
        --no-color \
        --no-cache-dir \
        install "${PACKAGE_FILE}"
}

main()
{
    get_version
    makeVenv
    installFromDistWhl
}

main "$@"
