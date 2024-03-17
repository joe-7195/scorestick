from ftplib import FTP
import hashlib
import random

def check_valid(check):
    required_keys = ['display_name', 'service', 'host', 'creds', 'content']
    for key in required_keys:
        if key not in check or check[key] == '':
            return False
    return True

def ftp_check(check):
    if not check_valid(check):
        return 'check error'
    try:
        username, password = random.choice(list(check['creds'].items()))
        file, correct_hash = random.choice(list(check['content'].items()))
        ftp = FTP()
        # ftp.debugging = 2
        ftp.connect(check['host'], 21)
        ftp.login(username, password)
        md5 = hashlib.md5()
        ftp.retrbinary('RETR ' + file, md5.update)
        md5 = md5.hexdigest()
        if md5.upper() == correct_hash.upper():
            return 0
        else:
            return 'failed content check'
    except Exception as e:
        return str(e)

if __name__ == '__main__':
    check = {
        "display_name": "ftp",
        "service": "ftp",
        "host": "198.18.0.188",
        "creds": {
            "anonymous": "",
            "jack.rover": "Password123!@#",
            "harry.potter": "Password123!@#"
        },
        "content": {
            "catboy.png": "66C2DCA3C6EE7760DCB98A3F31259D22"
        }
    }
    print(f'ftp: {ftp_check(check)}')