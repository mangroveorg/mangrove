import xml.etree.ElementTree as ET
from xml.etree.ElementTree import ElementTree
from xml.dom import minidom
import itertools
import collections
import re

class Xform(object):

    def __init__(self, xform):
        ET.register_namespace('', 'http://www.w3.org/2002/xforms')
        self.root_node = ET.fromstring(xform)

    def get_body_node(self):
        return self.root_node._children[1]

    def _model_node(self):
        return _child_node(_child_node(self.root_node, 'head'), 'model')

    def _instance_id(self, root_node=None):
        return self._instance_root_node(root_node).attrib['id']

    def _instance_root_node(self, root_node=None):
        return _child_node(_child_node(_child_node(root_node or self.root_node, 'head'), 'model'), 'instance')._children[0]

    def instance_node(self, node):
        instance_node = self._instance_root_node()
        if node != self.get_body_node():
            node_name = node.attrib['ref'].split('/')[-1]
            instance_node = itertools.ifilter(lambda child: child.tag.endswith(node_name), self._instance_root_node().iter()).next()
        return instance_node

    def bind_node(self, node):
        return _child_node_given_attr(self._model_node(), 'bind', 'nodeset', node.attrib['ref'])

    def get_bind_node_by_name(self, name):
        return _child_node_given_attr(self._model_node(), 'bind', 'nodeset', name)

    def remove_bind_node(self, node):
        bind_node = self.bind_node(node)
        remove_node(self._model_node(), bind_node)

    def add_bind_node(self, bind_node):
        add_node(self._model_node(), bind_node)

    def remove_instance_node(self, parent_node, node):
        self.instance_node(parent_node).remove(self.instance_node(node))

    def add_instance_node(self, parent_node, instance_node):
        self.instance_node(parent_node).append(instance_node)

    def sort(self):
        self._sort(self._instance_root_node(), lambda node: node.tag)
        self._sort(self.get_body_node(), lambda node: node.attrib.get('ref'))
        self._sort(self._model_node(), lambda node: node.attrib.get('nodeset'))
        self._sort_attrib(_child_nodes(self._model_node(), 'bind'))

    def _sort(self, node, key):
        node._children = sorted(node._children, key=key)
        for child in node._children:
            self._sort(child, key)

    def _sort_attrib(self, nodes):
        for node in nodes:
            node.attrib = dict([(re.sub('\{http://[^ ]*\}','', key), value) for key, value in node.attrib.items()])
            node.attrib = collections.OrderedDict([(x, y) for x, y in sorted(node.attrib.items(), key=lambda t: t[0])])

    def change_instance_id(self, another_xform):
        xform_str = ET.tostring(self.root_node).replace(self._instance_id(), self._instance_id(another_xform.root_node))
        self.root_node = ET.fromstring(xform_str)

    def _to_string(self, root_node=None):
        data = []

        class dummy:
            def write(self, str):
                str = str.strip(' \t\n\r')
                data.append(str)
        file = dummy()

        ElementTree(root_node or self.root_node).write(file)

        return "".join(data)

    def equals(self, another_xform):
        return re.sub('ns[0-9]:','',self._to_string()) == re.sub('ns[0-9]:','',self._to_string(another_xform.root_node))


def get_node(node, field_code):
    for child in node:
        if child.tag.endswith('repeat'):
            for inner_child in child:
                if 'ref' in inner_child.attrib and inner_child.attrib['ref'].endswith(field_code):
                    return inner_child

        if 'ref' in child.attrib and child.attrib['ref'].endswith(field_code):
            return child


def add_node(parent_node, node):
    repeat_node = _child_node(parent_node, 'repeat')
    if repeat_node is not None:
        repeat_node._children.append(node)
    else:
        parent_node._children.append(node)


def remove_node(parent_node, node):
    repeat_node = _child_node(parent_node, 'repeat')
    if repeat_node is not None:
        repeat_node._children.remove(node)
    else:
        parent_node._children.remove(node)


def add_attrib(node, key, value):
    attr_key = _find_key_endswith(key, node.attrib)
    if attr_key:
        key = attr_key[0]
    node.attrib[key] = value


def remove_attrib(node, key):
    attr_key = _find_key_endswith(key, node.attrib)
    if attr_key:
        del node.attrib[attr_key[0]]


def _find_key_endswith(key, attrib):
    attr_key = [k for k in attrib.keys() if k.endswith(key)]
    return attr_key


def add_child(node, tag, value):
    elem = ET.Element(tag)
    elem.text = value
    node._children.append(elem)


def _child_node(node, tag):
    for child in node:
        if child.tag.endswith(tag):
            return child


def _child_nodes(node, tag):
    child_nodes = []
    for child in node:
        if child.tag.endswith(tag):
            child_nodes.append(child)
    return child_nodes


def _child_node_given_attr(node, tag, key, value):
    for child in node:
        if child.tag.endswith(tag) and child.attrib.get(key) and child.attrib.get(key).endswith(value):
            return child

def replace_node_name_with_xpath(value, xform):
    form_code = re.search('\$\{(.*?)\}', value).group(1)
    value_xpath = xform.get_bind_node_by_name(form_code).attrib['nodeset']
    return re.sub(r'(\$\{)(.*?)(\})', " " + value_xpath + " ", value)
