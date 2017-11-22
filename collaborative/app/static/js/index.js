$(function() {
	console.log('index.js')
	var start_game = function(amt_id) {
		$.getJSON($SCRIPT_ROOT + '/_create_user', {
			amt_id: amt_id
		}, function(data) {
			$(location).attr('href', $SCRIPT_ROOT);
		});
	};
	$('#start').click(function(){ start_game($('#amt_id').val()) })
});