import hashlib
import smbclient
import random

def check_valid(check):
    required_keys = ['display_name', 'service', 'host', 'creds', 'content']
    for key in required_keys:
        if key not in check or check[key] == '':
            return False
    return True

def smb_check(check):
    if not check_valid(check):
        return 'check error'
    try:
        username, password = random.choice(list(check['creds'].items()))
        file, correct_hash = random.choice(list(check['content'].items()))
        url = '\\\\' + check['host'] + '\\' + file
        smbclient.register_session(check['host'], username=username, password=password)
        with smbclient.open_file(url, mode='rb') as f:
            md5 = hashlib.md5(f.read()).hexdigest()
            if md5.upper() == correct_hash.upper():
                return 0
            else:
                return 'failed content check'
    except Exception as e:
        return str(e)