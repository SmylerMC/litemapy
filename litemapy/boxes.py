Coordinate = tuple[int, int, int]


def block_is_in_box(block: Coordinate, box: tuple[Coordinate, Coordinate]) -> bool:
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
    x_min, x_max = xs
    y_min, y_max = ys
    z_min, z_max = zs
    return x_min <= x <= x_max and y_min <= y <= y_max and z_min <= z <= z_max


def box_is_in_box(box1: tuple[Coordinate, Coordinate], box2: tuple[Coordinate, Coordinate]) -> bool:
    return block_is_in_box(box1[0], box2) and block_is_in_box(box1[1], box2)
