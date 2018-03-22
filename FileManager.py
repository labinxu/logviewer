#!/usr/bin/env python
#*-*coding:utf-8
"""
#list the logs 
curl http://localhost:8000/logs

"""
import subprocess, flask, time
from flask import Flask, request
from flask_restful import Resource , Api, reqparse
import mimetypes, json
parser = reqparse.RequestParser()
parser.add_argument('rate', type=int, help='Rate to charge for this resource')
app = Flask(__name__)
api = Api(app)

LOGS = {

}

class LogManager(Resource):

    def isdir(self, path):
        isdir_cmd = "file -b %s|grep directory" % path
        p = subprocess.Popen(isdir_cmd, stdout=subprocess.PIPE, shell=True)
        app.logger.debug("+%s" % isdir_cmd)
        content = p.stdout.readlines()
        return content

    def list(self, path=''):
        if not path:
            path = "~"

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
            app.logger.debug(l)
            if path in LOGS.keys():
                LOGS[path][l.split(" ")[-1]] = l
            else:
                LOGS[path] = {}
            time.sleep(0.5)

        print(LOGS)
        return LOGS

    def get(self):
        # if path in LOGS.keys():
        #     app.logger.warning("Use the cache!")
        #     return LOGS[path]
        # else:
        return self.list("~/testforflask")

    def post(self):
        return ["post log manager"]

    def put(self, path):
        return ["hello%s"%path]

class Logs(Resource):
    def get(self, path=None):
        return ["file1", "file2", path, request.get_data()]

    def delete(self):
        return ["delete %s" % path]

    def post(self, path):
        return ["post", path, request.get_data()]


    def search(self, path):
        return ["search %s " % path]

    def put(self, path):
        return ["file3", "file4"]

api.add_resource(LogManager, "/list")
api.add_resource(Logs, "/logs","/logs/<path>")

if __name__ == "__main__":
    app.debug = True
    app.run(port=8000)

