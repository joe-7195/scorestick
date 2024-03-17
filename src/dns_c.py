import dns.resolver, random

def check_valid(check):
    required_keys = ['display_name', 'service', 'host', 'content']
    for key in required_keys:
        if key not in check or check[key] == '':
            return False
    return True

def dns_check(check):
    if not check_valid(check):
        return 'check error'
    try:
        name, ip = random.choice(list(check['content'].items()))
        r = dns.resolver.Resolver(configure=False)
        r.nameservers = [check['host']]
        result = r.resolve(name, 'A')
        for result_ip in result:
            if ip in result_ip.to_text():
                return 0
            else:
                return 'wrong ip: ' + result_ip.to_text()
    except Exception as e:
        return str(e)

if __name__ == '__main__':
    check = {
        "display_name": "dns :]",
        "service": "dns",
        "host": "198.18.0.188",
        "content": {
            "db01.galacticspace.local":"192.168.151.1",
            "dc01.galacticspace.local":"198.18.0.188"
        }
    }
    print(f'dns: {dns_check(check)}')