$(function() {
    var choose_arm = function(id) {
      $.getJSON($SCRIPT_ROOT + '/_choose_arm', {
        k: id
      }, function(data) {
        var reward = data.reward;
        $('#reward').text(reward);
        if (reward == 1) {
          $('#score').text(parseInt($('#score').html()) + 1)
        }
        var nextTrial = parseInt($('#trial').html()) + 1;
        if (nextTrial > 15) {
          var nextGame = parseInt($('#game').html()) + 1;
          if (nextGame > 20) {
            $('body').append('<div>Gameover</div>');
          } else { 
            $('#game').text(nextGame);
            $('#trial').text('1');
            $('#score').text('0');
          }
        } else {
          $('#trial').text(nextTrial);
        }

      });
      return false;
    };
    $('button').click(function(){ choose_arm(this.id) });
  });