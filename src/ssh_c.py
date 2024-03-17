import paramiko, random

def check_valid(check):
    required_keys = ['display_name', 'service', 'host', 'creds', 'command']
    for key in required_keys:
        if key not in check or check[key] == '':
            return False
    return True

def ssh_check(check):
    if not check_valid(check):
        return 'check error'
    try:
        username, password = random.choice(list(check['creds'].items()))
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(check['host'], username=username, password=password, look_for_keys=False, banner_timeout=30)
        stdin, stdout, stderr = ssh.exec_command(check['command'])
        return 0
    except Exception as e:
        return str(e)

if __name__ == '__main__':
    creds = {
        "jack.rover": "Password123!@#",
        "kate.bush": "Password123!@#",
        "harry.potter": "Password123!@#"
    }
    check = {
        "display_name": "ssh",
        "service": "ssh",
        "host": "198.18.0.188",
        "creds": creds,
        "command": "whoami"
    }
    print(f'ssh: {ssh_check(check)}')
    import json
    with open('temp.json', 'w') as f:
        f.write(json.dumps(check, indent=2))