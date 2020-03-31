import requests
import os
import subprocess
import shutil
import xml.etree.ElementTree
import py4j.java_gateway
from .constants import *

SUB_PROC, GATEWAY = None, None

def java_test_available():
    return (not is_windows()) and os.path.isfile(ENTRY_JCLASS_JAVA)

def setup_litematica():
    if not is_local_git_repo(LITEMATICA_LOCAL_GIT):
        clone_git_repo(LITEMATICA_GIT_URL, LITEMATICA_LOCAL_GIT)
    else:
        git_pull(LITEMATICA_LOCAL_GIT)
    git_reset(LITEMATICA_LOCAL_GIT)
    git_checkout(LITEMATICA_LOCAL_GIT, LITEMATICA_BRANCH)
    gradle_build(LITEMATICA_LOCAL_GIT)
    fname = gradle_find_latest_build(LITEMATICA_LOCAL_GIT)
    shutil.copyfile(fname, LITEMATICA_FNAME)

def download(url, fname):
    print("Downloading", fname, "from", url, end=" ")
    resp = requests.get(LITEMATICA_URL)
    print("[{}]".format(resp.status_code))
    data = resp.content
    with open(fname, 'wb') as f:
        f.write(data)

def get_litematica_jvm():
    """
    The subprocess needs to be terminated!
    """
    global SUB_PROC, GATEWAY
    if SUB_PROC == None:
        classpath = get_full_classpath_str(LITEMATICA_LOCAL_GIT)
        compile_java(ENTRY_JCLASS_JAVA, classpath)
        cmd = ["java", "-cp", classpath, "EntryPoint"]
        SUB_PROC = subprocess.Popen(cmd)
        try:
            SUB_PROC.wait(1)
        except:
            pass # This is excepted, we are only letting some time for the gateway to start
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

def make_file_available(url, fname, override=False):
    if not os.path.isfile(fname) or override:
        self.download(url, fname)

def is_local_git_repo(directory):
    return os.path.isdir(directory) #TODO More checks

def is_windows():
    return os.name == 'nt'

def clone_git_repo(url, localdir):
    print("Clonning git repo from", url, "to", localdir)
    cmd = ["git", "clone", url, localdir]
    proc = subprocess.run(
            cmd,
        )
    proc.check_returncode()

def git_checkout(repo, branch):
    print("Switching", repo, "to branch", branch)
    cmd = ["git", "checkout", branch]
    proc = subprocess.run(
            cmd,
            cwd=repo
        )
    proc.check_returncode()

def git_pull(repo):
    print("Pulling in", repo)
    cmd = ["git", "pull"]
    proc = subprocess.run(
            cmd,
            cwd=repo
        )
    proc.check_returncode()

def git_reset(repo):
    print("Reseting", repo)
    cmd = ["git", "reset", "--hard"]
    proc = subprocess.run(
            cmd,
            cwd=repo
        )
    proc.check_returncode()

def gradle_build(projectroot):
    if is_windows():
        cmdroot = ["gradlew.bat", ]
    else:
        os.chmod(projectroot + "/gradlew", 0b0111110100) #May need to be changed
        cmdroot = ["./gradlew", ]
    print("Generating eclipse envirronement in", projectroot) # We need this to get the classpath
    proc = subprocess.run(
            cmdroot + ["eclipse",],
            cwd=projectroot
        )
    proc.check_returncode()
    print("Running gradle build in", projectroot)
    proc = subprocess.run(
            cmdroot + ["build",],
            cwd=projectroot
        )
    proc.check_returncode()

def gradle_find_latest_build(projectroot):
    builddir = projectroot + "/build/libs"
    for dirname, dirs, fnames in os.walk(builddir):
        break
    fnames = list(filter(lambda n: n.endswith("dev.jar"), fnames))
    fnames.sort()
    fname = builddir + "/" + fnames[-1]
    print("Found latest build:", fname)
    return fname

def gradle_get_eclipse_classpath(projectroot):
    tree = xml.etree.ElementTree.parse(projectroot + "/.classpath").getroot()
    jars = []
    for tag in tree.findall("classpathentry"):
        if tag.get("kind") == "lib":
            jars.append(tag.get("path"))
    return jars

def get_full_classpath_str(projectroot):
    classpath = gradle_get_eclipse_classpath(projectroot)
    classpath.extend([TEST_PACKAGE + "/", LITEMATICA_FNAME, PY4J_PATH])
    return ":".join(classpath)

def compile_java(fname, classpath):
    print("Compiling", fname)
    cmd = ["javac", "-cp", classpath, fname]
    proc = subprocess.run(
            cmd,
        )
    proc.check_returncode()

