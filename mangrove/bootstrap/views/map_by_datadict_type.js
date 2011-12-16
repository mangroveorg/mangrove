function(doc) {
    if (doc.document_type == 'DataDict') {
        emit(doc.slug, doc._id);
    }
}
