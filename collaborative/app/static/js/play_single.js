google.charts.load("current", {packages:['corechart']});
google.charts.setOnLoadCallback(drawSingleGame);
function drawSingleGame() {
	if (typeof vars !== 'undefined') {
		num_trials = vars.num_trials;
		// Charts interface
		var charts_data = [];
		var charts_options = {
			title: "Ratio: —",
			titleTextStyle: { fontSize: 14 },
			width: 150,
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

			charts_data.push(data);
			var chart = new google.visualization.ColumnChart(document.getElementById("chart_" + String(i + 1)));
			chart.draw(data, charts_options);
		};

		var update_chart = function(k, row) {
			var onePointCount = charts_data[k].getValue(0, 1);
			var zeroPointCount = charts_data[k].getValue(1, 1);
			if (row == 0) {
				charts_data[k].setValue(row, 1, onePointCount + 1);
				onePointCount += 1;
			} else {
				charts_data[k].setValue(row, 1, zeroPointCount + 1);
				zeroPointCount += 1;
			}
			ratio = (onePointCount / parseFloat(onePointCount + zeroPointCount)).toFixed(2)
				options = $.extend({}, charts_options);
				options["title"] = "Ratio: " + ratio

			var chart = new google.visualization.ColumnChart(document.getElementById("chart_" + String(k + 1)));
			chart.draw(charts_data[k], options);
		};

		// Remaining interface
		console.log('play_single.js', vars)

		var display_state = function(uid, score, reward, game, trial, nextGameBtnBool, chosenArm) {
			$('#game').text(game);
			if (trial > num_trials) {
				trial = num_trials
			} 
			$('#trial').text(trial);
			$('#reward').text(reward);
			$('#score').text(score);

			if (reward == 1) {
				update_chart(chosenArm - 1, 0);
				$('#reward').css('color', '#2c7bb6');
				$('#score').text(score);
				$('#reward').fadeOut(50);
				$('#score').fadeOut(50);
				$('#reward').fadeIn(25);
				$('#score').fadeIn(25);
			} else if (reward == 0) {
				update_chart(chosenArm - 1, 1);
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
			$.getJSON($SCRIPT_ROOT + '/_choose_arm_single', {
				k: id
			}, function(data) {
				if ($('#nextbutton').length != 0) {
					return;
				}
				display_state(data.uid, data.score, data.reward, data.game, data.trial, data.next_game_bool, data.chosen_arm)
				return false;
			});
			return false;
		};

		display_state(vars.uid, vars.score, vars.reward, vars.game, vars.trial, vars.next_game_bool, data.chosen_arm)
		if (vars.next_game_bool != true) {
			$('.choice').click(function(){ choose_arm(this.id, vars.uid) });
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
	};
};