function(doc) {
  if (doc.document_type == "Entity") {
	emit( [doc.aggregation_paths['_type'],doc.short_code], 1);
  }
}