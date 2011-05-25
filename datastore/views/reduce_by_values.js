function(key, values, rereduce) {
	if (rereduce == false){
		result = {};
		current = values[0];
		total = 0;
		count = 0;
		for(i in values){
			count = count + 1;
			x = values[i];
			if (typeof(x.value)=='number') total = total + x.value;
		}
		result.sum = total;
        result.count = count;
		return result;
	}
	else{
        result = {};
		current = values[0];
		total = 0;
		count = 0;
		for(i in values){
			x = values[i];
			count = count + x.count;
			if (typeof(x.sum)=='number') total = total + x.sum;
		}
        result.sum = total;
        result.count = count;
        return result;
	}

}