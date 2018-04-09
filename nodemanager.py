import subprocess, flask, time
from flask import Flask, request, make_response, redirect, url_for
import mimetypes, json, os
import zipfile, time
import optparse,logging


global master_pipe
#os.open( write_path, os.O_SYNC | os.O_CREAT | os.O_RDWR )  
app = Flask(__name__)
def commandline():
    parser = optparse.OptionParser()
    parser.add_option('-H', '--host', dest="hostname", default="0.0.0.0", help="host adress default is :0.0.0.0")
    parser.add_option('-P', '--port', dest="port", default=8800, help="port NO. default is 8800")
    parser.add_option("-d", '--debug', action="store_true", dest="debug", help="run with debug mode, defult level is info")
    parser.add_option("-l", '--log', default='/tmp/nlslognodemanager.log', dest="logpath", help="nodemanager log")
    return parser.parse_args()

@app.route("/register",methods=["GET"])
def register():
    global master_pipe
    port = request.args.get("port")
    ip = request.remote_addr
    nodestr = 'http://%s:%s;' % (ip, port)
    os.write(master_pipe, nodestr)
    return "ok"

def main():
    global master_pipe
    master_pipe = os.open('/tmp/nls_master', os.O_WRONLY)
    opt, args = commandline()
    handler = logging.FileHandler(opt.logpath)
    if opt.debug:
        handler.setLevel(logging.DEBUG)
    else:
        handler.setLevel(logging.WARNING)

    app.logger.addHandler(handler)
    #app.logger.debug(opt)
    app.run(host=opt.hostname, port=int(opt.port), debug=opt.debug)

if __name__ == '__main__':
    main()
