from dataclasses import dataclass

UNKNOWN_ERROR_CODE = 100


@dataclass
class RespError(Exception):
    error_code: int = UNKNOWN_ERROR_CODE
    message: str = "unknown error"
    log_id: str = ''
    req_key: str = ''

    def __str__(self):
        return f'RespError, error_code: {self.error_code}, message: {self.message}, log_id: {self.log_id}, req_key: {self.req_key}'
