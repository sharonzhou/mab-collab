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
	var ping;
	var ping_server = function(uid, room_id) {
		$.getJSON($SCRIPT_ROOT + '/_check_partner_move', {
			uid: uid,
			room_id: room_id
		}, function(data) {
			// Partner still going
			if (data.next_turn_uid != data.uid) {
				display_disabled_state(data.reward)
				display_common_state(data.trial, data.game, data.score, data.chosen_arm, data.reward, data.completion_code, data.scores, data.is_observable, data.partner_is_observable, data.experimental_condition);
			// Partner dropped out of game
			} else if (data.timeout == true) {
				// Clear partner's session? on server side, send something to room var?
				// TODO
				console.log('partner dropped out')
			// Your turn now
			} else {
				window.clearInterval(ping);
				display_state(data.uid, data.score, data.reward, data.game, data.trial, data.next_game_bool, data.completion_code, data.scores, data.next_turn_uid, data.room_id, data.chosen_arm, data.is_observable, data.partner_is_observable, data.experimental_condition);
			}
		});   
	}

	var display_enabled_state = function(reward) {
		// Enable buttons; display your turn, partner's past turn arm & reward, if observable
		$('.choice').prop("disabled", false);
		$('.choice').removeClass("disabled");
		$('.choice').one('click', function(){ $(this).prop("disabled", true); choose_arm(this.id) });
		$('#turn_uid').text('You');
		$('#past_turn_uid').text('Your partner');
	};

	var display_disabled_state = function(reward) {
		// Disable buttons; display partner's turn, your past turn arm & reward
		$('.choice').prop("disabled", true);			
		$('.choice').addClass("disabled");
		$('#turn_uid').text('Your partner');
		$('#past_turn_uid').text('You');
	};

	var display_common_state = function(trial, game, score, chosen_arm, reward, completion_code, scores, is_observable, partner_is_observable, experimental_condition) {
		$('#game').text(game);
		if (trial > 15) {
			trial = 15
		} 
		$('#trial').text(trial);
		$('#score').text(score);
		$('#chosen_arm').text(chosen_arm);

		console.log('can my partner see?', partner_is_observable, '// can i see?', is_observable)
		if (reward != null || is_observable != null || partner_is_observable != null) {
			if (is_observable == true) {
				if (reward == 1) {
					$('#reward').text(reward);
					$('#reward').css('color', '#2c7bb6');
				} else if (reward == 0) {
					$('#reward').text(reward);
					$('#reward').css('color', '#d7191c');
				} 
			} else {
				$('#reward').text('hidden');
				$('#reward').css('color', '#d3d3d3');
			}

			if (experimental_condition != 'control') {
				if (partner_is_observable == true) {
					$('#partner_observation').text('Your partner sees this.');
				} else {
					$('#partner_observation').text('Hidden from your partner.');
				}
			}

		} else {
			$('#reward_unobserved').css('visibility', 'hidden');
			$('#reward_observed').css('visibility', 'hidden');
			$('#partner_observed').css('visibility', 'hidden');
			$('#partner_unobserved').css('visibility', 'hidden');
		}

		if (trial == 1 && game != 1) {
			$('#new_game_text').css('visibility', 'visible');
		} else {
			$('#new_game_text').css('visibility', 'hidden');
		}

		if (completion_code != null && completion_code != false) {
			$('body').append('<div><span id="gameover">Gameover!</span> Completion code: ' + completion_code + '</div>');
		};

		if (scores != null) {
			for (i = 0; i < scores.length; i++) {
				tdnum = i + 1
				$('#td-game-' + tdnum).text(scores[i]);
			}
		}
	}

	var display_state = function(uid, score, reward, game, trial, next_game_bool, completion_code, scores=[], next_turn_uid, room_id, chosen_arm, is_observable, partner_is_observable, experimental_condition) {
		console.log('display_state', reward, next_turn_uid)
		$('#turn_uid').css('visibility', 'visible');

		// Your turn
		if (next_turn_uid == uid) {
			console.log('it\'s my turn');
			display_enabled_state(reward);
		// Partner's turn
		} else {
			console.log('it\'s my partner\'s turn');
			display_disabled_state(reward);
		}

		display_common_state(trial, game, score, chosen_arm, reward, completion_code, scores, is_observable, partner_is_observable, experimental_condition);

	};

	var processing = false;
	var choose_arm = function(id) {
		console.log('choosing arm');
		if (processing == false) {
			console.log('actually processing')
			processing = true;
			$.getJSON($SCRIPT_ROOT + '/_choose_arm', {
				k: id
			}, function(data) {
				if ($("#gameover").length != 0) {
					return;
				} else {				
					console.log('choose arm');

					display_state(data.uid, data.score, data.reward, data.game, data.trial, data.next_game_bool, data.completion_code, data.scores, data.next_turn_uid, data.room_id, data.chosen_arm, data.is_observable, data.partner_is_observable, data.experimental_condition);

					if (data.next_turn_uid != data.uid) {
						// Poll server for partner completing turn
						console.log('ping', ping)
						ping = setInterval(function() {ping_server(data.uid, data.room_id)}, 1000);
					}
					processing = false;
				}
			});
		}
	};

	if (typeof vars !== 'undefined') {
		console.log('regular vars');
		display_state(vars.uid, vars.score, vars.reward, vars.game, vars.trial, vars.next_game_bool, vars.completion_code, vars.scores, vars.next_turn_uid, vars.room_id, vars.chosen_arm, vars.is_observable, vars.partner_is_observable, vars.experimental_condition);
		
		// Poll server for partner completing turn
		if (vars.next_turn_uid != vars.uid) {
			console.log('ping', ping)
			ping = setInterval(function() {ping_server(vars.uid, vars.room_id)}, 1000);
		}
	}

});