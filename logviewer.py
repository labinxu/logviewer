from flask import url_for, Flask, render_template
import json, requests


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
    addr = ''
    files = []
    def __init__(self, addr):
        self.addr = addr

class NodeMgr:
    """
    Node information manager
    ip:port
    """
    def __init__(self, nodesinfo):
        for node in nodesinfo:
            app.logger.debug("node address %s" % node["addr"])
        self.nodesinfo = nodesinfo

    def get_nodes(self):
        nodes = []
        for node in self.nodesinfo:
            nd = Node(node["addr"])

    def update(self):
        pass


class LogViewer():
    """
    Init the node configure
    """
    def __new__(cls, *args, **kwargs):
        app.logger.error("LogViewer New")

        #import pdb
        #pdb.set_trace()
    def __init__(self):
        app.logger.debug("init LogViewer")
        with open("./config","r") as f:
            nodes = json.loads(f.read().replace('\n',''))
            ndmgr = NodeMgr(nodes)
            self.nodes = ndmgr.get_nodes()

    @app.route("/")
    def index():
        nodes = []
        for i in range(3):
            node = Node("%s"%i)
            node.files = [Item("url","path %s" %0, 0),Item("url%s"%i,"path %s"%1, 1)]
            nodes.append(node)

        return render_template("base.html",nodes=nodes)


logviewer = LogViewer()
if __name__ == "__main__":
    app.debug = True
    app.run(port=8080)
