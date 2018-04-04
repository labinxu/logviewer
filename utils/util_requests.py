import requests
import platform
import logging


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


if platform.system() == 'Windows':
    from requests_ntlm import HttpNtlmAuth
    from requests_kerberos import HTTPKerberosAuth, REQUIRED
    from bs4 import BeautifulSoup

# disable the ssl warnings
from requests.packages import urllib3
urllib3.disable_warnings()

class UtilityRequests():
    def __init__(self, domain='ccr'):
        """
        @param: content web page content
        @param: htmlparser web page parser HTMLParser or bs4.BeautifulSoup
        """
        self.domain = domain
        self.session = requests.Session()
        self.auth = None
        self.status_code = None

    def setHeaders(self, headers):
        self.session.headers = headers

    def makeNtlmAuth(self, username, password):
        logger.debug('[+] Make HttpNtlmAuth %s' % username)
        auth = HttpNtlmAuth('%s\\%s' % (self.domain, username),
                            password, self.session)

        self.auth = auth

    def makeKerberosAuth(self):
        auth = HTTPKerberosAuth(mutual_authentication=REQUIRED,
                                sanitize_mutual_error_response=False)
        self.auth = auth

    def makeAuth(self, username, password):
        self.auth = (username, password)

    def getContent(self, url):
        return self.get(url).content

    def get(self, url):
        logger.debug('[+] Get: %s' % url)
        response = self.session.get(url, auth=self.auth, verify=False)
        self.status_code = response.status_code
        return response

    def getSoup(self, url):
        r = self.get(url)
        return BeautifulSoup(r.text.encode('utf-8'), 'html.parser')

    def post(self, url, data):
        logger.debug('[+] Post %s' % url)
        return self.session.post(url,data=data)

    def postSoup(self, url, data):
        r = self.post(url, data=data)
        return BeautifulSoup(r.text.encode('utf-8'), 'html.parser')
