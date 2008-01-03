// * get selection start and end
// * work back to previous word
// * filter list of names by word
// * order remaining names starting alphabetically after the current selection
// * replace selection with bit from list item


// make lastIndexOf work in browsers other than Firefox
if (!Array.prototype.lastIndexOf)
{
  Array.prototype.lastIndexOf = function(elt /*, from*/)
  {
    var len = this.length;
    var from = Number(arguments[1]);
    if (isNaN(from)) {from = len - 1;}
    else
    {
      from = (from < 0) ? Math.ceil(from) : Math.floor(from);
      if (from < 0) {from += len;}
      else if (from >= len) {from = len - 1;}
    }
    for (; from > -1; from--)
    {
      if (from in this && this[from] === elt) {return from;}
    }
    return -1;
  };
}

tc = {
  selectionInfo: function (field) {
    var selStart = selEnd = 0;
    var selText = "";
  
    // Internet Explorer
    if (document.selection) {
      field.focus();
    
      // create dummy range, then set its end point to that of the actual
      // selection, then compare those lengths to get start/end positions
      var range = document.selection.createRange();
      var stored_range = range.duplicate();
      stored_range.moveToElementText(element);
      stored_range.setEndPoint('EndToEnd', range);
      selStart = stored_range.text.length - range.text.length;
      selEnd = stored_range.text.length;
      selText = range.text;
    }
    // Gecko/Webkit
    else if (field.selectionStart || field.selectionStart == '0') {
      selStart = field.selectionStart;
      selEnd = field.selectionEnd;
      selText = field.value.slice(selStart, selEnd);
    };
  
    return [selStart, selEnd, selText]
  },

  replaceSelection: function (field, replacement) {
    // Internet Explorer
    if (document.selection) {
      field.focus();
      document.selection.createRange().text = replacement;
    }
    // Gecko/Webkit
    else if (field.selectionStart || field.selectionStart == '0') {
      var selStart = field.selectionStart;
      var selEnd = field.selectionEnd;
      var text = field.value;
      var before = text.slice(0, field.selectionStart);
      var after = text.slice(field.selectionEnd);
      field.value = before + replacement + after;
      field.setSelectionRange(selStart, selStart + replacement.length);
    };
  },

  prefix: function (string, position) {
    // gets the word leading up to the caret or selection start
    var prefixStart = string.slice(0, position).lastIndexOf(" ") + 1;
    return string.slice(prefixStart, position);
  },

  nextUser: function (prefix, selection, users) {
    // filter list of users by prefix, then grab the next one after the
    // selection alphabetically
    var userList = [prefix + selection];
    for (var user in users) {
      if (user.indexOf(prefix) == 0) {
        userList.push(user);
      };
    };
    userList.sort();
    var nextUserIndex = (userList.lastIndexOf(prefix + selection) + 1) % userList.length;
  
    return userList[nextUserIndex];
  }
};