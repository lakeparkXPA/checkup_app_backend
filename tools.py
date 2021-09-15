import jwt
import datetime
import base64
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import requests
import json

from checkup_backend.settings import ALGORITHM, SECRET_KEY, EMAIL_REFRESH_TOKEN, CLIENT_SECRET, CLIENT_ID


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


def mail_token(token):
    url = 'https://oauth2.googleapis.com/token'
    body = {
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'refresh_token': token,
        'grant_type': 'refresh_token'
    }
    response = requests.post(url, body)
    return json.loads(response.content)['access_token']


def create_message(sender, to, subject, message_text=None):
    """Create a message for an email.
    Args:
      sender: Email address of the sender.
      to: Email address of the receiver.
      subject: The subject of the email message.
      message_text: The text of the email message.
    Returns:
      An object containing a base64url encoded email object.
    """
    message = MIMEMultipart()
    message['to'] = to
    message['from'] = sender
    message['subject'] = subject

    if message_text != None:
        msg = MIMEText(message_text, 'html')
        message.attach(msg)
    try:
        return {'raw': base64.urlsafe_b64encode(message.as_string())}
    except:
        return {'raw': base64.urlsafe_b64encode(message.as_bytes()).decode('utf8')}


def sendmail(to, subject, message_text_html):
    # access_token = EMAIL_TOKEN
    user_id = 'hello@docl.org'
    access_token = mail_token(EMAIL_REFRESH_TOKEN)

    url = 'https://www.googleapis.com/gmail/v1/users/' + user_id + '/messages/send'

    request_header = {
        "Content-Type": "application/json",
        "Authorization": "Bearer " + access_token,
        "X-GFE-SSL": "yes"
    }

    payload = create_message(user_id, to, subject, message_text_html)

    requests.post(url, headers=request_header, data=json.dumps(payload))





code = 1234
sendmail(
                    to='hjshljy@gmail.com',
                    subject='CheckUP Password Reset Confirmation Code.',
                    message_text_html='CheckUp DOCL Password Reset<br>' +
                    'Your code to reset the password of CheckUp DOCL is <br><br><h2>'+str(code)+
                    '</h2><br><br> Please enter the site linked below and enter the code.<br>'+
                    'https://testapi.docl.org <br><br>Thank you,<br>Sincerely DOCL.'
                )