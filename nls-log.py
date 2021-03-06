#!/usr/bin/env python

import os, sys, json
import argparse
from pprint import pprint
from utils.util_requests import UtilityRequests
import logging


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
        url = nls_run_info["nls_active_node"]
        # get the default pwd
        pwd = connector.getContent(os.path.join(url, "pwd"))
        logger.debug('PWD %s' % pwd)
        nls_run_info['nls_pwd'] = pwd

    return nls_run_info



def get_from_node(cmd, args=None):
    url = os.path.join(NLSINFO["nls_active_node"], cmd)
    params = ''
    if args:
        last = args.pop()
        for name, val in args:
            params += "%s=%s&" % (name,val)
        params += "%s=%s" % last
        url = "%s?%s" % (url, params)
    data = connector.getContent(url)
    return data

def post_from_node(cmd, data):
    url = os.path.join(NLSINFO["nls_active_node"], cmd)
    params = json.dumps(data)
    result = connector.post(url, params)
    return result

###############################################
##decorade NLS command
def NLSLOG_CMD(func):
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
    data = get_from_node("ls")
    #data = connector.getContent(nlsinfo['nls_active_'])

    jdata = json.loads(data)
    for key, files in jdata.iteritems():
        #nlsinfo['nls_pwd'] = key
        for f in  files.values():
            print(f)
        break
    write_nls_info(NLSINFO)

@NLSLOG_CMD
def nodes(args):
    for n in NLSINFO['nls_nodes']:
        print(n)

@NLSLOG_CMD
def node(args):
    """show the active node"""
    # newnode = args.args
    # if newnode:
    #     NLSINFO['nls_active_node'] = newnode[0]
    #     write_nls_info(NLSINFO)
    # else:
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
    # params: ?path="path"
    params = [("file", args.args[0]),]
    #url = "%s/download?path=%s" % (nls_run_info['nls_active_node'], os.path.join(nls_run_info['nls_pwd'], args.args[0]))
    #data = connector.getContent("cp")
    data = get_from_node("cp",args=params)
    with open(destpath, 'w') as f:
        f.write(data)

@NLSLOG_CMD
def addnode(args):
    """add nodes"""
    node = args.args[0]
    if node:
        NLSINFO['nls_nodes'].append(node)
    write_nls_info(NLSINFO)

    nodes(args)

@NLSLOG_CMD
def pwd(args):
    """show current path"""

    res = get_from_node('pwd')
    NLSINFO['nls_pwd'] = res
    print(res)

@NLSLOG_CMD
def cd(args):
    logger.debug('cd %s' % args.args[0])
    NLSINFO['nls_pwd'] = get_from_node("cd",args=[('path', args.args[0])])
    logger.debug('PWD %s' %  NLSINFO['nls_pwd'])
    write_nls_info(json.dumps(NLSINFO))

if __name__ == "__main__":
    global NLSINFO
    NLSINFO = init_nls_info()
    r = parser.parse_args()
    r.func(r)
