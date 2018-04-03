#!/usr/bin/env python

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
REMOTE_CMDS = ['find']
LOCAL_CMDS = ['vi', 'vim']

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
        try:
            pwd = connector.getContent(os.path.join(url, "pwd"))
        except Exception as e:
            active = False
            while not active:
                for node in nodes:
                    url = node
                    try:
                        pwd = connector.getContent(os.path.join(url, "pwd"))
                    except Exception as er:
                        continue
                    nls_run_info["nls_active_node"] = node
                    active = True
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
    cmdline.set_defaults(func=func)
    return func

############################################
@NLSLOG_CMD
def rm(args):
    return post_from_node('rm', data=args.args)

@NLSLOG_CMD
def ls(args):
    """list the files in current folder"""

    for n in NLSINFO['nls_nodes']:
        data = get_from_node("ls", node=n)
        if not data:
            return
        jdata = json.loads(data)
        print("NODE: %s" % n)
        for key, files in jdata.iteritems():
            #nlsinfo['nls_pwd'] = key
            for f in  files.values():
                print(f)
            break

@NLSLOG_CMD
def remote_cmd(args):
    """find command run on nodes"""
    cmd = "exe"
    params = ' '.join(args.args)
    data = run_remote_cmd(cmd, args=params)
    print(data)

@NLSLOG_CMD
def nodes(args):
    for i, n in enumerate(NLSINFO['nls_nodes']):
        print("[%s]: %s" % (i, n))

@NLSLOG_CMD
def node(args):
    """show the active node"""
    newnode = args.args
    if newnode:
        newnode = newnode[0]
        nodes =  NLSINFO['nls_nodes']
        if newnode.isdigit() and len(nodes) > int(newnode):
            NLSINFO['nls_active_node'] = nodes[int(newnode)]
        else:
            NLSINFO['nls_active_node'] = newnode
            if newnode not in NLSINFO['nls_nodes']:
                NLSINFO['nls_nodes'].append(newnode)

    print(NLSINFO['nls_active_node'])

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
    #write_nls_info(json.dumps(NLSINFO))

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
