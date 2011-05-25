function(doc) {
  if (!doc.void && doc.document_type == "Entity") {
      location_path = doc.aggregation_paths['_geo'];
      entity_type = doc.aggregation_paths['_type'];
      emit([entity_type,location_path], doc._id);
  }
}

