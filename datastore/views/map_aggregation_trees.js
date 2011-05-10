function(doc) {
  if (doc.document_type == "AggregationTree"){
    emit(doc._id, doc.name);
  }
}
