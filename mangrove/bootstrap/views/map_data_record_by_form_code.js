function (doc) {
    if (doc.document_type == 'DataRecord') {
        emit([doc.submission['form_code'],doc.entity['short_code']], doc);
    }
}
