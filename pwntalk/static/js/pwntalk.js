/**
 * Copyright 2014 David Tomaschik <david@systemoverlord.com>
 * 
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 * 
 *     http://www.apache.org/licenses/LICENSE-2.0
 * 
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

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
