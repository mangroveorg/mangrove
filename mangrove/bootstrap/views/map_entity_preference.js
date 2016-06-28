function(doc) {
    if (doc.document_type == 'EntityPreference' && !doc.void) {
        emit([doc.org_id, doc.entity_type], doc);
    }
}
