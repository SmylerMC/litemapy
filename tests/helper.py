import os
import random
import subprocess
import py4j.java_gateway
from litemapy import Schematic, Region, BlockState
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
        SUB_PROC = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        line = SUB_PROC.stdout.readline().decode('utf-8')
        while line is not None:
            if "[JAVA] Gateway Server Started..." in line:
                break
            elif "FAILED" in line:
                raise RuntimeError("Failed to create test JVM")
            line = SUB_PROC.stdout.readline().decode('utf-8')
        GATEWAY = py4j.java_gateway.JavaGateway()
    return SUB_PROC, GATEWAY

def terminate_litematica_jvm():
    print("Closing gateway")
    GATEWAY.close()
    try:
        SUB_PROC.wait(1)
    except:
        pass # This is excepted, we are only letting some time for the gateway to stop
    print("Killing java subprocess")
    SUB_PROC.kill()
    try:
        SUB_PROC.wait(1)
    except:
        pass # This is excepted, we are only letting some time for the gateway to stop

def is_windows():
    return os.name == 'nt'

def randomstring(length):
    al = "AZERTYUIOPQSDFGHJKLMWXCVBNazertyuiopqsdfghjklmwxcvbn0123456789"
    s = ""
    for i in range(length):
        s += random.choice(al)
    return s

def randomblockstate():
    ids = ("air", "stone", "granite", "diorite", "andesite", "dirt", "grass_block", "cobblestone", "oak_planks")
    return BlockState("minecraft:" + random.choice(ids))

def randomschematic(regsize=20, regspread=20, regprob=0.8, blockprob=0.999):
    sch = Schematic(name=randomstring(15), author=randomstring(15), description=randomstring(100))
    while random.random() < regprob or len(sch.regions) <= 0:
        x = random.randrange(-regspread, regspread)
        y = random.randrange(-regspread, regspread)
        z = random.randrange(-regspread, regspread)
        width = random.randrange(-regsize, regsize)
        height = random.randrange(-regsize, regsize)
        length = random.randrange(-regsize, regsize)
        if width == 0 or height == 0 or length == 0:
            pass
        else:
            sch.regions[randomstring(10)] = Region(x, y, z, width, height, length)
    for reg in sch.regions.values():
        while random.random() < blockprob:
            s = randomblockstate()
            mix, max = reg.minx(), reg.maxx()
            miy, may = reg.miny(), reg.maxy()
            miz, maz = reg.minz(), reg.maxz()
            x = random.randint(mix, max)
            y = random.randint(miy, may)
            z = random.randint(miz, maz)
            print("schemblock", mix, max, miy, may, miz, maz, x, y, z)
            reg.setblock(x, y, z, s)
    return sch
