import xml.etree.ElementTree as ET
from xml.etree.ElementTree import ElementTree
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
        return \
        _child_node(_child_node(_child_node(root_node or self.root_node, 'head'), 'model'), 'instance')._children[0]

    def instance_node(self, node):
        if node == self.get_body_node():
            return self._instance_root_node()
        node_name = node.attrib['ref'].split('/')[-1]
        return self.instance_node_given_name(node_name)

    def instance_node_given_name(self, node_name):
        return itertools.ifilter(lambda child: child.tag.endswith(node_name), self._instance_root_node().iter()).next()

    def bind_node(self, node):
        return _child_node_given_attr(self._model_node(), 'bind', 'nodeset', node.attrib['ref'])

    def get_bind_node_by_name(self, name):
        return _child_node_given_attr(self._model_node(), 'bind', 'nodeset', name)

    def get_readonly_bind_nodes(self):
        return itertools.ifilter(lambda child: not child.attrib.get('nodeset').endswith('instanceID'),
                                 child_nodes_given_attr(self._model_node(), 'bind', 'readonly', 'true()'))

    def remove_bind_node(self, node):
        bind_node = node if node.tag.endswith('bind') else self.bind_node(node)
        remove_node(self._model_node(), bind_node)

    def remove_bind_node_given_name(self, name):
        remove_node(self._model_node(), self.get_bind_node_by_name(name))

    def add_translation_node(self, node):
        add_node(self._translation_root_node(), node)

    def remove_translation_nodes(self, node):
        nodes_to_be_removed = self.get_translation_nodes(node)
        for translation_node in nodes_to_be_removed:
            remove_node(self._translation_root_node(), translation_node)

    def get_translation_nodes(self, node):
        return [translation_node for translation_node in self._translation_root_node()
                if self._cascade_instance_id(node) in translation_node.attrib['id']]

    def add_cascade_instance_node(self, node):
        add_node(self._model_node(), node)

    def remove_cascade_instance_node(self, node):
        remove_node(self._model_node(), self.get_cascade_instance_node(node))

    def get_cascade_instance_node(self, node):
        return _child_node_given_attr(self._model_node(), "instance", "id", self._cascade_instance_id(node))

    def _cascade_instance_id(self, node):
        return re.search("instance\('(.*)'\)", _child_node(node, "itemset").attrib['nodeset']).group(1)

    def _translation_root_node(self):
        return _child_node(_child_node(self._model_node(), "itext"), "translation")

    def add_bind_node(self, bind_node):
        add_node(self._model_node(), bind_node)

    def remove_instance_node(self, parent_node, node):
        self.instance_node(parent_node).remove(self.instance_node(node))

    def remove_instance_node_given_name(self, parent_node, name):
        self.instance_node(parent_node).remove(self.instance_node_given_name(name))

    def add_instance_node(self, parent_node, instance_node):
        self.instance_node(parent_node).append(instance_node)

    def add_node_given_parent_node(self, parent_node, node):
        if parent_node != self.get_body_node():
            parent_node_name = parent_node.attrib.get('ref').split('/')[-1]
            parent_node =  itertools.ifilter(lambda child: child.attrib.get('ref') is not None and
                                                           child.attrib.get('ref').endswith(parent_node_name),
                                             self.get_body_node().iter()).next()
        add_node(parent_node, node)

    def _add_useful_cascade_instance_ids(self, node, useful_cascade_instance_ids):
        if _child_node(node, "itemset") is not None:
            useful_cascade_instance_ids.append(self._cascade_instance_id(node))

        for child in node:
            self._add_useful_cascade_instance_ids(child, useful_cascade_instance_ids)

    def remove_undesirable_cascade_instance_nodes(self):
        useful_cascade_instance_ids = []
        self._add_useful_cascade_instance_ids(self.get_body_node(), useful_cascade_instance_ids)

        for node in child_nodes(self._model_node(), "instance"):
            if node.attrib.get("id") is not None and node.attrib.get("id") not in useful_cascade_instance_ids:
                for child in _child_node(node, "root"):
                    translation_node = \
                        _child_node_given_attr(self._translation_root_node(), "text", "id", _child_node(child, "itextId").text)
                    remove_node(self._translation_root_node(), translation_node)

                remove_node(self._model_node(), node)

    def node_given_bind_node(self, bind_node):
        def _has_child_with_ref(node, value):
            return node._children and _child_node_given_attr(node, None, 'ref', value) is not None

        node = itertools.ifilter(lambda child: _has_child_with_ref(child, bind_node.attrib.get('nodeset')),
                                 self.get_body_node().iter()).next()

        return (node, _child_node_given_attr(node, None, 'ref', bind_node.attrib.get('nodeset')))

    def instance_node_given_bind_node(self, bind_node):
        def _has_child_with_tag(node, value):
            return node._children and _child_node(node, value) is not None

        node = itertools.ifilter(lambda child: _has_child_with_tag(child, bind_node.attrib.get('nodeset').split('/')[-1]),
                                 self._instance_root_node().iter()).next()

        return (node, _child_node(node, bind_node.attrib.get('nodeset').split('/')[-1]))

    def remove_node_given_bind_node(self, bind_node):
        parent_node, node = self.node_given_bind_node(bind_node)
        remove_node(parent_node, node)

    def remove_instance_node_given_bind_node(self, bind_node):
        parent_node, node = self.instance_node_given_bind_node(bind_node)
        remove_node(parent_node, node)

    def sort(self):
        _sort(self._instance_root_node(), lambda node: node.tag)
        _sort(self.get_body_node(), lambda node: (node.attrib.get('ref'), None if _child_node(node, 'value') is None else getattr(_child_node(node, 'value'), 'text', None)))
        _sort(self._model_node(), lambda node: (node.attrib.get('id'), node.attrib.get('nodeset')))
        _sort_attrib(child_nodes(self._model_node(), 'bind'))

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
        return re.sub('ns[0-9]:', '', self._to_string()) == re.sub('ns[0-9]:', '',
                                                                   self._to_string(another_xform.root_node))


def _sort(node, key):
    node._children = sorted(node._children, key=key)
    for child in node._children:
        _sort(child, key)


def _sort_attrib(nodes):
    for node in nodes:
        node.attrib = dict([(_remove_namespace_from_tagname(key), value) for key, value in node.attrib.items()])
        node.attrib = collections.OrderedDict([(x, y) for x, y in sorted(node.attrib.items(), key=lambda t: t[0])])


def _remove_namespace_from_tagname(tagname):
    return re.sub('\{http://[^ ]*\}', '', tagname)


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


def add_child(node, tag, value):
    elem = ET.Element(tag)
    elem.text = value
    node._children.append(elem)
    return elem


def child_nodes(node, tag):
    child_nodes = []
    for child in node:
        if child.tag.endswith(tag):
            child_nodes.append(child)
    return child_nodes


def child_nodes_given_attr(node, tag, key, value):
    child_nodes = []
    for child in node:
        if child.tag.endswith(tag) and child.attrib.get(key) and child.attrib.get(key).endswith(value):
            child_nodes.append(child)
    return child_nodes


def node_has_child(node, child_tag, child_value):
    return _child_node(node, child_tag) is not None and _child_node(node, child_tag).text == child_value


def update_node(node, child_tag, child_value):
    if _child_node(node, child_tag) is not None:
        _child_node(node, child_tag).text = child_value


def replace_node_name_with_xpath(value, xform):
    form_code = re.search('\$\{(.*?)\}', value).group(1)
    value_xpath = xform.get_bind_node_by_name(form_code).attrib['nodeset']
    return re.sub(r'(\$\{)(.*?)(\})', " " + value_xpath + " ", value)


def _find_key_endswith(key, attrib):
    attr_key = [k for k in attrib.keys() if k.endswith(key)]
    return attr_key


def _child_node(node, tag):
    for child in node:
        if child.tag.endswith(tag):
            return child


def _child_node_given_attr(node, tag, key, value):
    for child in node:
        tag_condition = True if tag is None else child.tag.endswith(tag)
        if tag_condition and child.attrib.get(key) and child.attrib.get(key).endswith(value):
            return child
