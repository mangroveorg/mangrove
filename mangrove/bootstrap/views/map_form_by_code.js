function(doc) {
    if (doc.document_type == 'FormModel' && !doc.void) {
        emit(doc.code, doc);
    }
}
