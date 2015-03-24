function(doc) {
    if (doc.document_type == 'group' ) {
            emit(doc.name, 1);
    }
}