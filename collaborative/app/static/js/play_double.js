google.charts.load("current", {packages:['corechart']});
google.charts.setOnLoadCallback(drawSingleGame);
function drawSingleGame() {
	if (typeof vars !== 'undefined') {
		num_trials = vars.num_trials;
		num_games = vars.num_games;
		// Charts interface
		var charts_data = [];
		var charts_options = {
			title: "Ratio: —",
			titleTextStyle: { fontSize: 14 },
			width: 250,
			height: 300,
			bar: { groupWidth: "95%" },
			legend: { position: "none" },
			vAxis: { viewWindow: { min: 0, max: num_trials } }
		};

		var reset_chart = function() {
			charts_data = [];
			charts_options = {
				title: "Ratio: —",
				titleTextStyle: { fontSize: 14 },
				width: 250,
				height: 300,
				bar: { groupWidth: "95%" },
				legend: { position: "none" },
				vAxis: { viewWindow: { min: 0, max: num_trials } }
			};
			for (i=0; i<4; i++) {
				var data = new google.visualization.DataTable();
				data.addColumn("string", "1 or 0 Points");
				data.addColumn("number", "Number of times");
				data.addColumn({ type: "string", role: "style" });
				data.addRow(["Gave 1 point", 0, "color: #2c7bb6"]);
				data.addRow(["Gave 0 points", 0, "color: #d7191c"]);
				data.addRow(["Hidden", 0, "color: #d3d3d3"]);

				charts_data.push(data);
				var chart = new google.visualization.ColumnChart(document.getElementById("chart_" + String(i + 1)));
				chart.draw(data, charts_options);
			};
		};
		reset_chart();

		var update_chart = function(k, row) {
			var onePointCount = charts_data[k].getValue(0, 1);
			var zeroPointCount = charts_data[k].getValue(1, 1);
			var hiddenPointCount = charts_data[k].getValue(2, 1);
			if (row == 0) {
				charts_data[k].setValue(row, 1, onePointCount + 1);
				onePointCount += 1;
			} else if (row == 1) {
				charts_data[k].setValue(row, 1, zeroPointCount + 1);
				zeroPointCount += 1;
			} else {
				charts_data[k].setValue(row, 1, hiddenPointCount + 1);
				hiddenPointCount += 1;
			}
			options = $.extend({}, charts_options);
			if (parseFloat(onePointCount + zeroPointCount) > 0) {
				ratio = (onePointCount / parseFloat(onePointCount + zeroPointCount)).toFixed(2);
				options["title"] = "Ratio: " + ratio;
			}

			var chart = new google.visualization.ColumnChart(document.getElementById("chart_" + String(k + 1)));
			chart.draw(charts_data[k], options);
		};

		// Remaining interface
		console.log('play_double.js', vars);

		// Construct points table
		var table = '<table align="center"><tr>';
		for (var i=0; i<num_games; i++) {
			table += '<th>' + String(i + 1) + '</th>';
		}
		table += '</tr><tr>';
		for (var i=0; i<num_games; i++) {
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
				// Partner dropped out of game
				} else if (data.timeout == true) {
					console.log('partner dropped out')
					// Refresh
					$(location).attr('href', $SCRIPT_ROOT);
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

		var display_common_state = function(trial, game, score, chosen_arm, reward, completion_code, scores, is_observable, partner_is_observable, experimental_condition, next_turn_uid, uid) {	
			if (trial == 1) {
				// Hide stuff
				$('.turn_information').css('visibility', 'hidden');	
			} else {
				$('.turn_information').css('visibility', 'visible');
				if (reward != null || is_observable != null || partner_is_observable != null) {
					if (is_observable == true) {
						if (reward == 1) {
							if ($('#trial').text() != trial && completion_code != true && trial <= num_trials) {
								update_chart(chosen_arm - 1, 0);
							};
							$('#reward').text(reward);
							$('#reward').css('color', 'black');
						} else if (reward == 0) {
							if ($('#trial').text() != trial && completion_code != true && trial <= num_trials) {
								update_chart(chosen_arm - 1, 1);
							};
							$('#reward').text(reward);
							$('#reward').css('color', 'black');
						} 
					} else {
						if ($('#trial').text() != trial && completion_code != true && trial <= num_trials) {
							update_chart(chosen_arm - 1, 2);
						};
						$('#reward').text('hidden');
						$('#reward').css('color', '#d3d3d3');
					}

					if (experimental_condition != 'control') {
						if (partner_is_observable == true) {
							$('#partner_observation').html('<span id="partner_is_observable_style">seen</span> by your partner');
						} else {
							$('#partner_observation').html('<span id="partner_is_observable_style">hidden</span> from your partner');
						}
					}
				} else {
					$('#reward_unobserved').css('visibility', 'hidden');
					$('#reward_observed').css('visibility', 'hidden');
					$('#partner_observed').css('visibility', 'hidden');
					$('#partner_unobserved').css('visibility', 'hidden');
				}	
			}

			// Trials should not increment over the max
			if (trial > num_trials) {
				trial = num_trials;
			}
			$('#trial').text(trial);

			$('#game').text(game);
			$('#score').text(score);

			$('#coin_img').html('<img id="attached_coin_img" src="../static/img/coin_' + game + '.png" height="20">');

			// Highlight chosen arm with appropriate button color
			$('#chosen_arm').text(chosen_arm);
			var color;
			if (chosen_arm == 1) {
				color = '#d7191c';
			} else if (chosen_arm == 2) {
				color = '#fdae61';
			} else if (chosen_arm == 3) {
				color = '#abd9e9';
			} else if (chosen_arm == 4) {
				color = '#2c7bb6';
			}
			if (color != null) {
				$('#chosen_arm_highlight').css('background-color', color);
				$('#chosen_arm_highlight').css('color', 'white');
			} else {
				$('#chosen_arm_highlight').css('background-color', 'none');
				$('#chosen_arm_highlight').css('color', 'black');
			}

			// Show completion code
			if (completion_code != null && completion_code != false && !$('#gameover').length) {
				$('.choice').prop("disabled", true);			
				$('.choice').addClass("disabled");
				$('body').append('<div><span id="gameover">Gameover!</span> Completion code: ' + completion_code + '</div>');
			};

			// Display scores on past games
			if (scores != null) {
				for (i = 0; i < scores.length; i++) {
					tdnum = i + 1
					$('#td-game-' + tdnum).text(scores[i]);
				}
			}

			// Experimental condition toggle
			if (experimental_condition == 'control') {
				$('#experimental_condition_text').hide();
				$('#partner_observation_wrapper').hide();
				$('#score_subtext').hide();
				$('#overlay_observability').hide();
			} else if ($('#experimental_condition_text').text() == '') {
				var experimental_condition_text = '</br><div><b>Note:</b> ';
				if (experimental_condition == 'partial') {
					if (next_turn_uid == uid) {
						experimental_condition_text += 'You can see <b>all</b> points given. Your partner can see about <b>1/3</b> of the points.'
					} else {
						experimental_condition_text += 'You can see about <b>1/3</b> of the points given. Your partner can see <b>all</b> points.'
					}
				} else if (experimental_condition == 'partial_asymmetric') {
					if (next_turn_uid == uid) {
						experimental_condition_text += 'You can see about <b>2/3</b> of the points given. Your partner can see about <b>1/3</b> of the points.'
					} else {
						experimental_condition_text += 'You can see about <b>1/3</b> of the points given. Your partner can see about <b>2/3</b> of the points.'
					}
				}					
				experimental_condition_text += '</div>';
				$('#experimental_condition_text').append(experimental_condition_text);
				$('#experimental_condition_text').show();
			}	
		}

		var display_state = function(uid, score, reward, game, trial, next_game_bool, completion_code, scores, next_turn_uid, room_id, chosen_arm, is_observable, partner_is_observable, experimental_condition) {
			console.log('display_state: scores are', scores, '// score for me is', score, '// can i see?', is_observable, '// can my partner see?', partner_is_observable)
			$('#turn_uid').css('visibility', 'visible');

			// Your turn or time for next game
			if (next_turn_uid == uid || next_game_bool == true) {
				display_enabled_state(reward);
			// Partner's turn
			} else {
				display_disabled_state(reward);
			}

			display_common_state(trial, game, score, chosen_arm, reward, completion_code, scores, is_observable, partner_is_observable, experimental_condition, next_turn_uid, uid);

			// End of game screen
			if (next_game_bool == true) {
				// Show overlay
				$('#overlay_gameover').width('100%');
				$('#overlay_game').text(game);
				reset_chart();
				$('#coin_img').html('<img id="attached_coin_img" src="../static/img/coin_' + $('#game').text() + '.png" height="20">');
				if ($('#overlay_score').text() == '' && trial >= num_trials) {
					$.getJSON($SCRIPT_ROOT + '/_get_true_score', {
						uid: uid
					}, function(data) {
						console.log('TRUE SCORE',data.true_score, data);
						$('#overlay_score').text(data.true_score);
					});
				}
				if (!$('#nextbutton').length) {
					$('#nextbutton_wrapper').append('<button id="nextbutton">Ready for next game</button>');
				}
			}
		};

		var advance_next_game = function() {
			$('#overlay_score').text('');
			$('#overlay_gameover').width('0%');
			$('#nextbutton_wrapper').html('');
			$.getJSON($SCRIPT_ROOT + '/_advance_next_game', {
			}, function(data) {
				$('#coin_img').html('<img id="attached_coin_img" src="../static/img/coin_' + $('#game').text() + '.png" height="20">');
				display_state(data.uid, data.score, data.reward, data.game, data.trial, data.next_game_bool, data.completion_code, data.scores, data.next_turn_uid, data.room_id, data.chosen_arm, data.is_observable, data.partner_is_observable, data.experimental_condition);
			});
		}
		$('#nextbutton_wrapper').on('click', '#nextbutton', function(){
	    	advance_next_game();
		});

		var processing = false;
		var choose_arm = function(id) {
			if (processing == false) {
				processing = true;
				$.getJSON($SCRIPT_ROOT + '/_choose_arm', {
					k: id
				}, function(data) {
					if ($("#gameover").length != 0) {
						return;
					} else {				
						display_state(data.uid, data.score, data.reward, data.game, data.trial, data.next_game_bool, data.completion_code, data.scores, data.next_turn_uid, data.room_id, data.chosen_arm, data.is_observable, data.partner_is_observable, data.experimental_condition);

						if (data.next_turn_uid != data.uid) {
							// Poll server for partner completing turn
							ping = setInterval(function() {ping_server(data.uid, data.room_id)}, 1000);
						}
						processing = false;
					}
				});
			}
		};

		display_state(vars.uid, vars.score, vars.reward, vars.game, vars.trial, vars.next_game_bool, vars.completion_code, vars.scores, vars.next_turn_uid, vars.room_id, vars.chosen_arm, vars.is_observable, vars.partner_is_observable, vars.experimental_condition);
		
		// Poll server for partner completing turn
		if (vars.next_turn_uid != vars.uid) {
			ping = setInterval(function() {ping_server(vars.uid, vars.room_id)}, 1000);
		}

		if (vars.completion_code != null) {
			clearInterval(ping_server);
		}
	};
};