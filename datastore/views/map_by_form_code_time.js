function(doc) {
    if (!doc.void && doc.document_type == "DataRecord"
)
    {
        var date = Date.parse(doc.event_time);
        var entity = doc.entity;
        var entity_type = entity.aggregation_paths['_type'];
        var entity_id = entity._id;
        var form_code = doc.submission.form_code;
        for (k in doc.data) {
            value = doc.data[k].value;
            key = [form_code,date,entity_id,k];
            emit(key, value);
        }
    }
}

