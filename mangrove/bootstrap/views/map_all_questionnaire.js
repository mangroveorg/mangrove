function(doc) {
    if (doc.document_type == 'FormModel') {
        emit(doc._id, doc);
    }
}
