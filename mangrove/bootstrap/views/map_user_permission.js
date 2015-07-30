function(doc) {
    if (doc.document_type == 'UserPermission' && !doc.void) {
        emit(doc.user_id, doc);
    }
}
