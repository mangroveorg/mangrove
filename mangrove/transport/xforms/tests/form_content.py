expected_response_for_get_all_forms = """<forms>
                        <formID>name</formID>
            <form url="baseURL/id">name</form>
            <formID>name</formID>

                    <formID>name2</formID>
            <form url="baseURL/id2">name2</form>
            <formID>name2</formID>

            </forms>"""

expected_response_for_get_specific_form = """
<h:html xmlns="http://www.w3.org/2002/xforms" xmlns:h="http://www.w3.org/1999/xhtml"
        xmlns:ev="http://www.w3.org/2001/xml-events" xmlns:xsd="http://www.w3.org/2001/XMLSchema"
        xmlns:jr="http://openrosa.org/javarosa">
    <h:head>
        <h:title>name</h:title>
        <model>
            <instance>
                <data>
                    <eid>{reporter_id}</eid>
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

