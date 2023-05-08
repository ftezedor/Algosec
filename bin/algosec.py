from multiprocessing import AuthenticationError
from re import template
from typing import Dict
import requests, socket
from requests.models import Response
from xml.etree import ElementTree as ETree
from common import B64, HEX

def http_request(url: str, headers: Dict, method: str="get", payload = "", retries: int=50) -> Response:
    for retry in range(retries):
        if method.lower() not in ["get", "post", "put", "delete"]:
            raise RuntimeError( "Invalid http verb '{}'".format(method) ) 

        try:
            return requests.request(url=url, headers=headers, method=method, data=payload, verify=False, timeout=(50, 30))
        except (socket.gaierror, requests.ConnectionError, requests.ReadTimeout) as e:
            if e.errno != 10054:
                continue
            reconnect()
            print(str(e))
            print("{0}: retrying {1}".format(("#" + str(retry+1)).rjust(4), url))
        except Exception as e:
            print(f"{str(e)}")
            raise
    else:
        raise requests.ConnectionError()

class Algosec:
    _initialised = False
    _baseurl = None
    _session_data = None

    @staticmethod
    def unhide(msg):
        return B64.decode(HEX.decode(msg))

    @staticmethod
    def parse_search_xml(xml: str):
        dom = ETree.fromstring(xml)

        namespaces = {
            'soap': 'http://schemas.xmlsoap.org/soap/envelope/',
            'a': 'https://www.algosec.com/afa-ws'
        }

        rules = dom.findall('./soap:Body' '/a:SearchRuleResponse' '/Rules' '/Rule', namespaces)

        ret = []

        for rule in rules: 
            dct = {}
            for i in rule:
                dct[i.tag] = i.text
            ret.append(dct)

        return ret


    @classmethod
    def login_v1(cls, address: str, user: str, password: str):
        if not cls._session_data == None:
            return

        cls._baseurl = address
        
        url = f"https://{cls._baseurl}/FireFlow/api/authentication/authenticate"

        headers = {
            'Content-Type': 'application/json'
        }

        payload = f'''
           "username": "{user}", 
           "password": "{password}", 
           "domain": 0
        '''

        with http_request(url, headers, 'post', '{'+payload+'}') as resp:
            json = resp.json()
            if json['status'] == 'Success':
                cls._session_data = json['data']
            else:
                print(json)
                raise AuthenticationError(json['messages'][0]['message'])
        
        print(cls._session_data)

    @classmethod
    def login_v2(cls, address: str, username: str, password: str):
        if not cls._session_data == None:
            return

        cls._baseurl = address
        
        url = f"https://{cls._baseurl}/fa/server/connection/login"

        headers = {
            'Cookie': 'PHPSESSID=khcok6hhupgti62q4ab4l26185'
        }

        payload = {
            'username': username,
            'password': password
        }

        print("Contacting {0}".format(url))
        with http_request(url, headers, 'post', payload) as resp:
            json = resp.json()
            if json['status']:
                cls._session_data = json['SessionID']
            else:
                print(json)
                raise AuthenticationError(json['messages'][0]['message'])
        print("Done!")

    @classmethod
    def logout(cls):
        if cls._session_data == None:
            raise Exception("You must log in first")
        
        url = f"https://{cls._baseurl}/fa/server/connection/logout"

        payload = f'session={cls._session_data}'

        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }

        with http_request(url, headers, 'post', payload) as resp:
            json = resp.json()
            if not json['status']:
                print(json)
                raise Exception("Logout error")
        

    @classmethod
    def login(cls, username: str, password: str):
        # replace 127.0.0.1 by the real IP address or dns name of Algosec
        cls._baseurl = '127.0.0.1'
        cls.login_v2(cls._baseurl, username, password)


    @classmethod
    def get_nw_object(cls, device: str, object: str):
        if cls._session_data == None:
            raise Exception("You must log in first")

        if not (device and isinstance(device, str)):
            raise TypeError("device name must be a valid string")
        
        if not (object and isinstance(object, str)):
            raise TypeError("object name must be a valid string")

        url = f"https://{cls._baseurl}/afa/api/v1/networkObject/search/{device}/objects?hierarchyMode=BOTH&objectNames={object}" 

        headers = {
            'Content-Type': 'application/json',
            'Cookie': 'PHPSESSID=' + cls._session_data
        }

        resp = http_request(url, headers)

        resp = resp.json()
        
        if len(resp) > 0 and "ipaddresses" in resp[0]:
            return resp[0]["ipaddresses"]
        else:
            return [object]


    @classmethod
    def search(cls, address: str, field: str = "All"):
        if cls._session_data == None:
            raise Exception("You must log in first")
        
        url = f"https://{cls._baseurl}/afa/api/v1/rule/advancedsearch/full/ALL_FIREWALLS?exactMatch=true&includeAny=false&includeContainment=true" 

        template = """
        {
            "searchQuery" : "(\\\"{{field}}\\\" == {{address}})" 
        }
        """

        # retrieve and treat SOURCE
        payload = template.replace("{{address}}",address).replace("{{field}}", field)

        headers = {
            'Content-Type': 'application/json',
            'Cookie': 'PHPSESSID=' + cls._session_data
        }

        resp = http_request(url, headers, "post", payload)

        return resp.json()


    @classmethod
    def _search(cls, address: str):
        if cls._session_data == None:
            raise Exception("You must log in first")
        
        url = f"https://{cls._baseurl}/AFA/php/ws.php?wsdl"

        template = """<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:afa="https://www.algosec.com/afa-ws">
                        <soapenv:Header/>
                        <soapenv:Body>
                            <afa:SearchRuleRequest>
                                <SessionID>{{sessionid}}</SessionID>
                                <EntityID>ALL_FIREWALLS</EntityID>
                                <EntityType>GROUP</EntityType>
                                <!--1 or more repetitions:-->
                                <SearchFor>
                                    <Search>{{address}}</Search>
                                    <!--Optional:-->
                                    <Field>{{field}}</Field>
                                </SearchFor>
                                <!--Optional:-->
                                <ExactMatch>Yes</ExactMatch>
                                <!--Optional:-->
                                <IncludeAny>No</IncludeAny>
                            </afa:SearchRuleRequest>
                        </soapenv:Body>
                    </soapenv:Envelope>"""

        headers = {
            'Content-Type': 'text/xml',
            'Cookie': 'PHPSESSID=' + cls._session_data
        }

        # retrieve and treat SOURCE
        payload = template.replace("{{sessionid}}",cls._session_data).replace("{{address}}",address).replace("{{field}}","source")

        resp = http_request(url, headers, "post", payload)

        s_rules = Algosec.parse_search_xml(resp.text)

        for rule in s_rules:
            rule['Source'] = address

        # retrieve and treat DESTINATION
        payload = template.replace("{{sessionid}}",cls._session_data).replace("{{address}}",address).replace("{{field}}","destination")

        resp = http_request(url, headers, "post", payload)

        d_rules = Algosec.parse_search_xml(resp.text)

        for rule in d_rules:
            rule['Destination'] = address

        rules = []
        rules.extend(s_rules)
        rules.extend(d_rules)

        return rules

    # end of search method

# end of Algosec class
