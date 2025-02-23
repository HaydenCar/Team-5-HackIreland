extends Node3D

var xr_interface: XRInterface

func _ready():
	# Initialize OpenXR (optional, if you're using VR)
	#xr_interface = XRServer.find_interface("OpenXR")
	#if xr_interface and xr_interface.is_initialized():
		#print("OpenXR initialized successfully")
		#DisplayServer.window_set_vsync_mode(DisplayServer.VSYNC_DISABLED)
		#get_viewport().use_xr = true
	#else:
		#print("OpenXR not initialized, please check your headset connection")
	
	# Open the WebView overlay to display a webpage.
	# Note: Make sure the URL has the protocol, e.g., "https://"
	WebView.open_webview("https://www.example.com")
