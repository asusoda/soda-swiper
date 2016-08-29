import argparse
import json
import datetime
import chimp
import time
import os
import threading
import sys

try:
    LIST_ID = os.environ['MAILCHIMP_LIST_ID']
except:
    print 'Error please give a list'
    sys.exit()

def load_mailchimp():
    if os.path.isfile('members.json'):
        with open('members.json') as f:
            l = json.load(f)
            return l
    chimp_requester = chimp.ChimpRequester()

    raw_json = chimp_requester.get_list(LIST_ID)

    parsed_json = chimp.transform_mailchimp_response(raw_json)
    
    members = {'members': parsed_json}
    with open('members.json', 'w') as f:
        json.dump(members, f)
    return members

def update_members():
    chimp_requester = chimp.ChimpRequester()

    raw_json = chimp_requester.get_list(LIST_ID)

    parsed_json = chimp.transform_mailchimp_response(raw_json)
    
    members = {'members': parsed_json}
    with open('members.json', 'w') as f:
        json.dump(members, f)


def update_list(l=None, go=True):
    c = chimp.ChimpRequester()
    while go:
        t = str(datetime.datetime.utcnow())
        time.sleep(10)
        updated = c.update_list(LIST_ID, t)

        transform = chimp.transform_mailchimp_response(updated)
        if transform:
            l.update(transform)
def parse_input(input):
    if input[:7] == ';601744' and len(input) > 17:
        return input[7:17]
    else:
        print 'Invalid card swipe: Please swip again!:)'
    return input
def main():
    id = load_mailchimp()
    # bad dawg
    go = True 
    d = threading.Thread(name='update', target=update_list, kwargs={'l':id,'go':go})
    d.daemon = True
    d.start()
    checkin = []
    while True:
        try:
            input = raw_input('Enter your student ID: \n')
            parsed_input = parse_input(input)
            if parsed_input in id:
                print 'Success you are checked in!\n'
                checkin.append(id[parsed_input])
            else:
                print 'Please enter your information into Mailchimp\n'
        except KeyboardInterrupt:
            print 'Writing information to file'
            file_name = 'check_in_{}.json'.format(time.time())
            with open(file_name, 'w') as f:
                members = {}
                members['members'] = checkin
                json.dump(members, f)
            print 'Updating Members.json'
            with open('members.json', 'w') as f:
                json.dump(id, f)
            go = False
            sys.exit()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-u','--update', help='Manually update members.json', action='store_true',
                        default=False, dest='update')

    args = parser.parse_args()
    if args.update:
        update_members()
    main()


