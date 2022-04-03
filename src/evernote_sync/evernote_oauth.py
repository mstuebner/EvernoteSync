"""
Implements the OAuth process for Evernote
"""
import logging
from urllib.parse import urlparse
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from evernote.api.client import EvernoteClient

from config_model import settings

logging.basicConfig(level=logging.WARN)
LOGGER = logging.getLogger('evernote_oauth')

VALS = {}


class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    """
    Handler for http requests, here the callback url to take the oauth_verifier from
    """
    # pylint: disable=invalid-name
    def do_GET(self):
        """
        Method processes the GET requests
        """
        LOGGER.debug('Received GET request: %s', self.requestline)
        # pylint: disable=global-statement
        global VALS

        self.send_response(200)
        self.end_headers()

        VALS = self.parse_query_string(self.requestline)
        LOGGER.debug('GET request proccessed')

    @staticmethod
    def parse_query_string(authorize_url):
        """
        Helper function to turn query string parameters into a
        Python dictionary
        """
        if 'oauth_token' not in authorize_url:
            LOGGER.debug("'oauth_token' was not found in authorize_url. OAutj process failed.")
            return {}

        uargs = authorize_url.split('?')
        variables = {}

        if len(uargs) == 1:
            raise Exception('Invalid Authorization URL')
        for pair in uargs[1].split('&'):
            key, value = pair.split('=', 1)
            variables[key] = value
        return variables

    # pylint: disable=arguments-differ, unused-argument
    def log_message(self, str_format, *args):
        """
        Overrides BaseHTTPRequestHandler.log_message() because this method isn't using logging
        """
        LOGGER.debug(args[0])


class EvernoteOAuth:
    """
    Class implements the OAuth process used by Evernote
    """
    def __init__(self, consumer_key, consumer_secret, callback_url, sandbox=True):
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        self.callback_url = callback_url
        self.sandbox = sandbox

        self.client = None
        LOGGER.debug('EvernoteOAuth instantiated')

    def get_request_token(self):
        """
        Method returns the request token
        """
        self.client = EvernoteClient(
            consumer_key=self.consumer_key,
            consumer_secret=self.consumer_secret,
            sandbox=self.sandbox)
        LOGGER.debug('EvernoteClient instantiated to start token process')

        request_token = self.client.get_request_token(self.callback_url)
        LOGGER.debug('request_token: %s', request_token)
        return request_token

    def get_auth_url(self, request_token):
        """
        Method returns the authentication url
        """
        auth_url = self.client.get_authorize_url(request_token)
        LOGGER.debug('AuthUrl: %s', auth_url)
        return auth_url

    @staticmethod
    def open_access_grant_page(auth_url):
        """
        Method opens the authentication url in the default borowser to allow or to grant or to reject request
        """
        LOGGER.debug('Open: auth_url in a new browser tab to display access grant page.')
        webbrowser.open(auth_url, new=2)

    @staticmethod
    def _url_and_port_from_callbackurl(callback_url: str):
        """
        Method extracts the url and port to use from callback_url
        """
        default_port = 80

        _parsed_callback = urlparse(callback_url)
        url = _parsed_callback.hostname
        port = _parsed_callback.port if _parsed_callback.port else default_port

        if url:
            return url, port
        else:
            raise Exception('Could not process callback url')

    def handle_access_grant_return(self):
        """
        Method starts a local http server to receive and to process the request from authentication page
        """
        url, port = self._url_and_port_from_callbackurl(callback_url=self.callback_url)
        LOGGER.debug('Open HTTPServer on url "%s" and port "%s"', url, port)

        httpd = HTTPServer((url, port), SimpleHTTPRequestHandler)
        httpd.handle_request()
        LOGGER.debug('Close HTTPServer')

    def get_access_token(self, request_token, auth_verifier):
        """
        Method returns the access token
        """
        acc_token = self.client.get_access_token(
            request_token['oauth_token'],
            request_token['oauth_token_secret'],
            auth_verifier
        )

        LOGGER.debug(f'Access token: {acc_token}')
        return acc_token

    @staticmethod
    def get_auth_verifier() -> str:
        """
        Method returns the oauth_verifier or throws an exception if none was found
        """
        try:
            oauth_verifier = VALS['oauth_verifier']
            return oauth_verifier
        except KeyError:
            raise Exception('Access request was rejected') from None

    @staticmethod
    def test_access_token(acc_token):
        """
        Method gets the access token as parameter, instantiates an EvernoteClient from it and tries to acess the
        UserStore as prove that the access token is valid. Returns True if successful or False otherwise.
        """
        client = EvernoteClient(token=acc_token)
        user_store = client.get_user_store()
        user = user_store.getUser()
        if user:
            return True
        return False

    def process_token_request(self):
        """
        Method runs the whole process and returns the final access token
        """
        _rqt = self.get_request_token()
        _aurl = self.get_auth_url(request_token=_rqt)
        self.open_access_grant_page(auth_url=_aurl)
        self.handle_access_grant_return()
        _auth_verifier = self.get_auth_verifier()
        _access_token = self.get_access_token(request_token=_rqt, auth_verifier=_auth_verifier)

        return _access_token


if __name__ == '__main__':

    oauth = EvernoteOAuth(consumer_key=settings.consumer_key,
                          consumer_secret=settings.consumer_secret,
                          callback_url=settings.callback_url,
                          sandbox=settings.sandbox)

    access_token = oauth.process_token_request()

    if oauth.test_access_token(acc_token=access_token):
        print(f'Token "{access_token}" tested successfully')
    else:
        print('Token FAILED')
