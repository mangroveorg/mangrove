function(doc) {
    if (doc.document_type == 'FormModel' && !doc.void) {
        emit(doc.form_code, doc);
    }
}
