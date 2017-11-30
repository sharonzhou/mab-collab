$(function() {
	console.log('wait.js', vars)

	// Notify user that we've matched them and we're ready to begin
	var last_active = 0;
	var notify_user = function(experimental_condition) {
		if ($('body').hasClass('hidden')) {
			document.title = document.title == 'Starting game...' ? 'Waiting room' : 'Starting game...'
			setTimeout(notify_user, 500);
		} else if ($('body').hasClass('visible')) {
			// Redirect after 5s
			setTimeout(function() { 
				$(location).attr('href', $SCRIPT_ROOT);
			}, 5000);	
		}		
	}

	// Ping/poll server ever 1 sec (wait) to match a parter
	var ping_server = function() {
		$.getJSON($SCRIPT_ROOT + '/_waiting_ping', {
			uid: vars.uid
		}, function(data) {
			if (data.room_id != 0) {
				console.log('Matched room_id is ', data.room_id)

				clearInterval(elapse_timer);
				last_active = Date.now();
				document.title = 'Starting game...';
				$('#loading_gif').hide();

				$('#waiting_text').html('We found a partner for you! Loading your first game (in 5 seconds)...');
				$('#waiting_text').css('font-weight', 'bold');
				$('#waiting_text').css('color', 'darkblue');

				// Display experimental condition
				if (data.experimental_condition == 'control') {
					$('#experimental_condition_text').hide();
				} else if ($('#experimental_condition_text').text() == '') {
					var experimental_condition_text = '</br><div><b>Note:</b> ';
					if (data.experimental_condition == 'partial') {
						if (data.next_turn_uid == data.uid) {
							experimental_condition_text += 'You can see <b>all</b> points given. Your partner can see about <b>1/3</b> of the points.'
						} else {
							experimental_condition_text += 'You can see about <b>1/3</b> of the points given. Your partner can see <b>all</b> points.'
						}
					} else if (data.experimental_condition == 'partial_asymmetric') {
						if (data.next_turn_uid == data.uid) {
							experimental_condition_text += 'You can see about <b>2/3</b> of the points given. Your partner can see about <b>1/3</b> of the points.'
						} else {
							experimental_condition_text += 'You can see about <b>1/3</b> of the points given. Your partner can see about <b>2/3</b> of the points.'
						}
					}					
					experimental_condition_text += '</div>';
					$('#experimental_condition_text').append(experimental_condition_text);
				}

				// Flash notification on document title until window is active
				notify_user(data.experimental_condition);
			} else {
				setTimeout(ping_server, 1000);
			}
		});
	    
	}
	ping_server();

	// Display timer - make sure to change waiting room instructions if you change this value
	var MAX_WAIT_MIN = 10
	var elapsed_seconds = 0;
	var elapse_timer = setInterval(function() {
		if ($('#waiting_completion_code').length) {
			clearInterval(elapse_timer);
		} else {
			elapsed_seconds = elapsed_seconds + 1;
			if (elapsed_seconds <= MAX_WAIT_MIN * 60) {
				$('#timer').text((Math.floor(elapsed_seconds / 60)).toString() + 'min ' + (elapsed_seconds % 60).toString() + 's');
			}

			// If MAX_WAIT_MIN min of waiting, give adapted completion code (we'll just pay them for waiting)
			if (elapsed_seconds > MAX_WAIT_MIN * 60) {
				$.getJSON($SCRIPT_ROOT + '/_waiting_completion_code', {
					uid: vars.uid
				}, function(data_hidden) {
					code = data_hidden.waiting_code
					$('body').append('</br><div id="waiting_completion_code">Sorry to make you wait so long. No need to continue. Please submit the waiting completion code: <b>' + code + '</b></div>');
				});
			}
		}
	}, 1000);


	// Detect if tab/window is visible (cf. stackoverflow)
	(function() {
		var hidden = "hidden";

		// Standards:
		if (hidden in document)
			document.addEventListener("visibilitychange", onchange);
		else if ((hidden = "mozHidden") in document)
			document.addEventListener("mozvisibilitychange", onchange);
		else if ((hidden = "webkitHidden") in document)
			document.addEventListener("webkitvisibilitychange", onchange);
		else if ((hidden = "msHidden") in document)
			document.addEventListener("msvisibilitychange", onchange);
		// IE 9 and lower:
		else if ("onfocusin" in document)
			document.onfocusin = document.onfocusout = onchange;
		// All others:
		else
			window.onpageshow = window.onpagehide = window.onfocus = window.onblur = onchange;

		function onchange (evt) {
			var v = "visible", h = "hidden",
		    evtMap = {
		      focus:v, focusin:v, pageshow:v, blur:h, focusout:h, pagehide:h
			};

			evt = evt || window.event;
			if (evt.type in evtMap)
				document.body.className = evtMap[evt.type];
			else
				document.body.className = this[hidden] ? "hidden" : "visible";
		}

		// set the initial state (but only if browser supports the Page Visibility API)
		if (document[hidden] !== undefined)
			onchange({type: document[hidden] ? "blur" : "focus"});
	})();
});