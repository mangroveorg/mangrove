function(doc) {
/** 
 * Get the ISO week date week number 
 */  
Date.prototype.getWeek = function () {  
    // Create a copy of this date object  
    var target  = new Date(this.valueOf());  
  
    // ISO week date weeks start on monday  
    // so correct the day number  
    var dayNr   = (this.getDay() + 6) % 7;  
  
    // Set the target to the thursday of this week so the  
    // target date is in the right year  
    target.setDate(target.getDate() - dayNr + 3);  
  
    // ISO 8601 states that week 1 is the week  
    // with january 4th in it  
    var jan4    = new Date(target.getFullYear(), 0, 4);  
  
    // Number of days between target date and january 4th  
    var dayDiff = (target - jan4) / 86400000;    
  
    // Calculate week number: Week 1 (january 4th) plus the    
    // number of weeks between target date and january 4th    
    var weekNr = 1 + Math.ceil(dayDiff / 7);    
  
    return weekNr;    
}    
    if (!doc.void && doc.document_type == "DataRecord")
    {

        entity_type = doc.entity.aggregation_paths['_type'];
        var date = new Date(doc.event_time);
        for (f in doc.data) {
            value = doc.data[f].value;
            if (typeof(value) == 'number') {
                    k = [date.getUTCFullYear(),date.getWeek(),doc.submission.form_code,entity_type,
doc.entity.short_code,f];
                    emit(k, value);
            }
        }
    }
}
