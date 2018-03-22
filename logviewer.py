from flask import url_for, Flask, render_template, request, redirect
import json, os, sys
from utils import util_requests


app = Flask(__name__, template_folder="templates")

class Item():
    """
    file information
    path,attr
    """
    url = "url"
    path = "path"
    attr = "folder"
    def __init__(self, url, path, attr):
        self.url = url
        self.path = path
        self.attr = attr

class Node:
    """
    address or port
    files
    """
    def __init__(self, addr):
        self.addr = addr

    def list(self):
        requests = util_requests.UtilityRequests(domain='')
        app.logger.debug(self.addr)
        data = requests.getContent(self.addr)
        jdata = json.loads(data)
        self.files = []
        for key, val in jdata.items():
            self.base = key
            for k, v in val.items():
                f = Item(url=os.path.join(self.base, k), path=v, attr=v[0])
                self.files.append(f)
            break

        app.logger.debug(self.files)

    def show(self, path):
        requests = util_requests.UtilityRequests(domain='')
        url = "%s/show?path=%s" %(self.addr,path)
        app.logger.debug(url)
        data = requests.getContent(url)
        jdata = json.loads(data)
        self.files = []
        for key, val in jdata.items():
            self.base = key
            for k, v in val.items():
                f = Item(url=os.path.join(self.base, k), path=v, attr=v[0])
                app.logger.debug('%s %s'%(f.path, f.attr))
                self.files.append(f)
            break

        app.logger.debug(self.files)

class NodeMgr:
    """
    Node information manager
    ip:port
    """
    def __init__(self, nodesinfo):
        for node in nodesinfo:
            app.logger.debug("node address %s" % node["addr"])
        self.nodesinfo = nodesinfo
        self.nodes = {}

    def get_nodes(self):
        for node in self.nodesinfo:
            self.nodes[node['addr']] = Node(node["addr"])
        return self.nodes.values()

    def update(self):
        pass

class LogViewer():
    """
    Init the node configure
    """
    nodeMgr = ''
    def __init__(self):
        """
        init the node infor from the configure file
        """
        app.logger.error("init LogViewer")
        with open("./config","r") as f:
            nodes = json.loads(f.read().replace('\n',''))
            LogViewer.nodeMgr = NodeMgr(nodes)

    @app.route("/")
    @app.route("/list")
    def list():
        nodes = []
        for node in LogViewer.nodeMgr.get_nodes():
            node.list()
            nodes.append(node)
        return render_template("base.html",nodes=nodes)

@app.route("/show", methods=['GET'])
def show():
    path = request.args.get('path')
    n = request.args.get('node')
    node = LogViewer.nodeMgr.nodes[n]
    node.show(path)
    return render_template("base.html",nodes=[node])



@app.route("/download", methods=["GET", "POST"])
def download():
    filepath = request.args.get("path")
    app.logger.debug("Download file %s" % filepath)
    url = request.args.get('addr')
    return redirect(url_for(url+"/download", filename=filepath))

if __name__ == "__main__":
    app.debug = True
    logviewer = LogViewer()
    
    app.run(port=8080)
