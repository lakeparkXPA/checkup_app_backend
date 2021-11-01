from rest_framework import status


class ErrorCollection(object):

    def __init__(self, code, status, message):
        self.code = code
        self.status = status
        self.message = message


    def as_md(self):
        return '\n\n> **%s**\n\n```\n{\n\n\t"code": "%s"\n\n}\n\n```' % \
               (self.message, self.code) # \n\n\t"message": "%s"     self.message
    #TODO ---- add message to return


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
RAISE_400_RELATION_EXISTS = ErrorCollection(
    code='relation_exists',
    status=status.HTTP_400_BAD_REQUEST,
    message='해당 환자는 이미 추가되어 있습니다.'
)
RAISE_400_RELATION_NONEXISTENT = ErrorCollection(
    code='relation_nonexistent',
    status=status.HTTP_400_BAD_REQUEST,
    message='해당 환자가 추가되어 있지 않습니다.'
)
RAISE_400_PID_NONEXISTENT = ErrorCollection(
    code='p_id_nonexistent',
    status=status.HTTP_400_BAD_REQUEST,
    message='해당 환자 번호가 존재하지 않습니다.'
)
RAISE_400_PID_MISSING = ErrorCollection(
    code='p_id_missing',
    status=status.HTTP_400_BAD_REQUEST,
    message='해당 환자 번호가 존재하지 않습니다.'
)
RAISE_400_WRONG_MODE = ErrorCollection(
    code='wrong_mode',
    status=status.HTTP_400_BAD_REQUEST,
    message='해당 모드가 존재하지 않습니다.'
)
RAISE_400_PATIENT_PUSH_TOKEN_NULL = ErrorCollection(
    code='patient_push_token_null',
    status=status.HTTP_400_BAD_REQUEST,
    message='해당 모드가 존재하지 않습니다.'
)


RAISE_401_NO_TOKEN = ErrorCollection(
    code='no_token',
    status=status.HTTP_401_UNAUTHORIZED,
    message='해당 토큰이 존재하지 않습니다.'
)
RAISE_401_NO_REFRESH_TOKEN = ErrorCollection(
    code='no_token',
    status=status.HTTP_401_UNAUTHORIZED,
    message='해당 새로고침 토큰이 존재하지 않습니다.'
)
RAISE_401_REFRESH_TOKEN_EXPIRE = ErrorCollection(
    code='refresh_token_expire',
    status=status.HTTP_401_UNAUTHORIZED,
    message='해당 새로고침 토큰이 만료되었습니다.'
)
RAISE_401_WRONG_REFRESH_TOKEN = ErrorCollection(
    code='wrong_refresh_token',
    status=status.HTTP_401_UNAUTHORIZED,
    message='해당 새로고침 토큰이 잘못되었습니다.'
)

