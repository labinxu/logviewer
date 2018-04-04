#!/usr/bin/env python
#coding: utf-8
import os, sys, json
import argparse
from pprint import pprint
from utils.util_requests import UtilityRequests
import logging
import atexit

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

def read_nls_info():
    with open(os.path.join(os.environ['HOME'],".nlslog"), 'r') as f:
        data = json.loads(f.read())
        if isinstance(data, unicode):
            data = json.loads(data)
        if isinstance(data['nls_nodes'], unicode):
            data['nls_nodes'] = json.loads(data['nls_nodes'])

        return data

def write_nls_info(data=None):
    data = json.dumps(data)
    with open(os.path.join(os.environ['HOME'],".nlslog"), "wb") as f:
        f.write(data)
        f.flush()

def init_nls_info(node=None):
    if not node:
        nls_run_info = read_nls_info()
        nodes = nls_run_info['nls_nodes']
        url = nls_run_info["nls_active_node"]
        # get the default pwd
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
        # data = get_from_node("ls", node=n)
        # if not data:
        #     return
        # jdata = json.loads(data)
        # print("NODE: %s" % n)
        # for key, files in jdata.iteritems():
        #     #nlsinfo['nls_pwd'] = key
        #     for f in  files.values():
        #         print(f)
        #     break

@NLSLOG_CMD
def remote_cmd(args):
    """find command run on nodes"""
    params = ' '.join(args.args)
    # if not args.all:
    #     data = run_remote_cmd('exe', args=params)
    #     if not data:
    #         return
    #     print('%s:%s' % (NLSINFO['nls_active_node'], NLSINFO['nls_pwd']))
    #     for l in json.loads(data):
    #         print(l)
    #     return

    for n in NLSINFO["nls_nodes"]:
        data = run_remote_cmd('exe', args=params, node=n)
        if not data:
            continue

        print('%s:%s' % (n, NLSINFO['nls_pwd']))
        __output(json.loads(data))

@NLSLOG_CMD
def nodes(args):
    for i, n in enumerate(NLSINFO['nls_nodes']):
        print("[%s]: %s" % (i, n))

@NLSLOG_CMD
def rmnode(args):
    newnode = args.args
    if newnode:
        newnode = newnode[0]
        nodes =  NLSINFO['nls_nodes']
        if newnode.isdigit():
            if len(nodes) > int(newnode):
                del(NLSINFO['nls_nodes'][int(newnode)])
                NLSINFO['nls_active_node'] = NLSINFO['nls_nodes'][0]
            else:
                print('index out of nodes number')
        else:
            NLSINFO['nls_nodes'].remove(newnode)
            NLSINFO['nls_active_node'] = NLSINFO[0]

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
            if newnode not in NLSINFO['nls_nodes']:
                NLSINFO['nls_nodes'].append(newnode)

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
        NLSINFO['nls_nodes'].append(node)
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

global NLSINFO
NLSINFO = init_nls_info()
logger.info("Nls_cmds inited")

@atexit.register
def onexit():
    logger.info("Store the nlsinfo.")
    write_nls_info(NLSINFO)

def main(args=None):
    if args:
        r = parser.parse_args(args)
    else:
        r = parser.parse_args()
    r.func(r)

if __name__ == "__main__":
    main()
