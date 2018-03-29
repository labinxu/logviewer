#!/usr/bin/env python

import os, sys, json
import argparse
from pprint import pprint
from utils.util_requests import UtilityRequests

connector = UtilityRequests()
parser = argparse.ArgumentParser(prog='nls-log')
subparsers = parser.add_subparsers(title='subcommands',
                                       description='valid subcommands',
                                       help='additional help',
                                       dest='subcmd')


def read_nls_info():
    with open(os.path.join(os.environ['HOME'],".nlslog"), 'r') as f:
            return json.loads(f.read())

def write_nls_info(data=None):
    data = json.dumps(data)
    with open(os.path.join(os.environ['HOME'],".nlslog"), "wb") as f:
        f.write(data)
        f.flush()

def init_nls_inf():
    nls_run_info = read_nls_info()
    return nls_run_info


###############################################
##decorade NLS command
def NLSLOG_CMD(func):
    cmdline = subparsers.add_parser(func.__name__)
    cmdline.add_argument('args', nargs="*", help=func.__doc__)
    cmdline.set_defaults(func=func)
    return func


@NLSLOG_CMD
def ls(args):
    """list the files in current folder"""
    nlsinfo = init_nls_inf()
    data = connector.getContent(nlsinfo['nls_pwd'])
    jdata = json.loads(data)
    for key, files in jdata.iteritems():
        nlsinfo['nls_pwd'] = key
        for f in  files.values():
            print(f)
        break
    write_nls_info(nlsinfo)

@NLSLOG_CMD
def nodes(args):
    nls_run_info = init_nls_inf()
    for n in json.loads(nls_run_info['nls_nodes']):
        print(n)

@NLSLOG_CMD
def node(args):
    nls_run_info = init_nls_inf()
    nls_run_info['nls_active_node'] = args.args[0]
    write_nls_info(nls_run_info)


@NLSLOG_CMD
def cp(args):
    """download the file
    eg: cp src dest"""
    nls_run_info = init_nls_inf()
    assert(len(args.args) >= 2)
    dest = args.args.pop()
    destfolder = False
    home = os.environ["HOME"]
    dest = dest.replace('~', home)
    if os.path.isdir(dest):
        destfolder = True

    for f in args.args:
        url = "%s/download?path=%s" % (nls_run_info['nls_active_node'], os.path.join(nls_run_info['nls_pwd'], f))
        data = connector.getContent(url)
        if destfolder:
            d = os.path.join(dest, f)
        else:
            d = dest

        with open(d, 'w') as f:
            f.write(data)


@NLSLOG_CMD
def addnode(args):
    """add nodes"""
    print(ls.__name__)

@NLSLOG_CMD
def pwd(args):
    """show current path"""
    pass

@NLSLOG_CMD
def cd(args):
    print('cd %s' % args.args[0])
    nls_run_info = init_nls_inf()
    nls_run_info['nls_pwd'] = args.args[0]
    write_nls_info(json.dumps(nls_run_info))

if __name__ == "__main__":
    r = parser.parse_args()
    r.func(r)











