from requests.auth import HTTPBasicAuth
from json import dumps

import requests
import os
import re
import logging
import datetime 
import threading 
bad_resp_match = lambda status: re.match(r"^[4,5][0-9][0-9]$",status)

def handle_chimp_response(func):
    """Utility function that loggs the error
    """
    def wrapper(*args,**kwargs):
        r = func(*args,**kwargs)
        if bad_resp_match(str(r.status_code)):
            logging.error("Failed to execute mailchimp command")
            logging.error(r.json())
        else:
            logging.info("Mailchimp operation success")
        return r
    return wrapper
def transform_mailchimp_response(json_response):
    l = {}
    count = 0
    for member in json_response['members']:
        data = dict()
        data["email_address"] = member["email_address"]        
        # copy data in merge_fields
        temp = member["merge_fields"].copy()
        data["First_Name"] = temp['FNAME']
        data["Last_Name"] = temp['LNAME']
        data["ASU_ID"] = temp['MMERGE3']      
        l[temp['MMERGE3']]  = data
    return l

class ChimpRequester(object):
    """ChimpRequester sends authenticated requests to mailchimp to do various
    operations
    """
    
    def __init__(self,**kwargs):
        self._dc = "us11"
        self._api_version = "3.0"
        self._base_url = 'https://{}.api.mailchimp.com/{}/'.format(self._dc,self._api_version) 
        self._user_name = os.environ['MAILCHIMP_USER']
        self._api_key = os.environ['MAILCHIMP_AUTH']
        self._session = self._get_session(self._user_name,self._api_key)
  
    def _get_session(self,user,apikey):
         """
         _get_session returns a session with basic auth for mailchimp
         """
         s = requests.Session()
         s.auth = (user,apikey)
         return s
    
    @handle_chimp_response    
    def _post_request(self,path,body=""):
        """
        Return request object from POST request
        """
        r = self._session.post(self._base_url+path,dumps(body))
        return r
    
    @handle_chimp_response   
    def _get_request(self,path):
        """
        Return request object from GET request
        """
        r = self._session.get(self._base_url+path)
        return r
    
    @handle_chimp_response   
    def _patch_request(self,path,body=""):
        """
        Return request object from PATCH request
        """
        r = self._session.patch(self._base_url+path,body=body)
        return r
    
    @handle_chimp_response   
    def _put_request(self,path,body=""):
        """
        Return request object from PUT request
        """
        r = self._session.put(self._base_url+path,body)
        return r
    
    @handle_chimp_response   
    def _delete_request(self,path):
        """
        Return request object from DELETE request
        """
        r = self._session.delete(self._base_url+path)
        return r
        
        
    def add_member(self,list_id,data={}):
        """
        add_member adds a new contact to a mailchimp list
        """
        path = "lists/{}/members/".format(list_id)
        json_respose = self._post_request(path,data)
        return json_respose

    def get_list(self,list_id):
        """
        get_list returns a list of people on a mail chimp list 
        """
        path = "lists/{}/members?count=1700".format(list_id)
        json_response = self._get_request(path)
        return json_response.json()

    def update_list(self, list_id, timestamp):
        path = "lists/{}/members?since_last_changed={}".format(list_id, timestamp)
        json_response = self._get_request(path)
        return json_response.json()