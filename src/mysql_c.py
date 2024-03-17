import pymysql

def check_valid(check):
    required_keys = ['display_name', 'service', 'host', 'username', 'password', 'statement']
    for key in required_keys:
        if key not in check:
            return False
        elif key == 'password':
            continue
        elif check[key] == '':
            return False
    return True

def mysql_check(check):
    if not check_valid(check):
        return 'check error'
    try:
        connection = pymysql.connect(
            host=check['host'],
            user=check['username'],
            password=check['password']
        )
        with connection.cursor() as cursor:
            cursor.execute(check['statement'])
            result = cursor.fetchall()
        connection.commit()
        return 0
    except Exception as e:
        return str(e)
    
if __name__ == '__main__':
    check = {
        "display_name": "mysql :0",
        "service": "mysql",
        "host": "192.168.151.98",
        "username": "root",
        "password": "root",
        "statement": "select user,host from mysql.user"
    }
    print(f'mysql: {mysql_check(check)}')