expected_response_for_get_all_forms = """<?xml version=\'1.0\' encoding=\'UTF-8\' ?>
<xforms xmlns="http://openrosa.org/xforms/xformsList">
                        <xform>
                <formID>name</formID>
                <name>name</name>
                <downloadUrl>baseURL/id</downloadUrl>
            </xform>
                    <xform>
                <formID>name2</formID>
                <name>name2</name>
                <downloadUrl>baseURL/id2</downloadUrl>
            </xform>
            </xforms>"""

expected_xform_for_project_on_reporter = """
<h:html xmlns="http://www.w3.org/2002/xforms" xmlns:h="http://www.w3.org/1999/xhtml"
        xmlns:ev="http://www.w3.org/2001/xml-events" xmlns:xsd="http://www.w3.org/2001/XMLSchema"
        xmlns:jr="http://openrosa.org/javarosa">
    <h:head>
        <h:title>name</h:title>
        <model>
            <instance>
                <data id="id">
                    <eid>rep1</eid>
                    <code/>
                    <form_code>form_code</form_code>
                </data>
            </instance>
                <bind nodeset="/data/code" type="string" constraint="constraint" required="true()"/>
                <bind nodeset="/data/form_code" type="string">form_code</bind>
        </model>
    </h:head>
    <h:body>
        <input ref="code">
            <label>name</label>
            <hint>instruction</hint>
        </input>
        </h:body>
</h:html>"""


expected_xform_with_escaped_characters = """
<h:html xmlns="http://www.w3.org/2002/xforms" xmlns:h="http://www.w3.org/1999/xhtml"
        xmlns:ev="http://www.w3.org/2001/xml-events" xmlns:xsd="http://www.w3.org/2001/XMLSchema"
        xmlns:jr="http://openrosa.org/javarosa">
    <h:head>
        <h:title>&lt;mock_name</h:title>
        <model>
            <instance>
                <data id="id">
                    <eid>rep1</eid>
                    <selectcode/>
                    <form_code>form_code</form_code>
                </data>
            </instance>
            <bind nodeset="/data/selectcode" type="select1" constraint="" required="true()"/>
            <bind nodeset="/data/form_code" type="string">form_code</bind>

        </model>
    </h:head>
    <h:body>
        <select1 ref="selectcode" appearance="quick">
            <label>name&amp;</label>
            <hint>Choose answer(s) from the list.</hint>
            <item>
                <label>option1&amp;</label>
                <value>None</value>
            </item>

        </select1>
    </h:body>
</h:html>"""

expected_xform_for_project_with_unique_id = """
<h:html xmlns="http://www.w3.org/2002/xforms" xmlns:h="http://www.w3.org/1999/xhtml"
        xmlns:ev="http://www.w3.org/2001/xml-events" xmlns:xsd="http://www.w3.org/2001/XMLSchema"
        xmlns:jr="http://openrosa.org/javarosa">
    <h:head>
        <h:title>name</h:title>
        <model>
            <instance>
                <data id="id">
                    <eid>rep1</eid>                                            <code/>
                                            <cl/>
                                        <form_code>form_code</form_code>
                </data>
            </instance>
                            <bind nodeset="/data/code" type="string" constraint="constraint" required="true()"/>
                            <bind nodeset="/data/cl" type="unique_id" constraint="" required="true()"/>
                        <bind nodeset="/data/form_code" type="string">form_code</bind>

        </model>
    </h:head>
    <h:body>
                            <input ref="code">
    <label>name</label>
    <hint>instruction</hint>
</input>
                    <select1 ref="cl" appearance="quick">
        <label>cl</label>
                    <item>
                <label>nameOfEntity (shortCode1)</label>
                <value>shortCode1</value>
            </item>
                    <item>
                <label>nameOfEntity (shortCode1)</label>
                <value>shortCode1</value>
            </item>
        </select1>
            </h:body>
</h:html>"""

