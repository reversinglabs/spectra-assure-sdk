import logging

# real operations
from spectra_assure_api_client.operations.checks import SpectraAssureApiOperationsChecks
from spectra_assure_api_client.operations.create import SpectraAssureApiOperationsCreate
from spectra_assure_api_client.operations.delete import SpectraAssureApiOperationsDelete
from spectra_assure_api_client.operations.edit import SpectraAssureApiOperationsEdit
from spectra_assure_api_client.operations.list import SpectraAssureApiOperationsList
from spectra_assure_api_client.operations.report import SpectraAssureApiOperationsReport
from spectra_assure_api_client.operations.scan import SpectraAssureApiOperationsScan
from spectra_assure_api_client.operations.status import SpectraAssureApiOperationsStatus

# pseudo operation
from spectra_assure_api_client.operations.download import SpectraAssureApiOperationsDownload

logger = logging.getLogger(__name__)


class SpectraAssureApiOperations(  # pylint: disable=too-many-ancestors
    SpectraAssureApiOperationsCreate,  # Create a project or package in the Portal
    SpectraAssureApiOperationsScan,  # Upload and scan a new version
    SpectraAssureApiOperationsList,  # List all groups, projects, packages, and versions
    SpectraAssureApiOperationsEdit,  # Edit details for a project, package, or version
    SpectraAssureApiOperationsDelete,  # Remove a project, package, or version from the Portal
    SpectraAssureApiOperationsReport,  # Download analysis report for a version
    SpectraAssureApiOperationsStatus,  # Show analysis status for a version
    SpectraAssureApiOperationsChecks,  # Show performed checks for a version
    SpectraAssureApiOperationsDownload,  # Get artifact download link for a version (uses List and Status)
):
    """A class that combines all operations"""
