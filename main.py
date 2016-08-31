import argparse
import getpass
import json
import datetime
import chimp
import time
import datetime
import os
import threading
import sys
import csv

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

def update_members():
    chimp_requester = chimp.ChimpRequester()

    raw_json = chimp_requester.get_list(LIST_ID)

    parsed_json = chimp.transform_mailchimp_response(raw_json)

    with open('members.json', 'w') as f:
        json.dump(parsed_json, f)


def update_list(l=None, go=True):
    c = chimp.ChimpRequester()
    while go:
        t = str(datetime.datetime.utcnow())
        time.sleep(10)
        updated = c.update_list(LIST_ID, t)

        transform = chimp.transform_mailchimp_response(updated)
        if transform:
            l.update(transform)

def get_acsii(filename, default_text):
    if os.path.isfile(filename):
        with open(filename) as f:
            ascii_art = f.read()
        return ascii_art
    return default_text

def parse_input(input, invalid_text):
    # print input[:11]
    # if len(input) > 1 and input[0] != ';':
    #     return input
    if input[:7] == ';601744' and len(input) > 16:
        return input[7:17]
    elif input[:10] == '%E?;601744' and len(input) > 19:
        print input[:11]
        return input[10:20]


def main():
    id = load_mailchimp()
    # bad dawg
    go = True 
    d = threading.Thread(name='update', target=update_list, kwargs={'l':id,'go':go})
    d.daemon = True
    d.start()
    checkin = []
    print(chr(27) + "[2J")
    soda = get_acsii('soda.txt', 'Welcome to SoDA!')
    print '\n\n\n\n\n'
    enter_id_text = get_acsii('enter_id.txt', 'Enter your student ID: ')
    success_id_text = get_acsii('success_id.txt', 'Success, you are checked in!')
    mailchimp_text = get_acsii('mailchimp_text.txt','Please enter your information into Mailchimp')
    invalid_text = get_acsii('invalid.txt', 'Invalid card swipe: Please try again!:)')
    while True:
        try:
            print soda
            print '\n\n\n\n\n'
            input = getpass.getpass(enter_id_text)
            parsed_input = unicode(parse_input(input, invalid_text))
            if parsed_input is None:
                continue
            if parsed_input in id:
                print(chr(27) + "[2J")
                print success_id_text
                print '\n\n'
                checkin.append(id[parsed_input])
                time.sleep(2)
                print(chr(27) + "[2J")
                
            else:
                print(chr(27) + "[2J")
                print mailchimp_text
                time.sleep(2)
                print(chr(27) + "[2J")

        except KeyboardInterrupt:
            print 'Writing information to file'
            if not os.path.isdir('./sign-ins'):
                os.mkdir('./sign-ins')
            file_name = './sign-ins/check_in_{}.json'.format(str(datetime.datetime.utcnow()))

            with open(file_name, 'w+') as f:
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


