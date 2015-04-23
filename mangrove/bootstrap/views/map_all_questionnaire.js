function(doc) {
   if (doc.document_type == 'FormModel' && !doc.void && doc.form_code != 'reg' && doc.form_code != 'delete'){
                emit([doc.created,doc.name.toLowerCase()], doc);
   }
}
