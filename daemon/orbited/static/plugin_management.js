

function displayResult(result) {
	var output = document.getElementById('output');
	output.innerHTML=result[1];

	var success = result[0];
	
	//nice red/green indicator of whether the last call worked
	var flag = document.getElementById('flag');
	if (success) {
		flag.innerHTML = 'Success';
		flag.style.color = 'green';
	}
	else {
		flag.innerHTML = 'FAIL';
		flag.style.color = 'red';
	}
}

function makeLinks(funcs) {
// given a list of function names for a plugin
// return links
	var links = "<ol>";
	for (var i=0; i < funcs.length; i++) {
		links += "<li><a href=# onClick=\"get('";
		links += funcs[i];
		links += "',{}).success = displayResult;\">";
		links += funcs[i];
		links += "</a></li>";
	}
	links += "</ol>";
	return links
}

function getList(result) {
	//populate list of links
	var funcs = document.getElementById('functions');
	funcs.innerHTML = makeLinks(result[1].sort());

	// also, display result
	displayResult(result);
}

function getName(result) {
	//populate list of links
	var nameField = document.getElementById('name');
	nameField.innerHTML = result[1];
}