"""Specification-derived routing tables.

Internal to the SDK: nothing here is part of the customer-facing contract.
"""

from .index import (
    Operation,
    SpectraAssureSpecError,
    get_operation,
    operation_ids,
)
from .routes import (
    FILESTREAM_REPORT_OPERATIONS,
    PSEUDO_ACTIONS,
    ROUTES,
    resolve,
    resolve_filestream_report,
    routed_operation_ids,
)

__all__ = [
    "FILESTREAM_REPORT_OPERATIONS",
    "PSEUDO_ACTIONS",
    "ROUTES",
    "Operation",
    "SpectraAssureSpecError",
    "get_operation",
    "operation_ids",
    "resolve",
    "resolve_filestream_report",
    "routed_operation_ids",
]
