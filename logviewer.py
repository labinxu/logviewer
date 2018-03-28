from flask import url_for, Flask, render_template, request, redirect
import json, os, sys
from utils.util_requests import UtilityRequests
import multiprocessing, optparse
from multiprocessing import Process

##############################################################
#### pickle error workround
import types
import copy_reg
def _pickle_method(m):
    """fixed pickle error"""
    if m.im_self is None:
        return getattr, (m.im_class, m.im_func.func_name)
    else:
        return getattr, (m.im_self, m.im_func.func_name)

copy_reg.pickle(types.MethodType, _pickle_method)
##############################################################


def commandline():
    parser = optparse.OptionParser()
    parser.add_option('-H', '--hostname',dest='hostname',default="127.0.0.1", help="host server ip")
    parser.add_option('-P', '--port', dest="port", default=8080, type=int, help="port for host")
    parser.add_option('-n', '--node', dest='node', help="view the node nls logs split with ','")
    parser.add_option("-D", '--debug', action="store_true", dest="debug", help="run with debug mode")
    return parser.parse_args()

app = Flask(__name__, template_folder="templates")

class Item():
    """
    file information
    path,attr
    """
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
        """get the files from the node"""
        self.files = []
        try:
            data = self.requests.getContent(self.addr)
            jdata = json.loads(data)
        except Exception as e:
            app.logger.error(e)
            return

        for key, val in jdata.items():
            self.base = key
            for k, v in val.items():
                f = Item(url=os.path.join(self.base, k), path=v, attr=v[0])
                self.files.append(f)
        return self

    def get_data_with_json(self, url):
        try:
            data = self.requests.getContent(url)
            jdata = json.loads(data)
        except Exception:
            app.logger.error("Can not get files from %s" % self.addr)
            return
        for key, val in jdata.items():
            self.base = key
            self.files.extend([Item(url=os.path.join(self.base, k),
                                    path=v, attr=v[0]) for k, v in val.items()])


    def search(self, searchkey):
        url = "%s/search?key=%s" %(self.addr, searchkey)
        self.get_data_with_json(url)
        return self

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

        return self


class LogViewer():
    """
    Init the node configure
    """

    def create_node(self, nodeaddr):
        if not nodeaddr in self.nodes:
            n = Node(nodeaddr)
            self.nodes[nodeaddr] = n
            return n
        else:
            return self.nodes[nodeaddr]

    def __init__(self):
        self.nodes = {}

    def init_nodes(self):
        """
        init the node infor from the configure file
        """
        self.nodes = {}
        app.logger.warning("init LogViewer")
        with open("./config","r") as f:
            self.nodes_addrs = json.loads(f.read().replace('\n',''))
            for node in self.nodes_addrs:
                self.create_node(node)

logviewer = None

@app.route("/")
@app.route("/list")
def list():
    pool = multiprocessing.Pool(4)
    result = []

    for n in logviewer.nodes.itervalues():
        result.append(pool.apply_async(n.list))
    pool.close()
    pool.join()
    nodes = []
    for res in result:
        nodes.append(res.get())
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
    for node in logviewer.nodes.itervalues():
        node.search(searchkey)
        nodes.append(node)
    return render_template("base.html", nodes=nodes)

@app.route("/delete", methods=["POST"])
def delete():
    data = request.get_data()
    app.logger.debug(data)
    jdata = json.loads(data)
    import pdb
    pdb.set_trace()
    for nodeaddr, files in jdata.items():
        node = logviewer.create_node(nodeaddr)
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
    logviewer = LogViewer()
    opt,_ = commandline()
    app.logger.debug(opt)
    hostname = opt.hostname
    port = opt.port
    debug = opt.debug
    nodes = '' if not opt.node else opt.node.split(',')
    if nodes:
        for n in nodes:
            logviewer.create_node(n)
    else:
        logviewer.init_nodes()
    app.run(host=hostname, port=port, debug=debug)
