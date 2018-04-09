#!/usr/bin/env python
#*-*coding:utf-8

import subprocess, flask, time
from flask import Flask, request, make_response, redirect, url_for
import mimetypes, json, os
import zipfile, time
import optparse,logging
from utils import util_requests
import multiprocessing as mp

app = Flask(__name__)
global CUR_PATH
global DEFAULT_PATH

def commandline():
    parser = optparse.OptionParser()
    parser.add_option('-H', '--host', dest="hostname", default="127.0.0.1", help="host adress default is :17.0.0.1")
    parser.add_option('-P', '--port', dest="port", default=8000, help="port NO. default is 8000")

    parser.add_option('-m', '--master', dest="master", default='127.0.0.1', help="master ip")
    parser.add_option('-p', '--mport', dest="mport", default=8800, help="master regist port")
    parser.add_option('-t', '--interval', dest="interval", default=60, help="polling time interval")

    parser.add_option("-D", '--debug', action="store_true", dest="debug", help="run with debug mode")

    parser.add_option('-F', '--folder', dest="folder", default="/home", help="nls logs folder")

    parser.add_option('-l', '--log', dest='logpath', default='/tmp/nlslogmanager.log', help='the log path')
    return parser.parse_args()


#hostname = os.system("")
class FileManager():

    def isdir(self, path):
        isdir_cmd = "file -b %s|grep directory" % path
        p = subprocess.Popen(isdir_cmd, stdout=subprocess.PIPE, shell=True)
        app.logger.debug("+%s" % isdir_cmd)
        content = p.stdout.readlines()
        return content

    def list(self, path):
        if not self.isdir(path):
            pass
            #return redirect(url_for("download", filename=path))

        p = subprocess.Popen("ls -lh %s" % path, stdout=subprocess.PIPE, shell=True)
        files = []
        while True:
            l = p.stdout.readline()
            if not l:
                break
            l = l.strip()
            files.append(l)
            time.sleep(0.5)
        return files

def isdir(path):
    isdir_cmd = "file -b %s|grep directory" % path
    p = subprocess.Popen(isdir_cmd, stdout=subprocess.PIPE, shell=True)
    app.logger.debug("+%s" % isdir_cmd)
    content = p.stdout.readlines()
    return content

def exec_with_result(cmdline):
    """create new process to run the commandline
    and return the stdout data"""
    app.logger.debug(cmdline)
    p = subprocess.Popen(cmdline, stdout=subprocess.PIPE, shell=True)
    result = []
    while True:
        l = p.stdout.readline()
        if not l:
            break;
        result.append(l.strip())
    return result


@app.route("/")
@app.route('/list')
@app.route("/ls")
def list():
    # if LOGS:
    #     return json.dumps(LOGS)
    LOGS = {}
    path = CUR_PATH
    if not isdir(path):
        pass
    #return redirect(url_for("download", filename=path))
    p = subprocess.Popen("ls -lh %s" % path, stdout=subprocess.PIPE, shell=True)
    files = []
    istotal = True
    while True:
        l = p.stdout.readline()
        if not l:
            break
        if istotal:
            istotal = False
            continue

        l = l.strip()
        if path in LOGS.keys():
            LOGS[path][l.split(" ")[-1]] = l
        else:
            LOGS[path] = {l.split(" ")[-1]:l}

    return json.dumps(LOGS)

@app.route("/file", methods=["GET","POST"])
def showfile():
    path = request.args.get('path')
    act = request.args.get('act')

def exec_for_log(cmd):
    app.logger.debug(cmd)
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
    path = CUR_PATH
    LOGS = {}
    while True:
        l = p.stdout.readline()
        if not l:
            break
        l = l.strip()
        if path in LOGS.keys():
            LOGS[path][l.split("/")[-1]] = l
        else:
            LOGS[path] = {l.split("/")[-1]:l}
    return json.dumps(LOGS)

def exec_with_status(cmd):
    app.logger.debug(cmd)
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
    error = p.stderr.read()
    if error.strip():
        raise Exception(error)

@app.route("/show",methods=["GET", "POST", "OPTIONS"])
def show():
    path = request.args.get('path')
    if not isdir(path):
        pass
        #return redirect(url_for("download", path=path))
    app.logger.debug("ls -lh %s" % path)
    p = subprocess.Popen("ls -lh %s" % path, stdout=subprocess.PIPE, shell=True)
    LOGS = {}
    i = 0
    while True:
        l = p.stdout.readline()
        if not l:
            break
        if i == 0:
            i = 1
            app.logger.debug(l)
            continue

        l = l.strip()

        if path in LOGS.keys():
            LOGS[path][l.split(" ")[-1]] = l
        else:
            LOGS[path] = {}
        time.sleep(0.5)
    return json.dumps(LOGS)

@app.route("/pwd", methods=["GET"])
def pwd():
    app.logger.debug("CUR_PATH %s" % CUR_PATH)
    return CUR_PATH

@app.route("/exe", methods=["GET"])
def exe():
    cmdline = request.args.get('cmdline')
    output = exec_with_result('cd %s && %s'%(CUR_PATH, cmdline))
    return json.dumps(output)

@app.route("/cd", methods=["GET"])
def cd():
    global CUR_PATH
    global DEFAULT_PATH
    tmppath = CUR_PATH
    path = request.args.get('path')
    if "~" in path:
        CUR_PATH = DEFAULT_PATH
    elif ".." in path:
        CUR_PATH =  CUR_PATH[0:-1] if CUR_PATH[-1] == '/' else CUR_PATH
        CUR_PATH = "/".join(CUR_PATH.split('/')[0:-1])
    else:
        CUR_PATH = os.path.join(CUR_PATH, path)

    if not (os.path.isdir(CUR_PATH)) or (not os.path.exists(CUR_PATH)):
        app.logger.warning('Path %s is not a directory or not exists', CUR_PATH)
        CUR_PATH = tmppath

    app.logger.debug('Current Path %s', CUR_PATH)
    return CUR_PATH

@app.route("/download", methods=["GET", "POST"])
@app.route("/cp", methods=["GET", "POST"])
def download():
    if request.method == "POST":
        data = request.get_data()
        jdata = json.loads(data)
        filepath = '/tmp/nls_logs_%s.zip' % time.time()
        zipf = zipfile.ZipFile(filepath, 'w', zipfile.ZIP_DEFLATED)
        app.logger.debug("zip file %s" % filepath)
        for f in jdata:
            app.logger.debug("Zip file %s" % f)
            zipf.write(f)
        zipf.close()
        return json.dumps({'file': filepath})
    else:
        filepath = request.args.get("path")
        if not filepath:
            filepath = os.path.join(CUR_PATH, request.args.get("file"))

        app.logger.debug("Download file %s" % filepath)
        with open(filepath.encode('utf-8'), 'r') as f:
            response = make_response(f.read())
            mime_type = mimetypes.guess_type(filepath)[0]
            response.headers["Content-Type"] = mime_type
            response.headers["Content-Disposition"] = \
                                "attachment;filename=%s" % filepath.split("/")[-1]
            return response


@app.route('/search', methods=['GET'])
def search():
    searchkey = request.args.get('key')
    search_cmd = "find {0} -name \"{1}\" |xargs ls -lh".format(CUR_PATH,searchkey)
    return exec_for_log(search_cmd)

@app.route("/rm", methods=["POST"])
def rm():
    data = request.get_data()
    files = json.loads(data)
    files = [os.path.join(CUR_PATH, f) for f in files]
    delete_cmd = "rm -rf %s" % " ".join(files)
    app.logger.debug(files)
    try:
        exec_with_status(delete_cmd)
    except Exception as e:
        pass
    return list()


@app.route("/delete", methods=["POST"])
def delete():
    data = request.get_data()
    files = json.loads(data)
    app.logger.debug(files)
    delete_cmd = "rm -rf %s" % " ".join(files)
    app.logger.warning(delete_cmd)
    try:
        pass
        #exec_with_status(delete_cmd)
    except Exception as e:
        pass
    return list()

def register_polling(master_addr, master_port, port, interval):
    request = util_requests.UtilityRequests()
    url = 'http://{0}:{1}/register?port={2}'.format(master_addr, master_port, port)
    while True:
        try:
            resp_content = request.getContent(url)
        except Exception as e:
            app.logger.error(str(e))
        finally:
            time.sleep(interval)

if __name__ == "__main__":
    global CUR_PATH
    global DEFAULT_PATH

    DEFAULT_PATH = os.environ['HOME']
    CUR_PATH = DEFAULT_PATH

    opt, args = commandline()

    loghandler = logging.FileHandler(opt.logpath)
    if opt.debug:
        loghandler.setLevel(logging.DEBUG)
    else:
        loghandler.setLevel(logging.WARNING)
    app.logger.addHandler(loghandler)
    util_requests.logger = app.logger

    CUR_PATH = opt.folder
    DEFAULT_PATH = opt.folder
    p = mp.Process(target=register_polling, args=(opt.master, opt.mport, opt.port, int(opt.interval)))
    p.start()
    app.run(host=opt.hostname, port=int(opt.port), debug=opt.debug)

