from rest_framework import status


class ErrorCollection(object):

    def __init__(self, code, status, message):
        self.code = code
        self.status = status
        self.message = message


    def as_md(self):
        return '\n\n> **%s**\n\n```\n{\n\n\t"code": "%s"\n\n\t"message": "%s"\n\n}\n\n```' % \
               (self.message, self.code, self.message)


RAISE_400_EMAIL_MISSING = ErrorCollection(
    code='email_missing',
    status=status.HTTP_400_BAD_REQUEST,
    message='이메일이 존재하지 않습니다.'
)
RAISE_400_EMAIL_FORMAT_INVALID = ErrorCollection(
    code='email_format',
    status=status.HTTP_400_BAD_REQUEST,
    message='이메일 형식이 아닙니다.'
)
RAISE_400_EMAIL_EXIST = ErrorCollection(
    code='email_exist',
    status=status.HTTP_400_BAD_REQUEST,
    message='이메일이 존재합니다.'
)
RAISE_400_EMAIL_NONEXISTENT = ErrorCollection(
    code='email_nonexistent',
    status=status.HTTP_400_BAD_REQUEST,
    message='이메일이 존재합니다.'
)
RAISE_400_WRONG_PASSWORD = ErrorCollection(
    code='wrong_password',
    status=status.HTTP_400_BAD_REQUEST,
    message='비밀번호가 틀렸습니다.'
)
RAISE_400_WRONG_EMAIL = ErrorCollection(
    code='wrong_email',
    status=status.HTTP_400_BAD_REQUEST,
    message='이메일이 틀렸습니다.'
)
RAISE_400_PASSWORD_NOT_SAME = ErrorCollection(
    code='password_not_same',
    status=status.HTTP_400_BAD_REQUEST,
    message='두 비밀번호가 다릅니다.'
)
RAISE_400_CODE_MISSING = ErrorCollection(
    code='code_missing',
    status=status.HTTP_400_BAD_REQUEST,
    message='코드가 없습니다.'
)
RAISE_400_WRONG_CODE = ErrorCollection(
    code='wrong_code',
    status=status.HTTP_400_BAD_REQUEST,
    message='코드가 틀렸습니다.'
)
RAISE_400_TIME_EXPIRE = ErrorCollection(
    code='time_expire',
    status=status.HTTP_400_BAD_REQUEST,
    message='코드 제한시간을 초과했습니다.'
)
RAISE_400_CODE_NONEXISTENT = ErrorCollection(
    code='code_nonexistent',
    status=status.HTTP_400_BAD_REQUEST,
    message='존재하지 않는 코드입니다.'
)
RAISE_403_NO_TOKEN = ErrorCollection(
    code='no_token',
    status=status.HTTP_403_FORBIDDEN,
    message='해당 토큰이 존재하지 않습니다.'
)
RAISE_403_TOKEN_EXPIRE = ErrorCollection(
    code='token_expire',
    status=status.HTTP_403_FORBIDDEN,
    message='해당 토큰이 만료되었습니다.'
)