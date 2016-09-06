from requests.auth import HTTPBasicAuth

import requests
import os
import re
import logging
import datetime
import json
import StringIO
import time 
import tarfile
import sys
import shutil

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
        r = self._session.post(self._base_url+path, json.dumps(body))
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
        path = "lists/{}/members?count=1600".format(list_id)
        json_response = self._get_request(path)
        return json_response.json()

    def update_list(self, list_id, timestamp):
        path = "lists/{}/members?since_last_changed={}".format(list_id, timestamp)
        resp = self._get_request(path)
        return resp.json()
    
    def pull_num_list(self, list_id, num):
        path = "lists/{}/members?count={}".format(list_id, num)
        resp = self._get_request(path)
        return resp.json()

    def get_list_count(self, list_id):
        path = "lists/{}".format(list_id)
        resp = self._get_request(path)
        
        resp_json = resp.json()
        if 'stats' in resp_json and 'member_count' in resp_json['stats']:
            return resp_json['stats']['member_count']
        logging.fatal('Failure to get list count')

    def raw_update(self, list_id):
        list_count = self.get_list_count(list_id)

        if not list_count:
            return None 

        op_post = {
            'operations': []
        }

        # generate operations 
        off_set = 0
        list_left = list_count
        print (list_count)
        while list_left > 0:
            batch = {
                'method': 'GET',
                'path': '/lists/{}/members'.format(list_id),
                'operation_id': '{}/{}'.format(off_set, list_count),
                'params': {'count':500, 'offset':off_set}
            }
            logging.debug("off_set{} count{}".format(off_set, 500))
            op_post['operations'].append(batch)
            list_left -= 500
            off_set += 500
        resp = self._post_request('/batches', op_post)

        if resp.status_code != 200:
            logging.fatal('Failure to start batch operations status code {}'.format(resp.status_code)) 
        
        resp_json = resp.json()

        for link in resp_json['_links']:
            if link['rel'] == 'self':
                batch_url = link['href']

        batch_uri = None
        tries = 300
        logging.debug(batch_url)
        logging.debug("Waiting for batch operation to finish")
        while tries > 0:
            time.sleep(3)
            batch_resp = self._session.get(batch_url)
            batch_resp_json = batch_resp.json()

            if batch_resp_json['status'] == 'finished':
                batch_uri = batch_resp_json['response_body_url']
                logging.debug('Finished batch operations')
                break
            logging.debug("Operations Finished: {}".format(batch_resp_json['finished_operations']))
            logging.debug("Operations Total: {}".format(batch_resp_json['total_operations']))
            tries -= 1

        if not batch_uri:
            logging.fatal('Not batch uri found')
        self._write_tarfile(batch_uri)
        self._extract_tarfile()

    def _write_tarfile(self, batch_uri):
        logging.debug("Writing to tar.gz file")
        if os.path.isdir('./raw_json_members'):
            logging.debug('Removing old json files')
            shutil.rmtree('./raw_json_members')

        with open('raw_members.tar.gz', 'w') as f:
            r = requests.get(batch_uri)
            f.write(r.content)
    
    def _extract_tarfile(self):
        big_member_dict = {}
        logging.debug("Processing raw_members")
        with tarfile.open('raw_members.tar.gz') as t:
            t.extractall('./raw_json_members')
        json_files = glob.glob('./raw_json_members/*.json')
        big_member_dict = {}
        for j_f in json_files:
            with open(j_f, 'r') as f:
                raw_dict = json.loads(json.load(f)[0]['response'])
                transformed_dict = transform_mailchimp_response(raw_dict)
                big_member_dict.update(transformed_dict)
        logging.debug("Writing to members.json")
        with open('members.json', 'w') as f:
            json.dump(big_member_dict, f)
