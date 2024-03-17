import subprocess
import random

def check_valid(check):
    required_keys = ['display_name', 'service', 'host', 'creds']
    for key in required_keys:
        if key not in check or check[key] == '':
            return False
    return True

def rdp_check(check):
    if not check_valid(check):
        return 'check error'
    try:
        username, password = random.choice(list(check['creds'].items()))
        command = "export DISPLAY=:69; xfreerdp +auth-only /cert:ignore /v:'"+check['host']+"' /u:'"+username+"' /p:'"+password+"'"
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        err = process.stderr.readlines()
        out = process.stdout.readlines()
        for line in err:
            if 'status 0' in str(err):
                return 0
        return str(err) + '\n' + str(out)
    except Exception as e:
        return str(e)