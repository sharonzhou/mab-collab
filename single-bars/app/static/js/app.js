google.charts.load("current", {packages:['corechart']});
google.charts.setOnLoadCallback(drawGame);
function drawGame() {
  if (document.getElementById("chart_1") == null) {
	  var start_game = function(amt_id) {
	    $.getJSON($SCRIPT_ROOT + '/_create_user', {
	      amt_id: amt_id
	    }, function(data) {
	      uid = data.uid
	      $(location).attr('href', $SCRIPT_ROOT + '/play/' + uid)
	    });
	  };
	  $('#start').click(function(){ start_game($('#amt_id').val()) })
  } else {
	  var charts_data = [];
	  var charts_options = {
	      title: "Ratio: —",
	      titleTextStyle: { fontSize: 14 },
	      width: 150,
	      height: 300,
	      bar: { groupWidth: "95%" },
	      legend: { position: "none" },
	      vAxis: { viewWindow: { min: 0, max: 15 } }
	    };
	  for (i=0; i<4; i++) {
	    var data = new google.visualization.DataTable();
	    data.addColumn("string", "1 or 0 Points");
	    data.addColumn("number", "Number of times");
	    data.addColumn({ type: "string", role: "style" });
	    data.addRow(["Gave 1 point", 0, "color: #2c7bb6"]);
	    data.addRow(["Gave 0 points", 0, "color: #d7191c"]);

	    charts_data.push(data);
	    console.log();
	    var chart = new google.visualization.ColumnChart(document.getElementById("chart_" + String(i + 1)));
	    chart.draw(data, charts_options);
	  }

	  var table = '<table id="history"><tr>';
	  for (var i=0; i<20; i++) {
	    table += '<th>' + String(i + 1) + '</th>';
	  }
	  table += '</tr><tr>';
	  for (var i=0; i<20; i++) {
	    table += '<td id="td-game-' + String(i + 1) + '">-</td>';
	  }
	  table += '</tr></table>';
	  $('#table').append(table);

	  var update_chart = function(k, row) {
		var onePointCount = charts_data[k].getValue(0, 1);
		var zeroPointCount = charts_data[k].getValue(1, 1);
		if (row == 0) {
			charts_data[k].setValue(row, 1, onePointCount + 1);
		} else {
			charts_data[k].setValue(row, 1, zeroPointCount + 1);
		}
		ratio = (onePointCount / parseFloat(onePointCount + zeroPointCount)).toFixed(2)
	  	options = $.extend({}, charts_options);
	  	options["title"] = "Ratio: " + ratio

		var chart = new google.visualization.ColumnChart(document.getElementById("chart_" + String(k + 1)));
		chart.draw(charts_data[k], options);
	  };

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

	      var reward = data.reward;
	      var k = data.k;
	      $('#reward').text(reward);
	      if (reward == 1) {
	    	update_chart(k, 0);
	        $('#reward').css('color', '#2c7bb6');
	        $('#score').text(parseInt($('#score').html()) + 1);
	        $('#reward').fadeOut(50);
	        $('#score').fadeOut(50);
	        $('#reward').fadeIn(25);
	        $('#score').fadeIn(25);
	      } else {
	    	update_chart(k, 1);
	        $('#reward').css('color', '#d7191c');       
	        $('#reward').fadeOut(50);
	        $('#reward').fadeIn(25);
	      }

	      var nextTrial = parseInt($('#trial').html()) + 1;
	      if (nextTrial > 15) {
	        score = $('#score').html();
	        game = $('#game').html();
	        $('#td-game-' + game).text(score);
	        var nextGame = parseInt(game) + 1;
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
	          $('#nextbutton').fadeOut(50);
	          $('#nextbutton').fadeIn(25);          
	        }
	      } else {
	        $('#trial').text(nextTrial);
	      }

	    });
	    return false;
	  };
	  $('button').click(function(){ choose_arm(this.id, window.location.pathname.split('/').pop()) });

	  var next_game = function() {
	    $('#nextbutton_wrapper').html('')
	    $('#score').text('0');
	    $('#reward').text('0 or 1');
	    $('#reward').css('color', 'black');
	    var nextGame = parseInt($('#game').html()) + 1;
	    $('#game').text(nextGame);
	    $('#trial').text('1');
	    for (k=0; k<4; k++) {
	      	charts_data[k].setValue(0, 1, 0);
	      	charts_data[k].setValue(1, 1, 0);
	    	var chart = new google.visualization.ColumnChart(document.getElementById("chart_" + String(k + 1)));
	    	chart.draw(charts_data[k], charts_options);
	    }
	  }
	  $('#nextbutton_wrapper').on('click', '#nextbutton', function(){
	      next_game();
	  });
	}
};