function(doc) {
    var isNotNull = function(o) {
        return !((o === undefined) || (o == null));
    };
    if (doc.document_type == 'DataRecord' && isNotNull(doc.entity_backing_field) && !doc.entity_backing_field['void'] && doc.submission_id) {
	    emit([doc.entity_backing_field['_id'], doc.event_time], {'datarecord': doc, _id: doc.submission_id});
    }
}