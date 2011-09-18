function(doc) {
        getWeek = function(year,month,day){
    var when = new Date(year,month,day);
    var newYear = new Date(year,0,1);
    var offset = 7 + 1 - newYear.getDay();
    if (offset == 8) offset = 1;
    var daynum = ((Date.UTC(year,when.getMonth(),when.getDate(),0,0,0) - Date.UTC(year,0,1,0,0,0)) /1000/60/60/24) + 1;
    var weeknum = Math.floor((daynum-offset+7)/7);
    if (weeknum == 0) {
        year--;
        var prevNewYear = new Date(year,0,1);
        var prevOffset = 7 + 1 - prevNewYear.getDay();
        if (prevOffset == 2 || prevOffset == 8) weeknum = 53; else weeknum = 52;
    }
    return weeknum;}
    if (!doc.void && doc.document_type == "DataRecord")
    {

        entity_type = doc.entity.aggregation_paths['_type'];
        var date = new Date(doc.event_time);
        for (f in doc.data) {

                value = {};
                value["timestamp"] = date;
                value["value"] = doc.data[f].value;

                    k = [date.getUTCFullYear(),getWeek(date.getUTCFullYear(),date.getMonth()+1,date.getDay()),doc.submission.form_code,entity_type,
doc.entity.short_code,f];
                    emit(k, value);
        }
    }
}
