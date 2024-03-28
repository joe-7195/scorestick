import os
import json
import datetime
import sqlite3

from time import sleep
from threading import Thread
from flask import Flask, render_template, request, redirect, url_for, g
from multiprocessing import Process
from subprocess import Popen

# there should totally be a better way to do this
from src.rdp_c import rdp_check
from src.ssh_c import ssh_check
from src.winrm_c import winrm_check
from src.mysql_c import mysql_check
from src.http_c import http_check
from src.dns_c import dns_check
from src.ftp_c import ftp_check
from src.smb_c import smb_check

############################################################## sqlite

DB_NAME = 'scorestick.db'

def clear_all(db):
    query = """
        SELECT name FROM sqlite_master 
        WHERE type='table';
    """
    tables = db.execute(query).fetchall()
    for table in tables:
        db.execute(f'drop table ?;', table[0])

def get_table_names(db):
    tables = []
    query = """
        SELECT name FROM sqlite_master 
        WHERE type='table';
    """
    for table in db.execute(query).fetchall():
        tables.append(table[0])
    return tables

def get_num_entries(db, table):
    query = """
        SELECT COUNT(*) FROM ?;
    """
    return db.execute(query, (table)).fetchall()[0][0]

def push_checks(db, checks):
    db.execute('DROP TABLE checks;')
    query = """
        CREATE TABLE IF NOT EXISTS checks
        (index INT, check_json TEXT);
    """
    db.execute(query)
    for i in range(len(checks)):
        query = """ 
            INSERT INTO TABLE checks (index, check_json)
            VALUES (?, ?);
        """
        db.execute(query, (i, json.dumps(checks[i])))

def create_check_table(db, name):
    query = """
        CREATE TABLE IF NOT EXISTS ?
        (id INT, result TEXT, time TEXT);
    """
    db.execute(query, (name))

############################################################## scorestick
    
def is_valid_check(check):
    if ('display_name' in check) and ('service' in check) and ('host' in check):
        return True
    return False

def get_check_filepaths(check_dir):
    check_filepaths = []
    for filename in os.listdir(check_dir):
        if '.json' in filename:
            filepath = check_dir + filename
            with open(filepath ,'r') as f:
                try:
                    check = json.load(f)
                except:
                    continue
                if is_valid_check(check):
                    check_filepaths.append(filepath)
                f.close()
    return check_filepaths

def get_checks(check_dir):
    checks = []
    for filepath in get_check_filepaths(check_dir):
        with open(filepath, 'r') as f:
            checks.append(json.load(f))
    return checks

def process_check(check):
    check_type = check['service']
    if check_type == 'rdp':
        return rdp_check(check) 
    elif check_type == 'ssh':
        return ssh_check(check)
    elif check_type == 'winrm':
        return winrm_check(check)
    elif check_type == 'mysql':
        return  mysql_check(check)
    elif check_type == 'dns':
        return dns_check(check)
    elif check_type == 'http':
        return http_check(check)
    elif check_type == 'ftp':
        return ftp_check(check)
    elif check_type == 'smb':
        return smb_check(check)
    else:
        return 'check error'

def process_check_wrapper(check, i, results):
    results[i] = process_check(check)

def run_checks(check_dir):
    checks = get_checks(check_dir)
    threads = [None] * len(checks)
    results = [None] * len(checks)
    timestamps = [datetime.datetime.now().strftime('%I:%M')] * len(checks)
    for i in range(len(checks)):
        threads[i] = Thread(target=process_check_wrapper, args=(checks[i], i, results))
        threads[i].start()
    for i in range(len(checks)):
        threads[i].join()
    return checks, results, timestamps

def main_loop(round_time=5, history=20, check_dir='checks/'):
    while (True):
        db = sqlite3.connect(DB_NAME)
        checks, results, timestamps = run_checks(check_dir)
        push_checks(db, checks)
        time = time.time()
        for i in range(len(checks)):
            name = checks[i]['display_name'] + '_c'
            create_check_table(db, name)
            query = """
                INSERT INTO ? VALUES (id, result, time)
                (?, ?, ?);
            """
            db.execute(query, (time, name, results[i], timestamps[i]))
        sleep(round_time)

############################################################## flask

app = Flask(__name__, static_url_path='/static')
app.debug = True
app.secret_key = 'https://www.ietf.org/rfc/rfc1035.txt'

def get_db():
    db = getattr(g, '_database', None)
    if db == None:
        db = g.__database = sqlite3.connect(DB_NAME)
    return db

@app.route('/')
def index():
    db = get_db()
    data = {}

    for table_name in get_table_names(db):
        if '_c' in table_name:
            query = """
                SELECT * from ?;
            """
            data[table_name] = db.execute(query, (table_name))

    data2 = {}
    
    # key is name of check table
    # value is a list of tuples containing id, results, time
    for k, v in data.values():



    return render_template(
        'index.html', 
        all_results=, 
        checks=,
        round_time=, 
        timestamps=
    )

@app.route('/results/')
def results():
    return render_template('results.html', results=results, checks=checks)

@app.route('/checks/', methods=['GET'])
def checks():
    try:
        checks = json.loads(r.get('checks'))
    except TypeError:
        return redirect(url_for('index'))
    return render_template('checks.html', checks=checks)

@app.route('/checks/', methods=['POST'])
def check_change():
    return redirect(url_for('checks'))

@app.teardown_appcontext
def close_db(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

##############################################################

if __name__ == '__main__':
    p = Process(target=main_loop)

    p.start()
    app.run(host='0.0.0.0', port=1337)

    p.terminate()