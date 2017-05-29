import argparse
import getpass
import json
import datetime
import chimp
import time
import logging
import os
import threading
import sys

try:
    LIST_ID = os.environ['MAILCHIMP_LIST_ID']
except:
    logging.fatal('Error please give a list')

def load_mailchimp():
    if os.path.isfile('members.json'):
        with open('members.json') as f:
            l = json.load(f)
            return l
    logging.fatal('Failure to open members.json')

def update_members():
    chimp.ChimpRequester().raw_update(LIST_ID)


def update_list(l, go=True):
    c = chimp.ChimpRequester()
    while go:
        t = str(datetime.datetime.utcnow())
        time.sleep(10)
        logging.debug('Updating list')
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
    if input[:7] == ';601744' and len(input) > 16:
        return input[7:17]
    elif input[:10] == '%E?;601744' and len(input) > 19:
        return input[10:20]
    else:
        return input


def run_swiper():
    mailchimp_data = load_mailchimp()
    go = True 
    d = threading.Thread(name='update', target=update_list, kwargs={'l':id,'go':go})
    d.daemon = True
    d.start()
    checkin = []
    print(chr(27) + "[2J")
    soda = get_acsii('soda.txt', 'Welcome to SoDA!')
    print('\n\n\n\n\n')
    enter_id_text = get_acsii('enter_id.txt', 'Enter your student ID: ')
    success_id_text = get_acsii('success_id.txt', 'Success, you are checked in!')
    mailchimp_text = get_acsii('mailchimp_text.txt','Please enter your information into Mailchimp')
    invalid_text = get_acsii('invalid.txt', 'Invalid card swipe: Please try again!:)')
    while True:
        try:
            print(soda)
            print('\n\n\n\n\n')
            i = getpass.getpass(enter_id_text)
            parsed_input = parse_input(i, invalid_text)
            if parsed_input is None:
                continue
            if parsed_input in mailchimp_data:
                print(chr(27) + "[2J")
                print(success_id_text)
                print('\n\n')
                checkin.append(mailchimp_data[parsed_input])
                time.sleep(2)
                print(chr(27) + "[2J")
                
            else:
                print(chr(27) + "[2J")
                checkin.append({
                    parsed_input: {
                    }
                })
                print(mailchimp_text)
                time.sleep(2)
                print(chr(27) + "[2J")

        except KeyboardInterrupt:
            logging.debug('Writing information to file')
            if not os.path.isdir('./sign-ins'):
                os.mkdir('./sign-ins')
            file_name = './sign-ins/check_in_{}.json'.format(str(datetime.datetime.utcnow()))

            with open(file_name, 'w+') as f:
                members = {}
                members['members'] = checkin
                json.dump(members, f)
            logging.debug('Updating Members.json')
            with open('members.json', 'w') as f:
                json.dump(mailchimp_data, f)
            go = False
            sys.exit()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-u','--update', help='Raw update members.json', action='store_true',
                        default=False, dest='update')
    parser.add_argument('-d', '--debug', help='Set logging level to debug', action='store_true',
                        default=False, dest='debug')

    args = parser.parse_args()

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    if args.update:
        update_members()
    run_swiper()


