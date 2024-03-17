import winrm, random

def check_valid(check):
    required_keys = ['display_name', 'service', 'host', 'creds', 'command']
    for key in required_keys:
        if key not in check or check[key] == '':
            return False
    return True

def winrm_check(check):
    if not check_valid(check):
        return 'check error'
    try:
        username, password = random.choice(list(check['creds'].items()))
        session = winrm.Session(check['host'], auth=(username, password))
        result = session.run_cmd(check['command'])
        return 0
    except Exception as e:
        return str(e)