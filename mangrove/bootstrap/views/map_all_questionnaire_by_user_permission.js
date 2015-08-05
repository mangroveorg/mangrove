function(doc) {
    if (doc.document_type == 'UserPermission' && !doc.void) {
		for(i=0;i<doc.project_ids.length;i++){
			emit(doc.user_id,{_id:doc.project_ids[i]})		
		}
    }
}