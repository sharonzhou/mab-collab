$(function() {
	console.log('play_double.js', vars)

	// Construct points table
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

	// Polls server to check if partner moved
	// TODO: check if partner dropped out (the last room activity time > 2min), then give modified completion code
	var ping_server = function(uid, room_id) {
		$.getJSON($SCRIPT_ROOT + '/_check_partner_move', {
			uid: uid,
			room_id: room_id
		}, function(data) {
			if (data.partner_moved == true) {
				console.log('ping server')
				display_state(data.uid, data.score, data.reward, data.game, data.trial, data.next_game_bool, data.completion_code, data.scores, data.next_turn_uid, data.room_id, data.chosen_arm);
			} else {
				// Continue polling
				setTimeout(ping_server, 1000);
			}
		});   
	}

	var display_state = function(uid, score, reward, game, trial, nextGameBool, completionCodeBool, scores=[], next_turn_uid, room_id, chosen_arm) {
		console.log('display_state', reward, next_turn_uid)
		$('#turn_uid').css('visibility', 'visible');
		if (trial == 1) {
			$('#partner_observed_wrapper').css('visibility', 'visible');
			$('#partner_observed_wrapper').css('visibility', 'visible');			
		}

		// Your turn
		if (next_turn_uid == uid) {
			console.log('its my turn')
			// Enable buttons; display your turn, partner's past turn arm & reward #TODO: partial observability
			$('.choice').prop("disabled", false);
			$('.choice').removeClass("disabled");
			$('.choice').one('click', function(){ choose_arm(this.id) });
			// $('.choice').click(function(){ choose_arm(this.id) });
			$('#turn_uid').text('You');
			$('#past_turn_uid').text('Your partner');
			// TODO: for partial observability - and toggle the divs
			if (reward != null) {
				$('#reward_observed').css('visibility', 'visible');
				$('#reward').text(reward.toString());
			}
		// Partner's turn
		} else {
			console.log('its my partners turn')
			// Disable buttons; display partner's turn, your past turn arm & reward #TODO: partial observability
			$('.choice').prop("disabled", true);			
			$('.choice').addClass("disabled");
			$('#turn_uid').text('Partner');
			$('#past_turn_uid').text('You');
			// TODO: for partial observability - and toggle the divs
			if (reward != null) {
				$('#reward_observed').css('visibility', 'visible');
				$('#reward').text(reward.toString());
			}
		}

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
		} else if (reward == 0) {
			$('#reward').css('color', '#d7191c');
		} else {
			$('#reward').text('0 or 1');
			$('#reward').css('color', 'black');
		}

		if (nextGameBool) { 
			$('#next_game_notification').text('BEGIN NEW GAME');
			for (i = 0; i < 2; i++) {
				$('#next_game_notification').fadeOut(75);
				$('#next_game_notification').fadeIn(50);
			}
		} else {
			$('#next_game_notification').text('');
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

	var choose_arm = function(id) {
		// Disable choices immediately to prevent cascading click effects
		$('.choice').prop("disabled", true);			
		$('.choice').addClass("disabled");
		$.getJSON($SCRIPT_ROOT + '/_choose_arm', {
			k: id
		}, function(data) {
			if ($("#gameover").length != 0) {
				return;
			} else {				
				console.log('choose arm');

				display_state(data.uid, data.score, data.reward, data.game, data.trial, data.next_game_bool, data.completion_code, data.scores, data.next_turn_uid, data.room_id, data.chosen_arm);

				// Poll server for partner completing turn
				ping_server(data.uid, data.room_id);
			}
		});
	};

	if (typeof vars !== 'undefined') {
		console.log('regular vars');
		display_state(vars.uid, vars.score, vars.reward, vars.game, vars.trial, vars.next_game_bool, vars.completion_code, vars.scores, vars.next_turn_uid, vars.room_id, vars.chosen_arm);
		
		// Poll server for partner completing turn
		if (vars.next_turn_uid != vars.uid) {
			ping_server(vars.uid, vars.room_id);
		}
	}

});