import unittest
import litemapy.boxes as boxes

class TestBoxes(unittest.TestCase):

    def setUp(self):
        self.origin = (0, 0, 0)
        self.block1 = (-2, -2, -2)
        self.block2 = (2, 2, 2)
        self.block3 = (1, 2, 3)
        self.block4 = (-4, -4, -4)
        self.block5 = (4, 4, 4)
        self.centeredbox1 = (self.block1, self.block2)
        self.centeredbox2 = (self.block4, self.block5)
        self.box1 = (self.origin, self.block2)
        self.box2 = (self.block1, self.block5)
        self.box3 = (self.block1, self.block4)

    def test_block_is_in_box(self):
        self.assertTrue(boxes.block_is_in_box(self.origin, self.centeredbox1))
        self.assertFalse(boxes.block_is_in_box(self.block3, (self.block1, self.block2)))

    def test_box_is_in_box(self):
        self.assertTrue(boxes.box_is_in_box(self.centeredbox1, self.centeredbox2))
        self.assertTrue(boxes.box_is_in_box(self.box1, self.centeredbox2))
        self.assertFalse(boxes.box_is_in_box(self.centeredbox2, self.centeredbox1))
        self.assertFalse(boxes.box_is_in_box(self.box1, self.box3))
