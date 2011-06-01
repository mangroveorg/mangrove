function(doc) {
  if (!doc.void && doc.document_type == "DataRecord") {
    var date = Date.parse(doc.event_time);
    var entity = doc.entity_backing_field;
    var short_code = entity.short_code;
    var form_code = doc.form_code
    for (k in doc.data){
      value = {};
      key = [form_code,date,k];
      value["timestamp"] = date;
      value["value"] = doc.data[k].value;
      value["short_code"] = short_code;
      emit(key, value);
    }
  }
}