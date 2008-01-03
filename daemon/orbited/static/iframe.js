function extract_xss_domain(old_domain) {
  domain_pieces = old_domain.split('.');
  if (domain_pieces.length === 4) {
    var is_ip = !isNaN(Number(domain_pieces.join('')));
    if (is_ip) {
      return old_domain;
    }
  }
  return domain_pieces.slice(-2).join('.');
}

function reload() {
  // TODO: There should not be an alert here!
  alert('reload....');
}

window.onError = null;
document.domain = extract_xss_domain(document.domain);
parent.Orbited.attach_iframe(this);
// FIXME: Define this in orbited.js
p = function() {}