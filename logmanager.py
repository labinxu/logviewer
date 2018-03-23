#!/usr/bin/env python
#*-*coding:utf-8

import subprocess, flask, time
from flask import Flask, request, make_response
import mimetypes, json


app = Flask(__name__)


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

LOGS = {}
LOG_DIR =  "/home/laxxu/testforflask"
@app.route("/")
@app.route('/list')
def list():
    if LOGS:
        return json.dumps(LOGS)

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


@app.route("/show",methods=["GET", "POST"])
def show():
    path = request.args.get('path')
    if not isdir(path):
        pass
    #return redirect(url_for("download", filename=path))
    app.logger.debug("ls -lh %s" % path)
    p = subprocess.Popen("ls -lh %s" % path, stdout=subprocess.PIPE, shell=True)
    LOGS = {}
    i = 0
    while True:
        l = p.stdout.readline()
        if not l:
            break
        import pdb
        pdb.set_trace()
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
    filepath = request.args.get("path")
    app.logger.debug("Download file %s" % filepath)
    with open(filepath, 'r') as f:
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


@app.route("/delete", methods=["GET"])
def delete():
    return "delete"


if __name__ == "__main__":
    app.debug = True
    app.run(port=8000)

