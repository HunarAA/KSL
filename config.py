from streamlit_webrtc import ClientSettings

CLASSES = [
    'Ruberru',
    'Choni',
    'Leberdem',
    'Xoshewisti',
    'Cheshtxane',
    'zherpyalle',
    'Xorragir',
    'Sistem',
    'Tebayi',
    'Rengekan']
# CLASSES = [
#     'ڕوبەڕوو',
#     'چۆنی',
#     'لەبەردەم',
#     'خۆشەویستی',
#     'چێشتخانە',
#     'ژێرپیاڵە',
#     'خۆڕاگر',
#     'سیستەم',
#     'تەبایی',
#     'ڕەنگەکان']


WEBRTC_CLIENT_SETTINGS = ClientSettings(
        rtc_configuration={"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]},
        media_stream_constraints={"video": True, "audio": False},
    )