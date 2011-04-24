function(doc) {
  if (doc.document_type == "EntityType"){
    emit(doc._id, doc.name);
  }
}
