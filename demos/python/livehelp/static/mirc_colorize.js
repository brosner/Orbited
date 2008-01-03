// Copyright (c) 2006 Chris Chabot <chabotc@xs4all.nl>
//
// this script is freely distributable under the terms of an MIT-style license.
// For details, see the web site: http://www.chabotc.nl/

function colorize (message) {
	var pageBack  = 'white';
	var pageFront = 'black';
	var length    = message.length;
	var newText   = '';
	var bold      = false;
	var color     = false;
	var reverse   = false;
	var underline = false;
	var foreColor = '';
	var backColor = '';
	for (var i = 0 ; i < length ; i++) {
		switch (message.charAt(i)) {
			case String.fromCharCode(2):
				if (bold) {
					newText += '</b>';
					bold     = false;
				} else {
					newText += '<b>';
					bold    = true;
				}
				break;
			case String.fromCharCode(3):
				if (color)	{
					newtext += '</span>';
					color = false;
				}
				foreColor = '';
				backColor = '';
				if ((parseInt(message.charAt(i+1)) >= 0) && (parseInt(message.charAt(i+1)) <= 9)) {
					color = true;
					if ((parseInt(message.charAt(++i+1)) >= 0) && (parseInt(message.charAt(i+1)) <= 9)) {
						foreColor = getColor(parseInt(message.charAt(i)) * 10 + parseInt(message.charAt(++i)));
					} else {
						foreColor = getColor(parseInt(message.charAt(i)));
					}
					if ((message.charAt(i+1) == ',') && (parseInt(message.charAt(++i+1)) >= 0) && (parseInt(message.charAt(i+1)) <= 9)) {
						if ((parseInt(message.charAt(++i+1)) >= 0) && (parseInt(message.charAt(i+1)) <= 9)) {
							backColor = getColor(parseInt(message.charAt(i)) * 10 + parseInt(message.charAt(++i)));
						} else {
							backColor = getColor(parseInt(message.charAt(i)));
						}
					}
				}
				if (foreColor) {
					newText += '<span style="color:'+foreColor;
					if (backColor) {
						newText += ';background-color:'+backColor;
					}
					newText += '">';
				}
				break;
			case String.fromCharCode(15):
				if (bold) {
					newText += '</b>';
					bold     = false;
				}
				if (color) {
					newText += '</span>';
					color    = false;
				}
				if (reverse) {
					newText += '</span>';
					reverse  = false;
				}
				if (underline) {
					newText  += '</u>';
					underline = false;
				}
				break;
			case String.fromCharCode(22):
				if (reverse) {
					newText += '</span>';
					reverse  = false;
				} else {
					newText += '<span style="color:'+pageBack+';background-color:'+pageFront+'">';
					reverse  = true;
				}
			case String.fromCharCode(31):
				if (underline) {
					newText  += '</u>';
					underline = false;
				} else {
					newText  += '<u>';
					underline = true;
				}
			default:
				newText += message.charAt(i);
				break;
		}

	}
	if (bold)      newText += '</b>';
	if (color)     newText += '</span>';
	if (reverse)   newText += '</span>'
	if (underline) newText += '</u>';
	return newText;
}

function getColor(numeric)
{
	var num = parseInt(numeric);
	switch (num) {
		case 0:  return 'white';
		case 1:  return 'black';
		case 2:  return 'navy';
		case 3:  return 'green';
		case 4:  return 'red';
		case 5:  return 'maroon';
		case 6:  return 'purple';
		case 7:  return 'olive';
		case 8:  return 'yellow';
		case 9:  return 'lime';
		case 10: return 'teal';
		case 11: return 'aqua';
		case 12: return 'blue';
		case 13: return 'fuchsia';
		case 14: return 'gray';
		default: return 'silver';
	}
}
