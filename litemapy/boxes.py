def block_is_in_box(block, box):
    """
    Returns True id the block is in the box
    block is (x, y, z)
    box is ((x0, y0, z0), (x1, y1, z1))
    """
    x, y, z = block
    xs = [box[0][0], box[1][0]]
    xs.sort()
    ys = [box[0][1], box[1][1]]
    ys.sort()
    zs = [box[0][1], box[1][1]]
    zs.sort()
    xmin, xmax = xs
    ymin, ymax = ys
    zmin, zmax = zs
    return xmin <= x <= xmax and ymin <= y <= ymax and zmin <= z <= zmax

def box_is_in_box(box1, box2):
    return block_is_in_box(box1[0], box2) and block_is_in_box(box1[1], box2)
