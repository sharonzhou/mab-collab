$(function() {
	var table = '<table><tr>';
	for (var i=0; i<20; i++) {
		table += '<th>' + String(i + 1) + '</th>';
	}
	table += '</tr><tr>';
	for (var i=0; i<20; i++) {
		table += '<td id="td-game-' + String(i + 1) + '">-</td>';
	}
	table += '</tr></table>';
	$('#table').append(table);
	var choose_arm = function(id, uid) {
		var game = parseInt($('#game').html());
		var trial = parseInt($('#trial').html());
		$.getJSON($SCRIPT_ROOT + '/_choose_arm', {
			k: id,
			uid: uid,
			game: game,
			trial: trial
		}, function(data) {
			if ($("#gameover").length != 0 || $('#nextbutton').length != 0) {
				return;
			}

			var score = data.score;
			var reward = data.reward;
			$('#reward').text(reward);
			if (reward == 1) {
				$('#reward').css('color', '#2c7bb6');
				$('#score').text(score);
				$('#reward').fadeOut(50);
				$('#score').fadeOut(50);
				$('#reward').fadeIn(25);
				$('#score').fadeIn(25);
			} else {
				$('#reward').css('color', '#d7191c');				
				$('#reward').fadeOut(50);
				$('#reward').fadeIn(25);
			}

			var game = data.game;
			var nextTrial = data.trial;
			var nextGameBtnBool = data.next_game_button;
			console.log(nextTrial);
			if (nextGameBtnBool) {
				$('#td-game-' + game).text(score);
				var nextGame = game + 1;
				if (nextGame > 20) {
					$.getJSON($SCRIPT_ROOT + '/_completion_code', {
						uid: data.uid
					}, function(data_hidden) {
						if ($("#gameover").length == 0) {
							code = data_hidden.code
							$('body').append('<div><span id="gameover">Gameover!</span> Completion code: ' + code + '</div>');
						}
					});
				} else { 
					$('#nextbutton_wrapper').append('<button id="nextbutton">Go to next game</button>');
				}
			} else {
				$('#trial').text(nextTrial);
			}

		});
		return false;
	};

	if (typeof vars !== 'undefined') {
		$('button').click(function(){ choose_arm(this.id, vars.uid) });
	};

	var start_game = function(amt_id) {
		$.getJSON($SCRIPT_ROOT + '/_create_user', {
			amt_id: amt_id
		}, function() {
			$(location).attr('href', $SCRIPT_ROOT)
		});
	};
	$('#start').click(function(){ start_game($('#amt_id').val()) })

	var next_game = function() {
		$.getJSON($SCRIPT_ROOT + '/_next_game', {
		}, function(data) {
			$('#nextbutton_wrapper').html('');
			$('#score').text(data.score);
			$('#reward').text('0 or 1');
			$('#reward').css('color', 'black');

			$('#game').text(data.game);
			$('#trial').text(data.trial);
		});
	}
	$('#nextbutton_wrapper').on('click', '#nextbutton', function(){
    	next_game();
	});
});