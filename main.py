import json
import chimp
import time
import os


def load_mailchimp():
    if os.path.isfile('members.json'):
        with open('members.json') as f:
            l = json.load(f)
            return l['members']
    chimp_requester = chimp.ChimpRequester()

    raw_json = chimp_requester.get_list('b4ab6913d5')

    parsed_json = chimp.transform_mailchimp_response(raw_json)
    
    members = {'members': parsed_json}
    with open('members.json', 'w') as f:
        json.dump(members, f)
    return members['members']



def main():
    id = load_mailchimp()
    checkin = []
    input = raw_input('Enter your student ID: \n')
    while True:
        try:
            if input in id:
                print 'Success you are checked in!\n'
                checkin.append(id[input])
            else:
                print 'Please enter your information into Mailchimp\n'
            input = raw_input('Enter your student ID: \n')
        except KeyboardInterrupt:
            print 'Writing information to file'
            file_name = 'check_in_{}.json'.format(time.time())
            with open(file_name, 'w') as f:
                members = {}
                members['members'] = checkin
                json.dump(members, f)
            break

if __name__ == '__main__':
    main()


