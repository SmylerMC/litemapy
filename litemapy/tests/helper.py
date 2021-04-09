import os
import subprocess
import py4j.java_gateway
from .constants import *

SUB_PROC, GATEWAY = None, None

def java_test_available():
    return not is_windows() #TODO

def get_litematica_jvm():
    """
    The subprocess needs to be terminated!
    """
    global SUB_PROC, GATEWAY
    if SUB_PROC == None:
        gwrapper_path = JAVA_TEST_PROJECT + "/gradlew"
        os.chmod(gwrapper_path, 0b0111110100) #May need to be changed
        cmd = [gwrapper_path, "-p", JAVA_TEST_PROJECT, "--console=plain", "run"]
        SUB_PROC = subprocess.Popen(cmd, stdout=subprocess.PIPE)
        line = SUB_PROC.stdout.readline().decode('utf-8')
        while line is not None:
            if "[JAVA] Gateway Server Started..." in line:
                break
            line = SUB_PROC.stdout.readline().decode('utf-8')
        GATEWAY = py4j.java_gateway.JavaGateway()
    return SUB_PROC, GATEWAY

def terminate_litematica_jvm():
    print("Closing gateway")
    GATEWAY.close()
    try:
        SUB_PROC.wait(1)
    except:
        pass # This is excepted, we are only letting some time for the gateway to start
    print("Killing java subprocess")
    SUB_PROC.kill()
    try:
        SUB_PROC.wait(1)
    except:
        pass # This is excepted, we are only letting some time for the gateway to start

def is_windows():
    return os.name == 'nt'
