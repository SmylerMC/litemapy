import random
from litemapy import Schematic, Region, BlockState

SUB_PROC, GATEWAY = None, None


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
            reg[x, y, z] = s
    return sch
