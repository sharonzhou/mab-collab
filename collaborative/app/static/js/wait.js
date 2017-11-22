$(function() {
	console.log('wait.js', vars)

	// Notify user that we've matched them and we're ready to begin
	var last_active = 0;
	var notify_user = function() {
		if ($('body').hasClass('hidden')) {
			document.title = document.title == 'Starting game...' ? 'Waiting room' : 'Starting game...'
			setTimeout(notify_user, 500);
		} else if ($('body').hasClass('visible')) {
			// Redirect
			$(location).attr('href', $SCRIPT_ROOT);
		}
	}

	// Poll/ping server ever 1 sec (wait) to match a parter
	var ping_server = function() {
		$.getJSON($SCRIPT_ROOT + '/_waiting_ping', {
			uid: vars.uid
		}, function(data) {
			if (data.room_id != 0) {
				console.log('Matched room_id is ', data.room_id)
				$('#loading_gif').hide()
				$('#waiting_text').html('We found a partner for you!');
				document.title = 'Starting game...';
				last_active = Date.now();
				// Flash notification on document title until window is active
				notify_user();
			} else {
				setTimeout(ping_server, 1000);
			}
		});
	    
	}
	ping_server();

	// Display timer
	var elapsed_seconds = 0;
	setInterval(function() {
		elapsed_seconds = elapsed_seconds + 1;
		$('#timer').text((Math.floor(elapsed_seconds / 60)).toString() + 'min ' + (elapsed_seconds % 60).toString() + 's');
	}, 1000);

	// If 20 min of waiting, give adapted completion code (we'll just pay them for waiting)
	var start_wait = Date.now();
	if (Math.floor((new Date() - start_wait) / 60000) > 20) {
		$.getJSON($SCRIPT_ROOT + '/_waiting_completion_code', {
			uid: vars.uid
		}, function(data_hidden) {
			code = data_hidden.code
			$('body').append('<div><span id="gameover">Sorry to make you wait so long. No need to continue. Please submit the waiting completion code:</span> ' + code + '</div>');
		});
	}

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