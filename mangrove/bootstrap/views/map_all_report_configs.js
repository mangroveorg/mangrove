function(doc) {
    if (doc.document_type == 'ReportConfig') {
        emit(doc._id, doc);
    }
}
