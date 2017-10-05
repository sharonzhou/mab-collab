$(function() {
		var choose_arm = function(id, uid) {
			var game = parseInt($('#game').html());
			var trial = parseInt($('#trial').html());
			$.getJSON($SCRIPT_ROOT + '/_choose_arm', {
				k: id,
				uid: uid,
				game: game,
				trial: trial
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
		$('button').click(function(){ choose_arm(this.id, window.location.pathname.split('/').pop()) });

		var start_game = function(amt_id) {
			$.getJSON($SCRIPT_ROOT + '/_create_user', {
				amt_id: amt_id
			}, function(data) {
				uid = data.uid
				$(location).attr('href', $SCRIPT_ROOT + '/play/' + uid)
			});
		};
		$('#start').click(function(){ start_game($('#amt_id').val()) })
	});