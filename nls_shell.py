import sys, subprocess
import shlex, json
import os, json
import mmap, contextlib

SHELL_STATUS_RUN=1
SHELL_STATUS_STOP=0

nls_run_info = {
    'nls_pwd':'',
    'nls_nodes':''
}

def init_environ():
    with open(os.path.join(os.environ['HOME'],".nlsnodes")) as f:
        nls_run_info['nls_nodes']=f.read()

    nls_run_info['nls_active_node'] = json.loads(nls_run_info['nls_nodes'])[0]
    nls_run_info['nls_pwd'] = nls_run_info['nls_active_node']
    #init file
    print('init environ file')
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
        cmd_tokens=tokenize("python nls-log.py %s" % cmd)
        status=execute(cmd_tokens)

def main():
    init_environ()
    shell_loop()


if __name__=="__main__":
    main()
