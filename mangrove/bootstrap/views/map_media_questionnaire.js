function(doc) {
    if (doc.document_type == 'FormModel' && doc.xform && doc.is_media_type_fields_present) {
        emit(doc._id, doc);
    }
}
