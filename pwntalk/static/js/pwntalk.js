var showmodal = function(name) {
  $(name).modal('show');
};

$('#new-post-link').click(function() {
  document.location.hash = '#postbox=#post-modal';
  showmodal('#post-modal');
  return false;
});

$('#register-link').click(function() {
  showmodal('#register-modal');
  return false;
});

/*
 * If we include postbox=#post-modal, show it.
 */
$(document).ready(function() {
  var hash = document.location.hash;
  if (!hash)
    return;
  if (hash[0] == '#')
    hash = hash.substr(1);
  $.each(hash.split('&'), function(idx, seg) {
    var parts = seg.split('=');
    if (parts.length != 2)
      return;
    if (parts[0] == 'postbox')
      showmodal(decodeURIComponent(parts[1]));
  });
});

/*
 * API for posting on behalf of a user.
 */
var autoPost = function(text) {
  var form = $('#new-post-form');
  form.find('textarea[name="text"]').val(text);
  form.submit();
};
