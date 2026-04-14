from fastapi import HTTPException, status
from . import body as RespBody


class ApiError(HTTPException):
    status_code: int = 500
    code: str = "api_error"
    message: str = "API error"

    def __init__(
        self,
        *,
        message: str | None = None,
        code: str | None = None,
    ) -> None:
        super().__init__(
            status_code=self.status_code,
            detail={
                "code": code or self.code,
                "message": message or self.message,
            },
        )

    @classmethod
    def openapi(cls, description: str | None = None) -> dict:
        return {
            "model": RespBody.ErrorResponse,
            "description": description or cls.message,
            "content": {
                "application/json": {
                    "example": {
                        "detail": {
                            "code": cls.code,
                            "message": cls.message,
                        }
                    }
                }
            },
        }
    

class AuthExpiredSession(ApiError):
    status_code = status.HTTP_401_UNAUTHORIZED
    code = "expired_session"
    message = "Your session is over, become anonymous or log back in."

class AuthPoorAttempt(ApiError):
    status_code = status.HTTP_400_BAD_REQUEST
    code = "auth_poor_attempt"
    message = "Something is wrong with your request, the server did not accept it."

class AuthTokenPayloadInvalid(ApiError):
    status_code = status.HTTP_406_NOT_ACCEPTABLE
    code="token_payload_invalid"
    message="Authorization token payload has invalid format"
