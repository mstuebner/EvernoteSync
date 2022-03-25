"""
This is a complete and full automatic OAuth process with Evernote.
During the process a local browser is opened to display evernotes access grant page. The
callback url is then processed by a local web browser which is started to process this
one GET request.

# https://gist.github.com/brettkelly/5041037
# Python OAuth example
"""
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from evernote.api.client import EvernoteClient

COMSUMER_KEY = ''
CONSUMER_KEY_SECRET = ''
CALLBACK_URL = 'http://localhost:5555'


def parse_query_string(authorize_url):
    """
    Helper function to turn query string parameters into a
    Python dictionary
    """
    if 'oauth_token' not in authorize_url:
        return {}

    uargs = authorize_url.split('?')
    variables = {}

    if len(uargs) == 1:
        raise Exception('Invalid Authorization URL')
    for pair in uargs[1].split('&'):
        key, value = pair.split('=', 1)
        variables[key] = value
    return variables


##
# Create an instance of EvernoteClient using your API
# key (consumer key and consumer secret)
##
client = EvernoteClient(
    consumer_key=COMSUMER_KEY,
    consumer_secret=CONSUMER_KEY_SECRET,
    sandbox=True)

request_token = client.get_request_token(CALLBACK_URL)
AUTH_URL = client.get_authorize_url(request_token)

print(f'Open: {AUTH_URL} to display access grant page.')
webbrowser.open(AUTH_URL, new=2)

VALS = {}


# Webserver to handle callback
class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    """
    Handler for http requests, here the callback url to take the oauth_verifier from
    """
    # pylint: disable=invalid-name
    def do_GET(self):
        """
        Method processes the GET requests
        """
        self.send_response(200)
        self.end_headers()
        # pylint: disable=global-statement
        global VALS
        VALS = parse_query_string(self.requestline)
        # pylint: disable=attribute-defined-outside-init
        self.close_connection = True  # Check whether this is required


httpd = HTTPServer(('localhost', 5555), SimpleHTTPRequestHandler)
httpd.handle_request()

print(f"Auth Token: {request_token['oauth_token']}")
print(f"Auth Secret: {request_token['oauth_token_secret']}")
print(f"OAuth verifier: {VALS['oauth_verifier']}")

access_token = client.get_access_token(
    request_token['oauth_token'],
    request_token['oauth_token_secret'],
    VALS['oauth_verifier']
)

# Create a new client using the auth token
print(f'Access token: {access_token}, trying it out...')

client = EvernoteClient(token=access_token)
userStore = client.get_user_store()
user = userStore.getUser()
if user:
    print('Token tested successfully')
