$(function() {
    var choose_arm = function(id) {
      $.getJSON($SCRIPT_ROOT + '/_choose_arm', {
        k: id
      }, function(data) {
        $('#reward').text(data.reward);
      });
      return false;
    };
    $('button').click(function(){ choose_arm(this.id) });
  });