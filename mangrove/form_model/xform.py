import xml.etree.ElementTree as ET
import itertools

class Xform(object):

    def __init__(self, xform):
        ET.register_namespace('', 'http://www.w3.org/2002/xforms')
        self.root_node = ET.fromstring(xform)

    def get_body_node(self):
        return self.root_node._children[1]

    def _model_node(self):
        return _child_node(_child_node(self.root_node, 'head'), 'model')

    def _instance_id(self):
        return _instance_node().attrib['id']

    def _instance_node(self):
        return _child_node(_child_node(_child_node(self.root_node, 'head'), 'model'), 'instance')._children[0]

    def bind_node(self, node):
        return _child_node_given_attr(self._model_node(), 'bind', 'nodeset', node.attrib['ref'])

    def remove_bind_node(self, node):
        bind_node = self.bind_node(node)
        remove_node(self._model_node(), bind_node)

    def remove_instance_node(self, parent_node, node):
        node_name = node.attrib['ref'].split('/')[-1]
        parent_node_name = parent_node.attrib['ref'].split('/')[-1]
        node_to_be_removed = itertools.ifilter(lambda child: child.tag.endswith(node_name), self._instance_node().iter())
        parent_node = itertools.ifilter(lambda child: child.tag.endswith(parent_node_name), self._instance_node().iter())
        parent_node.next().remove(node_to_be_removed.next())

    def equals(self, another_xform):
        another_xform_str = ET.tostring(another_xform.root_node)\
            .replace(_instance_id(another_xform.root_node), _instance_id(self.root_node))
        return ET.tostring(self.root_node) == another_xform_str


def get_node(node, field_code):
    for child in node:
        if child.tag.endswith('repeat'):
            for inner_child in child:
                if 'ref' in inner_child.attrib and inner_child.attrib['ref'].endswith(field_code):
                    return inner_child

        if 'ref' in child.attrib and child.attrib['ref'].endswith(field_code):
            return child


def remove_node(parent_node, node):
    parent_node._children.remove(node)


def add_attrib(node, key, value):
    attr_key = [k for k in node.attrib.keys() if k.endswith(key)]
    if attr_key:
        key = attr_key[0]
    node.attrib[key] = value


def add_child(node, tag, value):
    elem = ET.Element(tag)
    elem.text = value
    node._children.append(elem)


def _child_node(node, tag):
    for child in node:
        if child.tag.endswith(tag):
            return child


def _child_node_given_attr(node, tag, key, value):
    for child in node:
        if child.tag.endswith(tag) and child.attrib.get(key) and child.attrib.get(key).endswith(value):
            return child