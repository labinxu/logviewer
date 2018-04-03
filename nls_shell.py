import sys, subprocess
import shlex, json
import os, json
import nls_cmds
import threading
# from evdev import InputDevice
# from select import select
""".nlslog store the runtime value
the current path nls_pwd, current node is nls_active_node"""

SHELL_STATUS_RUN=1
SHELL_STATUS_STOP=0

nls_run_info = {
    'nls_pwd':'',
    'nls_nodes':''
}

# def history():
#     dev = InputDevice("/dev/input/event4")
#     while True:
#         select([dev], [], [])
#         for event in dev.read():
#             print("code: %s value:%s" % (event.code, event.value))



def init_environ():
    """init the configure values"""
    nlslog = os.path.join(os.environ['HOME'],".nlslog")
    if os.path.exists(nlslog):
        return
    with open(os.path.join(os.environ['HOME'],".nlsnodes")) as f:
        nls_run_info['nls_nodes']=f.read()

    nls_run_info['nls_active_node'] = json.loads(nls_run_info['nls_nodes'])[0]
    nls_run_info['nls_pwd'] = nls_run_info['nls_active_node']
    data = json.dumps(nls_run_info)
    with open(os.path.join(os.environ['HOME'],".nlslog"), "wb") as f:
        f.write(data)
        f.flush()

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
        sys.stdout.write('>> ')
        sys.stdout.flush()
        cmd=sys.stdin.readline()
        cmd = cmd.strip()
        if not cmd:
            continue
        if cmd == "clear":
            sys.stdout.write("\n"*100)
            sys.stdout.flush()
            continue
        cc = tokenize(cmd)

        if cc[0] not in nls_cmds.CMDS:
            print('RUN %s' % cmd)
            cmd_tokens = tokenize(cmd)
            t = threading.Thread(target=execute, args=(cc, ) )
            t.start()
            t.join()
        else:
            cmd_tokens=tokenize("python nls-log.py %s" % cmd)
            t = threading.Thread(target=nls_cmds.main,args=(cc, ) )
            t.start()
            t.join()

def main():
    init_environ()
    shell_loop()


if __name__=="__main__":
    main()
