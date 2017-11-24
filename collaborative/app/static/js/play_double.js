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
			console.log('did partner move?', data.next_turn_uid, data.uid)
			if (data.next_turn_uid != data.uid) {
				console.log('nope still waiting')
				display_disabled_state(data.reward)
				display_common_state(data.trial, data.game, data.score, data.chosen_arm, data.reward, data.completion_code, data.scores);
			} else {
				console.log('should clear interval....')
				window.clearInterval(ping);
				display_state(data.uid, data.score, data.reward, data.game, data.trial, data.next_game_bool, data.completion_code, data.scores, data.next_turn_uid, data.room_id, data.chosen_arm);
			}
		});   
	}

	var display_enabled_state = function(reward) {
		// Enable buttons; display your turn, partner's past turn arm & reward #TODO: partial observability
		$('.choice').prop("disabled", false);
		$('.choice').removeClass("disabled");
		$('.choice').one('click', function(){ $(this).prop("disabled", true); choose_arm(this.id) });
		$('#turn_uid').text('You');
		$('#past_turn_uid').text('Your partner');
		// TODO: for partial observability - and toggle the divs
		if (reward != null) {
			$('#reward_observed').css('visibility', 'visible');
		}
	};

	var display_disabled_state = function(reward) {
		// Disable buttons; display partner's turn, your past turn arm & reward #TODO: partial observability
		$('.choice').prop("disabled", true);			
		$('.choice').addClass("disabled");
		$('#turn_uid').text('Your partner');
		$('#past_turn_uid').text('You');
		// TODO: for partial observability - and toggle the divs
		if (reward != null) {
			$('#reward_observed').css('visibility', 'visible');
		}	
	};

	var display_common_state = function(trial, game, score, chosen_arm, reward, completion_code, scores) {
		$('#game').text(game);
		if (trial > 15) {
			trial = 15
		} 
		$('#trial').text(trial);
		$('#score').text(score);
		$('#chosen_arm').text(chosen_arm);

		if (reward == 1) {
			$('#reward').text(reward);
			$('#reward').css('color', '#2c7bb6');
		} else if (reward == 0) {
			$('#reward').text(reward);
			$('#reward').css('color', '#d7191c');
		} else {
			$('#reward').text('0 or 1');
			$('#reward').css('color', 'black');
		}

		if (trial == 1 && game != 1) {
			$('#new_game_text').css('visibility', 'visible');
			$('#reward_observed').css('visibility', 'hidden');
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

	var display_state = function(uid, score, reward, game, trial, next_game_bool, completion_code, scores=[], next_turn_uid, room_id, chosen_arm) {
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

		display_common_state(trial, game, score, chosen_arm, reward, completion_code, scores);

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

					display_state(data.uid, data.score, data.reward, data.game, data.trial, data.next_game_bool, data.completion_code, data.scores, data.next_turn_uid, data.room_id, data.chosen_arm);

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
		display_state(vars.uid, vars.score, vars.reward, vars.game, vars.trial, vars.next_game_bool, vars.completion_code, vars.scores, vars.next_turn_uid, vars.room_id, vars.chosen_arm);
		
		// Poll server for partner completing turn
		if (vars.next_turn_uid != vars.uid) {
			console.log('ping', ping)
			ping = setInterval(function() {ping_server(vars.uid, vars.room_id)}, 1000);
		}
	}

});