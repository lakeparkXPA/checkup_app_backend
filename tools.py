import jwt
import datetime
from checkup_backend.settings import ALGORITHM, SECRET_KEY


def make_token(token_id, auth='patient'):
    payload = {}
    payload['auth'] = auth
    payload['id'] = token_id
    payload['exp'] = datetime.datetime.utcnow() + datetime.timedelta(hours=300)

    return jwt.encode(payload, SECRET_KEY, ALGORITHM)


def get_id(token):
    decoded_token = jwt.decode(token, SECRET_KEY, ALGORITHM)
    return decoded_token['id']


def bool_dic(data, data_lst):
    data_dic = {}
    for d in data_lst:
        if d in data:
            data_dic[d] = 1
        else:
            data_dic[d] = 0
    return data_dic

