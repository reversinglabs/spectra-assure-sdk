# SpectraAssureApiOperationsDownload

A custom download implementation that combines the `list` and `status` calls to get information about the specified version, and downloads only approved versions.
Before they can be downloaded, versions must be approved manually from the Portal web interface.

During the download, you can select what happens if a file already exists.

As requesting a download URL impacts your Portal Download Capacity, we only request the download at the end of the selection process.

## Targets

- Version

## Arguments

- project: str, mandatory. Project containing the version you want to download.
- package: str, mandatory. Package containing the version you want to download.
- version: str | None = None, optional. The version you want to download or None if you want to look at all available versions in the current project/package. By default, only approved versions will be considered download candidates.
- target_dir: mandatory. The directory where the file will be downloaded; MUST exist.
- download_criteria: SpectraAssureDownloadCriteria | None = None, optional. Specify exactly how the download should deal with e.g. verification, overwriting existing files in the target directory, and finding download candidates if the version is not specified.
- auto_adapt_to_throttle: bool = False, optional. If a throttle response is received, you may want to use this option to automatically wait until the data becomes available. Otherwise, no download will take place and an exception will be raised.

### SpectraAssureToolsDownloadCriteria

The download operation needs criteria to select which versions should be downloaded.
Currently only approved versions will be considered as candidates for downloading.

The `SpectraAssureDownloadCriteria` class lets you specify the criteria for how the download operation should execute its task.

```python
    downloadCriteria = SpectraAssureDownloadCriteria(
        with_overwrite_existing_files=False,
        with_verify_after_download=True,
        with_verify_existing_files=True,
        current_strategy=[
            "AllApproved",                        # select all
            "LatestApproved_ByApprovalTimeStamp", # select only one
        ][1],
    )
```

**current_strategy**

The following strategies are supported:

 - `AllApproved`: look at all approved versions in the current `project/package`.
 - `LatestApproved_ByApprovalTimeStamp`: select only one version in the current `project/package` - the version with the latest (most recent) approval date.

**with_overwrite_existing_files**

After candidates have been selected for download, we can specify what happens if the target file already exists.
If this criteria is set to `True`, any existing file in the target directory will be overwritten.

If set to `False` and the target file already exists, we do not overwrite the target file.

**with_verify_existing_files**

If we choose not to overwrite existing files, we can request verification of any already existing file against the `sha256` checksum we have in the Portal for this file.

If the file does not verify correctly, we raise an exception `ExistingTargetFileDigestFailure`.

**with_verify_after_download**

If the file will be overwritten or does not exist, we can specify if we want the downloaded file to be verified after it's downloaded.
The verification is done against the `sha256` checksum we have in the Portal.
If the file does not verify correctly, we raise an exception `DownloadFileDigestFailure`.

Note that every file is always downloaded to a temporary unique file name in the specified target directory, and renamed after it has finished downloading (or after verification, if it has been requested).

The temporary file will be removed on error.

## Responses

The response data of the download operation is a dictionary containing the internal selection criteria and the resulting download path.
Items are stored by version key and relevant data is converted to lowercase, so it may be different from the actual results of `list` and `status`.

The response may be empty if there are no approved download candidates when looking for multiple versions, or when the specified version is not approved.

**Example response**

```python
    {
      'v1.2.3-a': {
        'analysis': 'done',
        'quality': 'fail',
        'hashes': {
          'md5': 'e4968ef99266df7c9a1f0637d2389dab',
          'sha1': 'bec1b52d350d721c7e22a6d4bb0a92909893a3ae',
          'sha256': 'e1105070ba828007508566e28a2b8d4c65d192e9eaf3b7868382b7cae747b397'
        },
        'approved': 'approved',
        'approval-stamp': '2024-05-21t09:58:21.606240z',
        'released': False,
        'targetFilePath': '/home/somebody/downloads/eicarcom2.zip'
      }
    }
```


The following exceptions may be raised:

- SpectraAssureInvalidAction: if the target for download is incorrect.
- SpectraAssureInvalidPath: if there are issues with the target path.
- SpectraAssureUnexpectedNoDataFound: if a https.request did not return any data, but we expected data to arrive.
- SpectraAssureNoDownloadUrlInResult: if the status request does not have a download URL in the response.
- SpectraAssureUnsupportedStrategy: if the selection strategy specified in `downloadCriteria` is invalid.
- UrlDownloaderUnknownHashKey: if we cannot find the proper hash key in the provided hash info dict.
- UrlDownloaderTargetDirectoryIssue: when there are issues with the target directory.
- UrlDownloaderTargetFileIssue: when there are issues with the target file.
- UrlDownloaderTempFileIssue: when there are issues with the temp file.
- UrlDownloaderFileVerifyIssue: when the verification failed for the existing file or for the downloaded file.


## Code example

from [examples/api_client_example.py](../examples/api_client_example.py)

```python

# DOWNLOAD a approved version file
def download_versions(
    api_client: SpectraAssureApiOperations,
    project: str,
    package: str,
) -> None:
    # download only works on approved versions,

    for available_strategy in [
        "AllApproved",  # select all
        "LatestApproved_ByApprovalTimeStamp",  # select only one
    ]:
        download_criteria = SpectraAssureDownloadCriteria(
            with_overwrite_existing_files=False,
            with_verify_existing_files=True,
            with_verify_after_download=True,
            current_strategy=available_strategy,
        )

        target_dir = "./downloads"
        if not os.path.isdir(target_dir):
            os.mkdir(target_dir)

        download_data = api_client.download(
            project=project,
            package=package,
            target_dir=target_dir,
            download_criteria=download_criteria,
        )
        print("Download details: ", json.dumps(download_data, indent=2))
```
