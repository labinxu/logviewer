from flask import url_for, Flask, render_template, request, redirect
import json, os, sys
from utils.util_requests import UtilityRequests


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
    def __init__(self, addr, files=[]):
        self.addr = addr
        self.files = files
        self.requests = UtilityRequests(domain='')

    def delete(self, files):
        app.logger.warning("delete %s" % str(files))
        url = ("%s/delete") % self.addr
        self.requests.post(url,data=json.dumps(files))

    def download(self):
        response = self.requests.post("%s/download" % self.addr, data=json.dumps(self.files))
        app.logger.warning(response.content)
        return json.loads(response.content)["file"]

    def list(self):
        self.files = []
        try:
            data = self.requests.getContent(self.addr)
            jdata = json.loads(data)
        except Exception:
            return

        for key, val in jdata.items():
            self.base = key
            for k, v in val.items():
                f = Item(url=os.path.join(self.base, k), path=v, attr=v[0])
                self.files.append(f)
            break

    def get_data_with_json(self, url):
        try:
            data = self.requests.getContent(url)
            jdata = json.loads(data)
        except Exception:
            app.logger.error("Can not get files from %s" % self.addr)
            return
        for key, val in jdata.items():
            self.base = key
            for k, v in val.items():
                f = Item(url=os.path.join(self.base, k), path=v, attr=v[0])
                self.files.append(f)
            break

    def search(self, searchkey):
        url = "%s/search?key=%s" %(self.addr, searchkey)
        self.get_data_with_json(url)

    def show(self, path):
        requests = UtilityRequests(domain='')
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
    Nodes = {}
    @classmethod
    def create_node(cls, nodeaddr):
        if not nodeaddr in cls.Nodes:
            n = Node(nodeaddr)
            cls.Nodes[nodeaddr] = n
            return n
        else:
            return cls.Nodes[nodeaddr]


    def __init__(self):
        """
        init the node infor from the configure file
        """
        app.logger.warning("init LogViewer")
        with open("./config","r") as f:
            self.nodes_addrs = json.loads(f.read().replace('\n',''))


logviewer = LogViewer()


@app.route("/")
@app.route("/list")
def list():
    nodes = []
    for addr in logviewer.nodes_addrs:
        node = logviewer.create_node(addr)
        node.list()
        nodes.append(node)
    return render_template("base.html",nodes=nodes)

@app.route("/show", methods=['GET'])
def show():
    path = request.args.get('path')
    n = request.args.get('node')
    node = logviewer.create_node(n)
    node.show(path)
    return render_template("base.html",nodes=[node])

@app.route("/search", methods=["GET"])
def search():
    searchkey = request.args.get('key')
    app.logger.debug("in search GET: %s" % searchkey)
    nodes = []
    for node in logviewer.nodeMgr.get_nodes():
        node.search(searchkey)
        nodes.append(node)
    return render_template("base.html", nodes=nodes)

@app.route("/delete", methods=["POST"])
def delete():
    data = request.get_data()
    app.logger.debug(data)
    jdata = json.loads(data)

    for nodeaddr, files in jdata.items():
        node = LogViewer.create_node(nodeaddr)
        node.delete(files)
    return json.dumps({'status':'ok'})

@app.route("/download", methods=["POST"])
def download():
    if request.method == "POST":
        data = request.get_data()
        app.logger.debug(data)
        jdata = json.loads(data)
        data = {}
        for n , files in jdata.items():
            node = Node(n, files)
            filepath = node.download()
            app.logger.debug(filepath)
            data[n] = "%s/download?path=%s" % (n, filepath)

        return json.dumps(data.values())
    else:
        filepath = request.args.get("path")
        app.logger.debug("Download file %s" % filepath)
        url = request.args.get('addr')
        return redirect(url_for(url+"/download", filename=filepath))

if __name__ == "__main__":
    app.debug = True


    app.run(port=8080)
