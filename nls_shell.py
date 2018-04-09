import sys, subprocess
import shlex, json
import os, json
import threading
import optparse, logging

# from evdev import InputDevice
# from select import select
""".nlslog store the runtime value
the current path nls_pwd, current node is nls_active_node"""
SHELL_STATUS_RUN=1
SHELL_STATUS_STOP=0
nls_run_info = {
    'nls_pwd':'',
    'nls_nodes':[]
}
###

def commandline():
    parser = optparse.OptionParser()
    parser.add_option('-l', '--log', dest="logpath", default="/tmp/nlslogtrans.log", help="path of the nls log transfer")
    parser.add_option("-d", '--debug', action="store_true", dest="debug", help="log level debug,if not set the log level is error")
    parser.add_option("-w", '--warning', action="store_true", dest="warning", help="log level warning,if not set the log level is error")

    return parser.parse_args()


def init_nodes():
    nlsnodes = os.path.join(os.environ['HOME'],".nlsnodes")
    if not os.path.exists(nlsnodes):
        nls_run_info['nls_nodes'].append('http://127.0.0.1:8000')
        return

    with open(os.path.join(os.environ['HOME'],".nlsnodes")) as f:
        for l in f.readlines():
            nls_run_info['nls_nodes'].append(l.strip())

nlslog = os.path.join(os.environ['HOME'],".nlslog")
if not os.path.exists(nlslog):
    init_nodes()
    nls_run_info['nls_active_node'] = nls_run_info['nls_nodes'][0]
    nls_run_info['nls_pwd'] = nls_run_info['nls_active_node']
    data = json.dumps(nls_run_info)
    with open(os.path.join(os.environ['HOME'],".nlslog"), "w") as f:
        f.write(data)
        f.flush()

import nls_cmds
###########

def tokenize(string):
    return shlex.split(string)

def execute(cmd_tokens):
    """execute the nls-log command"""
    pid=os.fork()
    if pid==0:
        os.execvp(cmd_tokens[0], cmd_tokens)
    elif pid>0:
        while True:
            wpid, status=os.waitpid(pid,0)
            if os.WIFEXITED(status) or os.WISIGNALED(status):
                break
    return SHELL_STATUS_RUN


def shell_loop():
    status=SHELL_STATUS_RUN
    while status==SHELL_STATUS_RUN:
        sys.stdout.write('nls-log>>')
        sys.stdout.flush()
        cmd=sys.stdin.readline()
        cmd = cmd.strip()
        if not cmd:
            continue
        if cmd == "clear":
            sys.stdout.write("\n"*100)
            sys.stdout.flush()
            continue
        if cmd == 'exit' or cmd=='quit':
            status = SHELL_STATUS_STOP
            os._exit(0)

        cc = tokenize(cmd)
        ccmd = cc[0].lower()
        if ccmd in ['?', '-h', '--help']:
            t = threading.Thread(target=nls_cmds.main,args=(cc, ) )
            t.start()
            t.join()
            continue

        # local cmds like vi/vim /emacs
        if ccmd in nls_cmds.LOCAL_CMDS:
            cmd_tokens = tokenize(cmd)
            t = threading.Thread(target=execute, args=(cc, ) )
            t.start()
            t.join()
        elif ccmd in nls_cmds.CMDS:
            t = threading.Thread(target=nls_cmds.main,args=(cc, ) )
            t.start()
            t.join()
            # the complex command like find . | grep 
        elif ccmd in nls_cmds.REMOTE_CMDS:
            cc = ["remote_cmd", "%s"%cmd]
            t = threading.Thread(target=nls_cmds.main, args=(cc
, ) )
            t.start()
            t.join()
        else:
            print("%s is not the nls_log command!")

def main():
    opt, var = commandline()

    ### the logger config
    fh = logging.FileHandler(opt.logpath)

    if opt.debug:
        nls_cmds.logger.setLevel(logging.DEBUG)
        fh.setLevel(logging.DEBUG)
    elif opt.warning:
        nls_cmds.logger.setLevel(logging.WARNING)
        fh.setLevel(logging.WARNING)
    else:
        nls_cmds.logger.setLevel(logging.ERROR)
        fh.setLevel(logging.ERROR)
    nls_cmds.logger.addHandler(fh)
    # enter the shell loop
    shell_loop()

if __name__=="__main__":
    main()
