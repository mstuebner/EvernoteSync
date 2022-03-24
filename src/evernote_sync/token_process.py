# https://gist.github.com/brettkelly/5041037
# Python OAuth example
from evernote.api.client import EvernoteClient
from http.server import HTTPServer, BaseHTTPRequestHandler
import webbrowser

COMSUMER_KEY = ''
CONSUMER_KEY_SECRET = ''
CALLBACK_URL = 'http://localhost:5555'


##
# Helper function to turn query string parameters into a
# Python dictionary
##
def parse_query_string(authorize_url):
    if 'oauth_token' not in authorize_url:
        return {}

    uargs = authorize_url.split('?')
    vals = {}

    if len(uargs) == 1:
        raise Exception('Invalid Authorization URL')
    for pair in uargs[1].split('&'):
        key, value = pair.split('=', 1)
        vals[key] = value
    return vals


##
# Create an instance of EvernoteClient using your API
# key (consumer key and consumer secret)
##
client = EvernoteClient(
    consumer_key=COMSUMER_KEY,
    consumer_secret=CONSUMER_KEY_SECRET,
    sandbox=True)

request_token = client.get_request_token(CALLBACK_URL)
auth_url = client.get_authorize_url(request_token)

print(f'Open: {auth_url} to display access grant page.')
webbrowser.open(auth_url, new=2)

vals = None


# Webserver to handle callback
class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        global vals
        vals = parse_query_string(self.requestline)
        self.close_connection = True


httpd = HTTPServer(('localhost', 5555), SimpleHTTPRequestHandler)
httpd.handle_request()

print(f"Auth Token: {request_token['oauth_token']}")
print(f"Auth Secret: {request_token['oauth_token_secret']}")
print(f"OAuth verifier: {vals['oauth_verifier']}")

access_token = client.get_access_token(
    request_token['oauth_token'],
    request_token['oauth_token_secret'],
    vals['oauth_verifier']
)

# Create a new client using the auth token
print(f'Access token: {access_token}, trying it out...')

client = EvernoteClient(token=access_token)
userStore = client.get_user_store()
user = userStore.getUser()
if user:
    print('Token tested successfully')
