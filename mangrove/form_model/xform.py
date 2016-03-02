import xml.etree.ElementTree as ET

class Xform(object):

    def __init__(self, xform):
        ET.register_namespace('', 'http://www.w3.org/2002/xforms')
        self.root_node = ET.fromstring(xform)

    def get_node(self, node, field_code):
        for child in node:
            if 'ref' in child.attrib and child.attrib['ref'].endswith(field_code):
                return child

    def get_body_node(self):
        return self.root_node._children[1]

    def equals(self, another_xform):
        another_xform_str = ET.tostring(another_xform.root_node)\
            .replace(self._instance_node(another_xform.root_node), self._instance_node(self.root_node))
        return ET.tostring(self.root_node) == another_xform_str

    def _instance_node(self, node):
        return node._children[0]._children[1]._children[00]._children[0].attrib['id']