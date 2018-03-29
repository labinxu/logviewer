#!/usr/bin/env python
#*-*coding:utf-8

import subprocess, flask, time
from flask import Flask, request, make_response, redirect, url_for
import mimetypes, json, os
import zipfile, time
import optparse


app = Flask(__name__)


def commandline():
    parser = optparse.OptionParser()
    parser.add_option('-H', '--host', dest="hostname", default="127.0.0.1", help="host adress default is :17.0.0.1")
    parser.add_option('-P', '--port', dest="port", default=8000, help="port NO. default is 8000")
    parser.add_option("-D", '--debug', action="store_true", dest="debug", help="run with debug mode")
    parser.add_option('-F', '--folder', dest="folder", default="/home/laxxu/testforflask", help="nls logs folder")
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

LOG_DIR =  "~"

@app.route("/")
@app.route('/list')
def list():
    # if LOGS:
    #     return json.dumps(LOGS)
    LOGS = {}
    path = LOG_DIR
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
    path = LOG_DIR
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

@app.route("/download", methods=["GET", "POST"])
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
    search_cmd = "find {0} -name \"{1}\" |xargs ls -lh".format(LOG_DIR,searchkey)
    return exec_for_log(search_cmd)

@app.route("/delete", methods=["POST"])
def delete():
    data = request.get_data()
    files = json.loads(data)
    app.logger.debug(files)
    delete_cmd = "rm -rf %s" % " ".join(files)
    app.logger.warning(delete_cmd)
    try:
        pass
    except Exception as e:
        pass

    return json.dumps({'status':'ok'})


if __name__ == "__main__":
    opt, args = commandline()
    app.logger.debug(opt)
    LOG_DIR = opt.folder
    app.run(host=opt.hostname, port=int(opt.port), debug=opt.debug)

