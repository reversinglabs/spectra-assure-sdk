"""
/audit-log/export:
  post:
    operationId: export_job_create
    summary: Create a new export job
    description: >
      Creates an export job and immediately returns. Background processing starts asynchronously
    tags:
      - Audit

    requestBody:
      required: true
      content:
        application/json:
          schema:
            $ref: "#/components/schemas/CreateExportJobRequest"
          examples:
            both_formats:
              summary: Request both CEF and JSON
              value:
                name: "April audit export"
                datetime_start: "2025-01-01T00:00:00Z"
                datetime_end: "2025-04-01T00:00:00Z"
                filters:
                  action:
                    operation: is_any
                    values: [ "package.created", "package.deleted" ]
                should_create_cef: true
                should_create_json: true
            cef_only:
              summary: CEF only
              value:
                name: "CEF export"
                datetime_start: "2025-01-01T00:00:00Z"
                datetime_end: "2025-04-01T00:00:00Z"
                filters: []
                should_create_cef: true
                should_create_json: false
    responses:
      "201":
        description: Export job created. Processing has started in the background.
        content:
          application/json:
            schema:
              $ref: "#/components/schemas/ExportJob"
            example:
              id: "3fa85f64-5717-4562-b3fc-2c963f66afa6"
              name: "April audit export"
              cef_status: "IN_PROGRESS"
              cef_presigned_url: null
              cef_expires_at: null
              ndjson_status: "IN_PROGRESS"
              ndjson_presigned_url: null
              ndjson_expires_at: null
      "400":
        $ref: "../schemas/error_schemas.yaml#/responses/BadRequest"
      "401":
        $ref: "../schemas/error_schemas.yaml#/responses/Unauthorized"
      "403":
        $ref: "../schemas/error_schemas.yaml#/responses/Forbidden"
      "404":
        $ref: "../schemas/error_schemas.yaml#/responses/NotFound"
      "429":
        $ref: "../schemas/error_schemas.yaml#/responses/TooManyRequests"
      "500":
        $ref: "../schemas/error_schemas.yaml#/responses/ServerError"

  CreateExportJobRequest:
    type: object
    properties:
      name:
        type: string
        maxLength: 255
        example: "April audit export"
        required: true
      filters:
        type: array
        default: [ ]
        description: >
          List of filter conditions to apply. Each field may appear at most
          once. All conditions are ANDed together.
        items:
          $ref: "#/components/schemas/AuditFilterCondition"
      should_create_cef:
        type: boolean
        description: Whether to generate a CEF export file.
        required: true
      should_create_json:
        type: boolean
        description: Whether to generate a JSON export file.
        required: true
      datetime_start:
        type: string
        format: date-time
        description: Start of the time range (inclusive). Must be earlier than `datetime_end`.
        example: "2025-01-01T00:00:00Z"
        required: true
      datetime_end:
        type: string
        format: date-time
        description: End of the time range (exclusive).
        example: "2025-04-01T00:00:00Z"
        required: true
    required:
      - name
      - should_create_cef
      - should_create_json
      - datetime_start
      - datetime_end

  AuditFilterCondition:
    type: object
    required: [ filter_by, operation, values ]
    description: A single filter condition applied to one audit log field.
    properties:
      filter_by:
        required: true
        type: string
        description: The field to filter on.
        enum:
          - action
          - outcome
          - auth_context
          - resource_type
          - group_id
          - request_id
          - resource_id
          - user_id
          - user_email
      operation:
        required: true
        type: string
        description: >
          The comparison operator. Allowed operators depend on the field:
          `action` and `resource_type` allow all four;
          `group_id` allows `is` and `is_any`; all other fields allow `is` only.
          `is` / `is_not` use only the first value.
        enum: [ is, is_not, is_any, is_not_any ]
      values:
        required: true
        type: array
        minItems: 1
        description: >
          One or more filter values. For `is` and `is_not` only the first
          element is used; the rest are ignored.
        items:
          type: string
    example:
      filter_by: action
      operation: is_any
      values: [ "package.created", "package.deleted" ]
"""

import logging
from typing import (
    Any,
)

from spectra_assure_api_client.communication.exceptions import (
    SpectraAssureInvalidAction,
)

from .base import SpectraAssureApiOperationsBase

logger = logging.getLogger(__name__)

"""
params:
  required:
    - name
    - should_create_cef
    - should_create_ndjson
    - datetime_start
    - datetime_end
  optional:
    - filters # []
"""


class SpectraAssureApiOperationsAuditLogExport(  # pylint: disable=too-many-ancestors
    SpectraAssureApiOperationsBase,
):  # pylint: disable=too-many-instance-attributes
    def audit_log_export(
        self,
        *,  # force name based params
        name: str,
        datetime_start: str,
        datetime_end: str,
        should_create_cef: bool = False,
        should_create_ndjson: bool = False,
        filters: list[Any] | None = None,
        auto_adapt_to_throttle: bool = False,
        **qp: Any,  # ignored
    ) -> Any:
        if filters:
            if not isinstance(filters, list):
                msg = "when filters is specified it must be a list"
                raise SpectraAssureInvalidAction(message=msg)

        action = "audit_log_export"
        url = self._make_current_url_community(
            action=action,
        )
        logger.debug("url is now: %s", url)

        post_data = {
            "name": name,
            "should_create_cef": should_create_cef,
            "should_create_ndjson": should_create_ndjson,
            "datetime_start": datetime_start,
            "datetime_end": datetime_end,
        }

        if filters:
            z: list[Any] = []
            for item in filters:
                z.append(item)
            post_data["filters"] = z
        logger.debug("post_data is now: %s", post_data)

        return self.do_it_post(
            action=action,
            url=url,
            auto_adapt_to_throttle=auto_adapt_to_throttle,
            post_data=post_data,
        )
