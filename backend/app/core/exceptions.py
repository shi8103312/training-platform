"""
Custom Exceptions and Error Codes
"""
from fastapi import HTTPException, status


class BusinessException(HTTPException):
    """
    Business logic exception with custom error code.
    """

    def __init__(
        self,
        code: int,
        message: str,
        status_code: int = status.HTTP_200_OK,
        details: dict = None,
    ):
        super().__init__(
            status_code=status_code,
            detail={
                "code": code,
                "message": message,
                "data": details,
            },
        )
        self.code = code
        self.error_message = message
        self.details = details


class ErrorCode:
    # Authentication errors (10xxx)
    AUTH_FAILED = 10001
    AUTH_TOKEN_EXPIRED = 10002
    AUTH_TOKEN_INVALID = 10003
    AUTH_ACCOUNT_LOCKED = 10004
    AUTH_PERMISSION_DENIED = 10005

    # User errors (11xxx)
    USER_NOT_FOUND = 11001
    USER_ALREADY_EXISTS = 11002
    USER_DISABLED = 11003

    # Department errors (12xxx)
    DEPT_NOT_FOUND = 12001
    DEPT_ALREADY_EXISTS = 12002
    DEPT_HAS_CHILDREN = 12003
    DEPT_IMPORT_ERROR = 12004

    # Training project errors (20xxx)
    PROJECT_NOT_FOUND = 20001
    PROJECT_TITLE_DUPLICATE = 20002
    PROJECT_CANNOT_EDIT = 20003
    PROJECT_CANNOT_DELETE = 20004
    PROJECT_CANNOT_PUBLISH = 20005
    PROJECT_HAS_NO_MATERIALS = 20006

    # Material errors (30xxx)
    MATERIAL_NOT_FOUND = 30001
    MATERIAL_UPLOAD_FAILED = 30002
    MATERIAL_TYPE_INVALID = 30003
    MATERIAL_FILE_TOO_LARGE = 30004
    MATERIAL_EXTENSION_NOT_ALLOWED = 30005

    # Progress errors (40xxx)
    PROGRESS_NOT_FOUND = 40001
    PROGRESS_INVALID_POSITION = 40002

    # Exam errors (50xxx)
    EXAM_NOT_FOUND = 50001
    EXAM_ALREADY_STARTED = 50002
    EXAM_ATTEMPT_EXCEEDED = 50003
    EXAM_NOT_COMPLETED = 50004
    EXAM_PREREQUISITE_NOT_MET = 50005
    EXAM_TIME_EXPIRED = 50006

    # Comment errors (60xxx)
    COMMENT_NOT_FOUND = 60001
    COMMENT_CANNOT_DELETE = 60002

    # Notification errors (70xxx)
    NOTIF_SEND_FAILED = 70001
    NOTIF_NO_RECIPIENTS = 70002

    # Common errors (90xxx)
    VALIDATION_ERROR = 90001
    INTERNAL_ERROR = 90002
    RESOURCE_NOT_FOUND = 90003
    OPERATION_FAILED = 90004


def raise_auth_error(message: str = "认证失败"):
    raise BusinessException(
        code=ErrorCode.AUTH_FAILED,
        message=message,
    )


def raise_token_expired_error():
    raise BusinessException(
        code=ErrorCode.AUTH_TOKEN_EXPIRED,
        message="Token已过期",
    )


def raise_token_invalid_error():
    raise BusinessException(
        code=ErrorCode.AUTH_TOKEN_INVALID,
        message="Token无效",
    )


def raise_account_locked_error():
    raise BusinessException(
        code=ErrorCode.AUTH_ACCOUNT_LOCKED,
        message="账号已锁定，请15分钟后重试",
    )


def raise_permission_denied_error():
    raise BusinessException(
        code=ErrorCode.AUTH_PERMISSION_DENIED,
        message="权限不足",
        status_code=status.HTTP_403_FORBIDDEN,
    )


def raise_not_found_error(resource: str):
    raise BusinessException(
        code=ErrorCode.RESOURCE_NOT_FOUND,
        message=f"{resource}不存在",
    )


def raise_validation_error(message: str):
    raise BusinessException(
        code=ErrorCode.VALIDATION_ERROR,
        message=message,
    )