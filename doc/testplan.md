# Integration tests: requirements and decisions

How the integration tests in `tests/` run is described in `tests/README.md`. This file records what they must do, the decisions behind them, and what could be added later.

## 1. Requirements

These are the requirements as you stated them.

- The tests run through the Makefile against **five endpoint configurations**: staging, playground 1, playground 2, production and Canada.
- **Playground 1 and 2** differ only in how `host` and `server` are passed to the SDK.
- **Playground, production and Canada run the same production code.** Running every test on staging and the playgrounds is enough; production and Canada are tested now and then.
- **Canada is special:** it is never part of `tests-all` and runs only on demand, when access to it is available.
- **Every test endpoint has a dedicated test group,** set in its env file, so the tests may create and delete projects and scan files on all five.
- **Staging (and the development endpoint) use self-signed certificates** on Kubernetes-hosted test environments, so TLS verification must be off there. Playground, production and Canada are internet-hosted with real certificates, and must be verified.
- **The first failing test stops everything,** including the endpoints not yet run.
- **The env files contain only `export KEY=VALUE` lines,** and other scripts use them too, so the tests must not require changes to them.
- **The tests run on the minimal Python version** configured in the Makefile: 3.10 now, 3.11 from November.
- **The top-level Makefile** decides which endpoint runs.
- **Every test must finish without errors.** The first error must stop the rest of the `make` run.
- **Endpoint settings are never committed.** They are read from hidden files in the user's home directory.
- **The example program** `tests/api_client_example.py` is copied to `examples/` after it has run successfully.

## 2. Decisions

The decisions behind the way the tests work:

| # | Question | Decision |
| --- | --- | --- |
| 1 | Is Canada part of `tests-all`? | No. Canada is special and runs only on demand, when access to it is available. |
| 2 | Which endpoints need TLS verification off? | Staging, and the development endpoint: both use self-signed certificates on Kubernetes-hosted environments. Playground, production and Canada have real certificates and are verified. |
| 3 | May the tests create, delete and scan on production? | Playground, production and Canada run the same production code, so every test runs on playground and production and Canada are tested now and then. Each endpoint's env file names a dedicated test group, so the full suite may run on any of them. |
| 4 | May the test token approve versions? | Yes; the download test approves through the API. |
| 5 | Stop at the first failure, or run on? | Stop at the first failing test, across endpoints too. |
| 6 | What is in the env files? | Only `export KEY=VALUE` lines, and other scripts use them too; the tests don't require changes to them. |
| 7 | Which Python version? | The minimal version configured in the Makefile at the time of the run: 3.10 now, 3.11 from November. |
| 8 | Canada's env file? | `~/.envfile_rl-scanner-cloud-canada`, with `RLPORTAL_HOST="ca.secure.software"` and `RLPORTAL_SERVER="test2"`. |
| 9 | When is the example copied to `examples/`? | Only after all tests have passed. |
| 10 | Is a 404 a failure? | Yes, always: an answer the full test does not expect means the run did not produce the expected results. For example, an endpoint without the File Stream answers the example's File Stream calls with 404, and the run fails. (Only clean-up treats a 404 as "already deleted".) |

## 3. Possible later additions

None of these is needed now.

- a `test_filestream.py` module of its own; the example program covers the File Stream today, and all the regular endpoints now have it;
- an `rl-diff` report test, once its behaviour on a first version is known;
