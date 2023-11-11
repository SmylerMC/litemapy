import litemapy.boxes as boxes

origin = (0, 0, 0)
block1 = (-2, -2, -2)
block2 = (2, 2, 2)
block3 = (1, 2, 3)
block4 = (-4, -4, -4)
block5 = (4, 4, 4)
centered_box_1 = (block1, block2)
centered_box_2 = (block4, block5)
box1 = (origin, block2)
box2 = (block1, block5)
box3 = (block1, block4)


def test_block_is_in_box():
    assert boxes.block_is_in_box(origin, centered_box_1)
    assert not (boxes.block_is_in_box(block3, (block1, block2)))


def test_box_is_in_box():
    assert boxes.box_is_in_box(centered_box_1, centered_box_2)
    assert boxes.box_is_in_box(box1, centered_box_2)
    assert not boxes.box_is_in_box(centered_box_2, centered_box_1)
    assert not boxes.box_is_in_box(box1, box3)
