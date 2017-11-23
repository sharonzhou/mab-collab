$(function() {
	console.log('play_single.js', vars)

	var display_state = function(uid, score, reward, game, trial, nextGameBtnBool) {
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
			$('#nextbutton_wrapper').append('<button id="nextbutton">Ready to play with a partner</button>');
		} else {
			$('#nextbutton_wrapper').html('');
		};

	};

	var choose_arm = function(id, uid) {
		$.getJSON($SCRIPT_ROOT + '/_choose_arm', {
			k: id
		}, function(data) {
			if ($('#nextbutton').length != 0) {
				return;
			}
			display_state(data.uid, data.score, data.reward, data.game, data.trial, data.next_game_bool)
			return false;
		});
		return false;
	};

	if (typeof vars !== 'undefined') {
		display_state(vars.uid, vars.score, vars.reward, vars.game, vars.trial, vars.next_game_bool)
		if (vars.next_game_bool != true) {
			$('.choice').click(function(){ choose_arm(this.id, vars.uid) });
		} 
	}

	var play_double = function() {
		$.getJSON($SCRIPT_ROOT + '/_enter_waiting', {
		}, function(data) {
			$(location).attr('href', $SCRIPT_ROOT);
		});
	}
	$('#nextbutton_wrapper').on('click', '#nextbutton', function(){
    	play_double();
	});
});