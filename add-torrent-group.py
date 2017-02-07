import requests
import transmissionrpc
import secret
import base64
import time


transmission = transmissionrpc.Client()

#set up requests session, log in to gazelle
requestsSession = requests.Session()
requestsSession.post(secret.baseurl+'login.php', data = {'username':secret.username, 'password':secret.password})


torrentGroupID = input("Input torrent group id: ")

#set up json object of torrent group (album) data
groupJSON = requestsSession.get(secret.baseurl+'ajax.php', params = {'action':'torrentgroup','id':torrentGroupID}).json()

#wait 5 seconds between getting json and requesting torrent downloads
time.sleep(5)

#loop through torrents array to get each torrent id and use it to get a torrent file
for torrent in groupJSON['response']['torrents']:
    print("found torrent id "+str(torrent['id'])+", attempting download")
    try:
        transmission.add_torrent(base64.b64encode(requests.get(secret.baseurl+'torrents.php', params = {'action':'download','id':torrent['id'],'authkey':secret.authkey,'torrent_pass':secret.passkey}).content).decode(), download_dir = secret.directory)
    except transmissionrpc.TransmissionError:
        print("torrent "+str(torrent['id'])+" failed, continuing")
    #wait 5 seconds before looping
    time.sleep(5)
