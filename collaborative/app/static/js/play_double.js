$(function() {
	console.log('play_double.js', vars)
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

	var display_state = function(uid, score, reward, game, trial, nextGameBtnBool, completionCodeBool, scores=[]) {
		// If your turn:
			// enable buttons 
			// display YOUR turn
		// else: 
			// disable buttons
			// display PARTNER's turn
			// poll server for partner taking a turn (external function)
		// After a move: make sure to display who just made a decision & reward (then hide reward)
			// another display_state update from polling server if partner's turn, else from choose_arm()

		$('#game').text(game);
		if (trial > 15) {
			trial = 15
		} 
		$('#trial').text(trial);
		$('#reward').text(reward);
		$('#score').text(score);

		if (reward == 1) {
			$('#reward').css('color', '#2c7bb6');
			$('#score').text(score);
			$('#reward').fadeOut(50);
			$('#score').fadeOut(50);
			$('#reward').fadeIn(25);
			$('#score').fadeIn(25);
		} else if (reward == 0) {
			$('#reward').css('color', '#d7191c');				
			$('#reward').fadeOut(50);
			$('#reward').fadeIn(25);
		} else {
			$('#reward').text('0 or 1');
			$('#reward').css('color', 'black');
		}

		if (nextGameBtnBool) { 
			$('#nextbutton_wrapper').append('<button id="nextbutton">Go to next game</button>');
		} else {
			$('#nextbutton_wrapper').html('');
		};

		if (completionCodeBool) {
			$.getJSON($SCRIPT_ROOT + '/_completion_code', {
				uid: uid
			}, function(data_hidden) {
				if ($("#gameover").length == 0) {
					code = data_hidden.code
					$('body').append('<div><span id="gameover">Gameover!</span> Completion code: ' + code + '</div>');
				}
			});
		};

		for (i = 0; i < scores.length; i++) {
			tdnum = i + 1
			$('#td-game-' + tdnum).text(scores[i]);
		}

	};

	var choose_arm = function(id, uid) {
		var game = parseInt($('#game').html());
		var trial = parseInt($('#trial').html());
		$.getJSON($SCRIPT_ROOT + '/_choose_arm', {
			k: id
		}, function(data) {
			if ($("#gameover").length != 0 || $('#nextbutton').length != 0) {
				return;
			}
			display_state(data.uid, data.score, data.reward, data.game, data.trial, data.next_game_button, data.completion_code, data.scores)
			return false;
		});
		return false;
	};

	if (typeof vars !== 'undefined') {
		display_state(vars.uid, vars.score, vars.reward, vars.game, vars.trial, vars.next_game_button, vars.completion_code, vars.scores)
		if (vars.next_game_button != true) {
			$('.choice').click(function(){ choose_arm(this.id, vars.uid) });
		} 
	}

	var next_game = function() {
		$.getJSON($SCRIPT_ROOT + '/_next_game', {
		}, function(data) {
			display_state(data.uid, data.score, null, data.game, data.trial, false, false, scores=data.scores)
		});
	}
	$('#nextbutton_wrapper').on('click', '#nextbutton', function(){
    	next_game();
	});
});