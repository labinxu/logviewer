#!/usr/bin/env python
#coding: utf-8

"""
nls_cmds module include a thread for node register
nls commands:
cd ls node remove etc,
usage: ./nls_shell
--help
:::::

usage: nls-log [-h]
               {remove,ls,remote_cmd,nodes,rmnode,node,cp,addnode,pwd,cd} ...

optional arguments:
  -h, --help            show this help message and exit

subcommands:
  valid subcommands

  {remove,ls,remote_cmd,nodes,rmnode,node,cp,addnode,pwd,cd}
                        additional help
"""


import os, sys, json
import multiprocessing as mp
from multiprocessing import Manager

import argparse
#!/usr/bin/env python

from utils.util_requests import UtilityRequests
import nodemanager
import logging, threading
import atexit, time, signal


### global variables
global NLSINFO
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
connector = UtilityRequests()

parser = argparse.ArgumentParser(prog='nls-log')
subparsers = parser.add_subparsers(title='subcommands',
                                       description='valid subcommands',
                                       help='additional help',
                                       dest='subcmd')
CMDS = []
REMOTE_CMDS = ['find', 'grep', 'awk', 'sed']
LOCAL_CMDS = ['vi', 'vim']

# config file for local and remote commands
# remote commands will executed on remote server and return the output through http
# local commands will executed on bash environment not nls_shell

cmdconfig = os.path.join(os.environ['HOME'], ".nlscmds")
if os.path.exists(cmdconfig):
    with open(cmdconfig, 'r') as f:
        data = json.loads(f.read())
        REMOTE_CMDS = data['remote_cmds']
        LOCAL_CMDS = data['local_cmds']
else:
    with open(cmdconfig, 'w') as f:
        data = {}
        data['remote_cmds'] = REMOTE_CMDS
        data['local_cmds'] = LOCAL_CMDS
        f.write(json.dumps(data))
########################################################
#end init commands


###########################################
#signal handle

def sigint_handler(signum, frame):
    os._exit(0)

signal.signal(signal.SIGINT, sigint_handler)
signal.signal(signal.SIGHUP, sigint_handler)
signal.signal(signal.SIGTERM, sigint_handler)
####

def read_nls_info():
    NLSINFO = {}
    with open(os.path.join(os.environ['HOME'],".nlslog"), 'r') as f:
        data = json.loads(f.read())
        if isinstance(data, unicode):
            data = json.loads(data)
        if isinstance(data['nls_nodes'], unicode):
            data['nls_nodes'] = json.loads(data['nls_nodes'])

        NLSINFO['nls_nodes'] = data['nls_nodes']
        NLSINFO['nls_pwd'] = data['nls_pwd']
        NLSINFO['nls_active_node'] = data['nls_active_node']
        return NLSINFO

def write_nls_info(data=None):
    data = json.dumps(data)
    with open(os.path.join(os.environ['HOME'],".nlslog"), "wb") as f:
        f.write(data)
        f.flush()


pipe_name = '/tmp/nls_master'
global master_pipe

global nodemanager_p
global register_p
global register_lock
global POLLING

def register(NLSINFO, pipe_name, lock, polling):
    global master_pipe

    master_pipe = os.open(pipe_name, os.O_RDONLY)
    line = ''
    while polling:
        line += os.read(master_pipe, 128)
        line = line.strip()
        if not line:
            time.sleep(1)
            continue

        if line[-1] != ';':
            linedata = [l for l in line.split(';')[0:-1] if l != '']
        else:
            linedata = [l for l in line.split(';') if l != '']

        for l in linedata:

            if l not in NLSINFO['nls_nodes']:
                logger.info('add new node %s' % l)
                lock.acquire()
                NLSINFO['nls_nodes'].append(l)
                lock.release()

def start_register():
    if not os.path.exists(pipe_name):
        os.mkfifo(pipe_name)

    global nodemanager_p
    global register_p
    global register_lock
    global POLLING
    # nodemanager_p = mp.Process(target=nodemanager.main)
    # nodemanager_p.start()

    register_lock = threading.Lock()
    register_p = threading.Thread(target=register, args=(NLSINFO, pipe_name, register_lock, POLLING))
    register_p.start()
###############################################################

def init_nls_info(node=None):
    if not node:
        nls_run_info = read_nls_info()
        nodes = nls_run_info['nls_nodes']
        url = nls_run_info["nls_active_node"]
        pwd = ''
        try:
            pwd = connector.getContent(os.path.join(url, "pwd"))
        except Exception as e:
            active = False
            while not active:
                for node in nodes:
                    url = node
                    try:
                        url = os.path.join(url, "pwd")
                        pwd = connector.getContent(url)
                    except Exception as er:
                        continue
                    nls_run_info["nls_active_node"] = node
                    active = True
                    break
                break

        logger.debug('PWD %s' % pwd)
        nls_run_info['nls_pwd'] = pwd

    return nls_run_info


def get_from_node(cmd, args=None, node=None):
    if not node:
        url = os.path.join(NLSINFO["nls_active_node"], cmd)
    else:
        url = os.path.join(node, cmd)

    params = ''
    data = None
    if args:
        last = args.pop()
        for name, val in args:
            params += "%s=%s&" % (name,val)
        params += "%s=%s" % last
        url = "%s?%s" % (url, params)
    try:
        data = connector.getContent(url)
    except Exception as e:
        logger.error(str(e))
    return data

def run_remote_cmd(cmd, args=None, node=None):
    if not node:
        url = os.path.join(NLSINFO["nls_active_node"], cmd)
    else:
        url = os.path.join(node, cmd)

    params = '?cmdline=%s' % args if args else ''
    data = None
    try:
        data = connector.getContent('%s%s'%(url, params))
        if connector.status_code != 200:
            logger.info("%s. status_code: %s" % (url, connector.status_code))
            data = None
    except Exception as e:
        logger.error(str(e))

    return data

def post_from_node(cmd, data):
    url = os.path.join(NLSINFO["nls_active_node"], cmd)
    params = json.dumps(data)
    result = None
    try:
        result = connector.post(url, params)
    except Exception as e:
        logger.error(str(e))

    return result

###############################################
##decorade NLS command
def NLSLOG_CMD(func):
    CMDS.append(func.__name__)
    cmdline = subparsers.add_parser(func.__name__)
    cmdline.add_argument('args', nargs="*", help=func.__doc__)
    cmdline.add_argument('--all', action="store_true", dest="all", help="run the command on all nodes")
    cmdline.set_defaults(func=func)
    return func

############################################
@NLSLOG_CMD
def remove(args):
    """remote files"""
    return post_from_node('rm', data=args.args)

def __output(lines):
    for l in lines:
        print(l.encode('utf-8', errors='ignore'))

def __do_ls(node=None):
    node = NLSINFO["nls_active_node"] if not node else node
    data = get_from_node("ls", node=node)
    if not data:
        return
    jdata = json.loads(data)
    print("NODE: %s" % node)
    for key, files in jdata.iteritems():
        __output(files.values())
        break

@NLSLOG_CMD
def ls(args):
    """list the files in current folder"""
    if not args.all:
        return __do_ls()


    for n in NLSINFO['nls_nodes']:
        __do_ls(node=n)

@NLSLOG_CMD
def remote_cmd(args):
    """these commands that will running on nodes"""
    params = ' '.join(args.args)
    for n in NLSINFO["nls_nodes"]:
        data = run_remote_cmd('exe', args=params, node=n)
        if not data:
            continue

        print('%s:%s' % (n, NLSINFO['nls_pwd']))
        __output(json.loads(data))

@NLSLOG_CMD
def nodes(args):
    register_lock.acquire()
    for i, n in enumerate(NLSINFO['nls_nodes']):
        print("[%s]: %s" % (i, n))
    register_lock.release()

@NLSLOG_CMD
def rmnode(args):
    newnode = args.args
    if newnode:
        newnode = newnode[0]
        nodes =  NLSINFO['nls_nodes']
        if newnode.isdigit():
            if len(nodes) > int(newnode):
                del(NLSINFO['nls_nodes'][int(newnode)])
                try:
                    NLSINFO['nls_active_node'] = NLSINFO['nls_nodes'][0]
                except Exception as e:
                    logger.warning(str(e))
                    NLSINFO['nls_active_node'] = None

            else:
                print('index out of nodes number')
        else:
            if newnode in NLSINFO['nls_nodes']:
                NLSINFO['nls_nodes'].remove(newnode)
                NLSINFO['nls_active_node'] = NLSINFO[0]
            else:
                logger.warning('%s not in the node list' % newnode)

@NLSLOG_CMD
def node(args):
    """show the active node"""
    newnode = args.args
    if newnode:
        newnode = newnode[0]
        nodes =  NLSINFO['nls_nodes']
        if newnode.isdigit():
            if len(nodes) > int(newnode):
                NLSINFO['nls_active_node'] = nodes[int(newnode)]
            else:
                print('index out of nodes number')
        else:
            NLSINFO['nls_active_node'] = newnode
            register_lock.acquire()
            if newnode not in NLSINFO['nls_nodes']:
                NLSINFO['nls_nodes'].append(newnode)
            register_lock.release()

    res = get_from_node('pwd')
    if not res:
        return
    NLSINFO['nls_pwd'] = res
    print("%s:%s" % (NLSINFO['nls_active_node'], res))


@NLSLOG_CMD
def cp(args):
    """download the file
    eg: cp src dest"""
    assert(len(args.args) >= 2)
    home = os.environ["HOME"]
    dest = args.args.pop()
    dest = dest.replace('~', home)
    destpath = os.path.abspath(dest)

    if os.path.isdir(destpath):
        destpath = os.path.join(destpath, args.args[0])
        logger.debug("destpath %s" % destpath)

    f = args.args[0]
    params = [("file", args.args[0]),]
    data = get_from_node("cp",args=params)
    if not data:
        return
    with open(destpath, 'w') as f:
        f.write(data)

@NLSLOG_CMD
def addnode(args):
    """add nodes"""
    node = args.args[0]
    if node:
        register_lock.acquire()
        NLSINFO['nls_nodes'].append(node)
        register_lock.release()
        #write_nls_info(NLSINFO)
    nodes(args)

@NLSLOG_CMD
def pwd(args):
    """show current path"""
    res = get_from_node('pwd')
    if not res:
        return
    NLSINFO['nls_pwd'] = res
    print(res)

@NLSLOG_CMD
def cd(args):
    logger.debug('cd %s' % args.args[0])
    curpath = get_from_node("cd",args=[('path', args.args[0])])
    if not curpath:
        return
    NLSINFO['nls_pwd'] = curpath
    logger.debug('PWD %s' %  NLSINFO['nls_pwd'])

NLSINFO = init_nls_info()
logger.info("Nls_cmds inited")
POLLING = True
start_register()

@atexit.register
def onexit():
    global master_pipe
    logger.info("Store the nlsinfo.")
    register_lock.acquire()
    write_nls_info(NLSINFO)
    register_lock.release()

    if register_p.is_alive():
        register_p.terminate()

    if nodemanager_p.is_alive():
        nodemanager_p.terminate()

    os.close(master_pipe)

def quit():
    global POLLING
    POLLING = False
    os._exit(0)

def main(args=None):
    if args:
        r = parser.parse_args(args)
    else:
        r = parser.parse_args()
    r.func(r)

if __name__ == "__main__":
    main()
