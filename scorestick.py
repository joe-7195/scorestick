import os
import json
import datetime

from time import sleep
from redis import Redis
from threading import Thread
from flask import Flask, render_template, request, redirect, url_for, flash
from multiprocessing import Process
from subprocess import Popen

from src.rdp_c import rdp_check
from src.ssh_c import ssh_check
from src.winrm_c import winrm_check
from src.mysql_c import mysql_check
from src.http_c import http_check
from src.dns_c import dns_check
from src.ftp_c import ftp_check
from src.smb_c import smb_check

############################################################## redis

def redis_server(port):
    command = ['redis-server', '--port', str(port)]
    Popen(command)

def redis_init(port=16379):
    global r
    Popen('pkill -9 redis-server; pkill -9 scorestick.py', shell=True)
    redis_process = Process(target=redis_server, args=(port,))
    redis_process.start()
    sleep(1)
    r = Redis(host='localhost', port=port)
    for key in r.keys():
        r.delete(key)
    return redis_process

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
    for i in range(len(checks)):
        threads[i] = Thread(target=process_check_wrapper, args=(checks[i], i, results))
        threads[i].start()
    for i in range(len(checks)):
        threads[i].join()
    return checks, results

def main_loop(round_time=5, history=20, check_dir='checks/'):
    r.set('round_history', history)
    r.set('round_time', 5)
    r.set('check_dir', check_dir)
    while (True):
        history = int(r.get('round_history'))
        check_dir = str(r.get('check_dir').decode('utf-8'))
        checks, results = run_checks(check_dir)
        r.set('checks', json.dumps(checks))
        all_results = []
        all_results.append(results)
        for i in range(history):
            try:
                all_results.append(json.loads(r.get('results' + str(i))))
            except TypeError:
                break
        for i in range(history):
            try:
                r.set('results' + str(i), json.dumps(all_results[i]))
            except IndexError:
                break
        sleep(round_time)

############################################################## flask

app = Flask(__name__, static_url_path='/static')
app.debug = True
app.secret_key = 'https://www.ietf.org/rfc/rfc1035.txt'

@app.route('/')
def index():
    all_results = []
    round_history = int(r.get('round_history'))
    round_time = int(r.get('round_time'))
    for i in range(round_history):
        try:
            all_results.append(json.loads(r.get('results' + str(i))))
        except TypeError:
            break
    try:
        checks = json.loads(r.get('checks'))
    except TypeError:
        checks = [{'display_name' : 'loading...'}]
    return render_template('index.html', all_results=all_results, checks=checks, round_time=round_time)

@app.route('/results/')
def results():
    try:
        results = json.loads(r.get('results0'))
    except:
        return redirect(url_for('index'))
    try:
        checks = json.loads(r.get('checks'))
    except TypeError:
        checks = [{'display_name' : 'waiting for first check...'}]
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
    try:
        input = json.loads(request.form['text'])
        check_index = int(request.form['check_index'])
        check_dir = str(r.get('check_dir').decode('utf-8'))
        check_paths = get_check_filepaths(check_dir)

        if not is_valid_check(input):
            raise Exception

        with open(check_paths[check_index], 'w') as f:
            json.dump(input, f)
            f.close()

        checks = get_checks(check_dir)
        r.set('checks', json.dumps(checks))
        return redirect(url_for('checks'))
    
    except:
        flash('some kinda error idk')
        return redirect(url_for('checks'))

##############################################################

if __name__ == '__main__':
    redis_process = redis_init()
    p = Process(target=main_loop)

    p.start()
    app.run(host='0.0.0.0', port=1337)

    p.terminate()
    redis_process.terminate()
