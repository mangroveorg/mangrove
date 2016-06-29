function(doc) {
    if (doc.document_type == 'EntityPreference' && !doc.void) {
        emit(doc.share_token, doc);
    }
}
