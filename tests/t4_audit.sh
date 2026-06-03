#! /bin/bash

source ~/.envfile_rl-scanner-cloud-staging

export LOG_LEVEL=DEBUG
export ENVIRONMENT=DEVELOPMENT

python3 t4_audit.py
