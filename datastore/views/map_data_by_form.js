function(doc) {
    if (!doc.void && doc.document_type == "DataRecord" && doc.submission.form_code != null
)
    {
        var time = Date.parse(doc.event_time);
        var short_code = doc.entity.short_code;
        var form_code = doc.submission.form_code;
        for (k in doc.data) {
            value = {};
            value["value"] = doc.data[k].value;
            value["timestamp"] = time;
            value["short_code"] = short_code
            key = [form_code,short_code,k,time]
            emit(key, value)
        }
    }
}