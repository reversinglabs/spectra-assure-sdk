# Integration tests

These tests run the SDK against a live Spectra Assure Portal. The offline unit tests are in `../tests_unit/`.

Everything here runs through `make`, against one endpoint at a time. The first failing test stops the run, and `make` fails exactly when the tests do.

## Running them

From the repository root, after the wheel has been built:

```
make tests-all            # staging, playground1, playground2, in that order
make tests-staging        # one endpoint; also tests-playground1, tests-playground2
make tests-production     # on demand
make tests-canada         # on demand, when access to it is available
```

From this directory:

```
make ENDPOINT=staging          # clean, type-check, then run the tests
make tests ENDPOINT=staging    # run the tests only
make sweep ENDPOINT=staging    # remove what interrupted runs left (see below)
```

### Only the Catalog API

```
make tests-staging ONLY_CATALOG=1         # from the repository root
make ENDPOINT=staging ONLY_CATALOG=1      # from this directory
```

`ONLY_CATALOG=1` tests the Catalog API and nothing else. It is meant for an endpoint where the Catalog API is new and there is little other data to test against, such as staging. Only `test_example.py` runs, and the example program runs only its Catalog section (it gets `RLPORTAL_ONLY_CATALOG=1`). `tests-all` refuses the flag, because it copies the example to `../examples/` only after a full run.

`tests-all` stops at the first failing test, including on the endpoints it has not reached yet. Only when all three endpoints have passed does it copy `api_client_example.py` to `../examples/`.

## Endpoints

Each endpoint is one row of the table in the `Makefile`:

| `ENDPOINT` | Env file in your home directory | TLS verification | In `tests-all` |
| --- | --- | --- | --- |
| `staging` | `.envfile_rl-scanner-cloud-staging` | off (self-signed certificate) | yes |
| `playground1` | `.envfile_rl-scanner-cloud-playground` | on | yes |
| `playground2` | `.envfile_rl-scanner-cloud-playground2` | on | yes |
| `production` | `.envfile_rl-scanner-cloud` | on | no, on demand |
| `canada` | `.envfile_rl-scanner-cloud-canada` | on | no, on demand |

There is no default endpoint. Without `ENDPOINT`, with an unknown name, or with a missing env file, `make` stops and says why. The old `TEST_STAGING=1`-style variables are refused with a message naming their replacement.

To add an endpoint, add a row: `ENV_FILE_<name>`, and `NO_SSL_VERIFY_<name> := 1` only if its certificate is self-signed. Then add the name to `ENDPOINTS`.

### The env files

They are never committed, and other scripts use them too. Each holds `export KEY=VALUE` lines:

```
export RLPORTAL_HOST="my.secure.software"
export RLPORTAL_SERVER="demo"
export RLPORTAL_ORG="..."
export RLPORTAL_GROUP="..."
export RLPORTAL_ACCESS_TOKEN="..."
```

- `RLPORTAL_HOST` and `RLPORTAL_SERVER`: at least one; see the SDK's README for how they combine.
- `RLPORTAL_GROUP`: a group dedicated to testing. The tests create and delete projects in it and scan files, which uses analysis capacity.
- The token's role must allow approving and rejecting versions.

The Makefile reads the file without shell tracing, so its contents never reach a log. The tests show the token as `***` wherever pytest prints a value.

## What runs

| Module | What it checks |
| --- | --- |
| `test_connection.py` | the client's settings given as arguments, from a configuration file, and both |
| `test_groups.py` | the organization's groups and the group's projects; `RLPORTAL_SLOW=1` also lists every project, package and version |
| `test_projects.py` | a project is created, listed, edited and deleted |
| `test_packages.py` | the same for a package |
| `test_versions.py` | one scanned version: listed, edited, checks, each report type, the RL-SAFE archive, then the approval states, download, rescan, delete |
| `test_community.py` | the four Spectra Assure Community calls (read-only) |
| `test_audit_log.py` | an audit-log export of the last 30 days, and its status |
| `test_example.py` | `api_client_example.py` runs to the end without an error |

`test_versions.py` follows the Portal's approval rules. A new version is pending, and only a pending version can be rejected. A rejected version can still be approved, and only an approved one can be revoked; revoked is final. So the version is rejected, approved, downloaded (and checked against the uploaded file), and revoked last.

Any answer a test does not expect fails it, a 404 included. The example program stops at the first error answer as well. It accepts only 409 (a version that already exists) and 429 (the SDK waits that out).

Before any endpoint is touched, `make` runs a selftest. It proves that a deliberately failing test fails the `make` run and that a passing one does not.

## Results

Each run writes `results/<endpoint>/<date-time>/`, whether it passes or fails:

- `pytest.1`, `pytest.2`: pytest's stdout and stderr, as shown on the terminal;
- `junit.xml`: one entry per test;
- `run.log`: the INFO-level log;
- `downloads/`: what the tests downloaded;
- `api_client_example.1`, `api_client_example.2`, `api_client_example.log`: the example program's stdout, stderr and DEBUG-level log.

The results of earlier runs are kept: `make ENDPOINT=<name>` cleans everything else first, but not `results/`. Only `make clean`, here or at the top level, removes them; the top-level `prep`, `build` and the `tests-*` targets clean everything else. Git ignores `results/`.

## Test data, and `make sweep`

Everything a run creates is named after its run id, `sdktest-<endpoint>-<yyyymmdd>-<hhmmss>-<4 hex>`, plus a suffix such as `-versions`. The run deletes it all when it ends, also after a failed test.

A run that is interrupted (killed, a lost connection) cannot clean up. `make sweep ENDPOINT=<name>` removes such leftovers, with three safeguards:

- **Names:** it only deletes projects whose name has that shape for this endpoint.
- **Age:** it only deletes those older than `SWEEP_AGE_HOURS` (24 by default), so a run still going on is safe.
- **Dry run:** `SWEEP_DRY_RUN=1` lists what it would delete, and deletes nothing.

## Settings

| Variable | Default | Effect |
| --- | --- | --- |
| `RLPORTAL_WAIT_LIMIT` | 1800 | seconds to wait for an analysis, a report or an archive |
| `RLPORTAL_POLL_PAUSE` | 15 | seconds between two polls |
| `RLPORTAL_SLOW` | unset | `1` runs the walk over the whole group |
| `SWEEP_AGE_HOURS` | 24 | how old a leftover must be before `make sweep` deletes it |
| `SWEEP_DRY_RUN` | unset | `1` makes `make sweep` only list |

## The scan artifact

The scan tests upload `eicarcom2.zip`, the EICAR test file. The Makefile copies it from `~/Downloads/eicar/` into `input/`, because downloading it directly does not work behind GlobalProtect. If it is missing there, the copy fails, naming the missing file, and the run stops before any test.

## The example program

`api_client_example.py` is both a test and the published example, so it must stay readable.

The tests pass it the run id as `RLPORTAL_RUN_ID`, so its project gets a unique name. Run by hand, it uses fixed names and handles a rerun over them.

It scans itself, and writes `downloads/`, `export_profile.*.json` and a log into this directory. `make test_clean` removes them. Under the tests, the log is moved to the run's results folder when the program ends.

## Type checking

`make mypy` and `make mypy-stubs` check this directory's code strictly against the installed wheel. The first uses the wheel's own type hints, the second the generated stubs in `../stubs/`. The top-level `make mypy2` covers it as well.
