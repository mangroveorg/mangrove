expected_response_for_get_all_forms = """<forms>
            <form url="baseURL/id">name</form>
            <form url="baseURL/id2">name2</form>
            </forms>"""

expected_xform_for_project_on_reporter = """
<h:html xmlns="http://www.w3.org/2002/xforms" xmlns:h="http://www.w3.org/1999/xhtml"
        xmlns:ev="http://www.w3.org/2001/xml-events" xmlns:xsd="http://www.w3.org/2001/XMLSchema"
        xmlns:jr="http://openrosa.org/javarosa">
    <h:head>
        <h:title>name</h:title>
        <model>
            <instance>
                <data>
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

expected_xform_for_project_on_subject = """
<h:html xmlns="http://www.w3.org/2002/xforms" xmlns:h="http://www.w3.org/1999/xhtml"
        xmlns:ev="http://www.w3.org/2001/xml-events" xmlns:xsd="http://www.w3.org/2001/XMLSchema"
        xmlns:jr="http://openrosa.org/javarosa">
    <h:head>
        <h:title>name</h:title>
        <model>
            <instance>
                <data>
                    <entity_question_code/>                                                                        <code/>
                                                                <form_code>form_code</form_code>
                </data>
            </instance>
                            <bind nodeset="/data/code" type="string" constraint="constraint" required="true()"/>
                        <bind nodeset="/data/form_code" type="string">form_code</bind>

        </model>
    </h:head>
    <h:body>
            <select1 ref="entity_question_code" appearance="quick">
        <label>name</label>
                    <item>
                <label>nameOfEntity (shortCode1)</label>
                <value>shortCode1</value>
            </item>
                    <item>
                <label>nameOfEntity (shortCode1)</label>
                <value>shortCode1</value>
            </item>
            </select1>
                                    <input ref="code">
    <label>name</label>
    <hint>instruction</hint>
</input>
                        </h:body>
</h:html>"""

