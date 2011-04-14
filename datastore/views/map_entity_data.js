function(doc) {
    var isNotNull = function(o) {
        return !((o === undefined) || (o == null));
    };
    if (doc.document_type == 'DataRecord' && isNotNull(doc.entity_backing_field)) {
	emit(doc.entity_backing_field['_id'], doc._id);
    }
}
