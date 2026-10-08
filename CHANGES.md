# Changes

A detailed summary of changes.

## Changes in 1.1.0

Compared with 1.0.14, the previous published version.

**New**

- The File Stream: scan or import standalone files, follow their analysis, approve, reject or revoke them,
  and download their reports, RL-SAFE archives and the files themselves (see [File Stream](./README.md#file-stream)).
- One HTTP session per client, reused by every call. The client can be used as
  `with SpectraAssureApiOperations(...) as client:`, which closes it at the end
  and keeps the client's type for type checkers (see [Sessions](./README.md#sessions)).
- `list_groups`, the new name of `listGroups`.

**Changes to check when upgrading**

- Timeouts: a connect timeout of 10 seconds and a read timeout of 3600 seconds by default replace
  1.0.14's single timeout of 10 seconds, so a slow answer is now waited for up to an hour.
  Set them with `connect_timeout` and `read_timeout` (or `timeout`, the same as `read_timeout`).
- A configuration file whose name does not end in `.json`, or that has no `"SpectraAssureApi"` key,
  raises `SpectraAssureInvalidAction`; 1.0.14 ignored such a file without a word.
- Other problems with the configuration file (missing, unreadable, not valid JSON, not UTF-8, not a JSON object)
  raise `SpectraAssureInvalidAction` too, with the original error as `__cause__`;
  in 1.0.14, `FileNotFoundError` or `json.JSONDecodeError` escaped.
- `url_import` and `purl_import` refuse a bearer token combined with a user name or password, as the API requires;
  1.0.14 documented the rule but sent such a request.
- `approve`, `reject` and `revoke` need a `reason` string, and raise before sending without one.
- `api_version`, `api_domain` and `api_proto` set to `None` are refused.
- Runtime checks raise SDK exceptions instead of `AssertionError` (an `assert` disappears under `python -O`).
- Every SDK exception derives from `SpectraAssureExceptions`; in 1.0.14 the `UrlDownloader...` exceptions did not.
  `SpectraAssureSpecError` is new.
- `download()` honours `must_be_approved=False`; 1.0.14 always set it to `True`.
  With it, versions that are not approved are candidates as well;
  if the latest-approved strategy then finds no approved version, `download()` returns `None`.
- `client.download_criteria` does not exist: the download criteria are made for each call.
- Internal methods are private; their old names, and `listGroups`, are deprecated (see [Deprecations](#deprecations)).

**Other improvements**

- Timeouts set in the configuration file are applied.
- A misspelt setting is reported with a `UserWarning` that suggests the right name.
- `rl_safe_download` waits while the API answers 202 (the archive is being prepared),
  and raises `SpectraAssureWaitTimeoutExceeded` after `max_wait_time_for_archive`.
- Downloading a reproducible build (`build="repro"`) checks the file against that build's hashes.
- To find the latest approved version, approval times are compared as points in time,
  whatever form the Portal writes them in.
- With `auto_adapt_to_throttle`, a 429 is waited out as long as the `Retry-After` header says.
  Download-link requests wait out the rate limit even without it, and a 402 is reported as insufficient download capacity.
- Waiting for an analysis stops when it ends in `ERROR`.
- Proxy passwords are masked in the log; proxy credentials and community names are percent-encoded in URLs.
- Each download writes to its own temporary file, and an existing file is overwritten, also on Windows.
- Upload file names may contain spaces, quotes or characters outside ASCII.
- `make_logger` replaces the handlers it added when it is called again.
- The profile import sends its `replace` flag as `true` or `false`.

## Deprecations

These methods of `SpectraAssureApiOperations` are internal to the SDK and were never part of the documented API:
`do_it_delete`, `do_it_get`, `do_it_patch`, `do_it_post`, `do_it_put`, `execute_with_retry`, `exists_posix_path`, `extract_hashes`, `extract_purl_components`, `extract_target_file_name`, `flatten_list`, `get_customer_context`, `get_path`, `qp_download`, `qp_edit`, `qp_purl_import`, `qp_reject`, `qp_revoke`, `qp_scan`, `qp_status`, `qp_url_import`, `remove_temp_file_if_exists`, `show_debug`, `simple_path_to_posix`.

They now carry a leading underscore. The old names still work, but each call emits a `DeprecationWarning`, and they will be removed in a future major release. `make_logger` and `get_additional_args` stay public.

`listGroups` is the old name of `list_groups`. It still works the same way, but each call emits a `DeprecationWarning`, and it will be removed in a future major release. Use `list_groups`.
