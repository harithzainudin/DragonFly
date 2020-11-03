import requests

class Anafi_Request_Post():

    def requestPost(self, idData, location):
        API_ENDPOINT = "http://pastebin.com/api/api_post.php"
        API_KEY = "http://cpsdragonfly.herokuapp.com/"
        source_code = {"id": idData, "location": location }

        data = {'api_dev_key':API_KEY, 'api_option':'paste', 'api_paste_code':source_code, 'api_paste_format':'python'} 

        resp = requests.post(url = API_ENDPOINT, data = data)