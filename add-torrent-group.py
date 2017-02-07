import requests
import transmissionrpc
import secret
import base64
import time


transmission = transmissionrpc.Client()

#set up requests session, log in to gazelle
requestsSession = requests.Session()
requestsSession.post(secret.baseurl+'login.php', data = {'username':secret.username, 'password':secret.password})

#avoid spamming the server
time.sleep(2)

#get user data json object, for passkey and authkey
userdata = requestsSession.get(secret.baseurl+'ajax.php', params = {'action':'index'}).json()
authkey = userdata['response']['authkey']
passkey = userdata['response']['passkey']

#get torrent group (album) id via userinput
torrentGroupID = input("Input torrent group id: ")

#set up json object of torrent group (album) data
groupJSON = requestsSession.get(secret.baseurl+'ajax.php', params = {'action':'torrentgroup','id':torrentGroupID}).json()

#wait 2 seconds between getting json and requesting torrent downloads
time.sleep(2)

#loop through torrents array to get each torrent id and use it to get a torrent file
###!!!!USES secret.directory TO DETERMINE WHERE TORRENTS GET PLACED!!!!###
for torrent in groupJSON['response']['torrents']:
    #create infostring to present to user
    torrentInfoString = "id "+str(torrent['id'])+", "+str(torrent['media'])+" rip in "+str(torrent['format'])+", encoding "+str(torrent['encoding'])

    print("found torrent "+torrentInfoString+", attempting to add to transmission...")
    
    #check if a torrent is marked as freeleech (as this is the purpose of the script)
    freetorrent = torrent['freeTorrent']
    if not freetorrent:
        print("WARNING! Torrent id "+str(torrent['id'])+" NOT marked as freeleech! (It could be marked neutral-leech) Do you wish to continue downloading?")
        validInput = False
        while not validInput:
            choice = input()
            if choice.lower() == "y" or choice.lower() == "yes" or choice.lower() == "n" or choice.lower() == "no":
                validInput = True
            else:
                print("Invalid input, try again")
        if choice.lower() == "n" or choice.lower() == "no":
            continue

    ##adding torrent can throw errors
    try:
        #adding torrent via add_torrent(url) wasn't working, i suspect because the tracker didn't like the request from the python library add_torrent uses to get from web
        #so it uses requests (outside of the session), however the returned content wasn't working
        #SO we encode it to base64 and then decode it
        transmission.add_torrent(base64.b64encode(requests.get(secret.baseurl+'torrents.php', params = {'action':'download','id':torrent['id'],'authkey':authkey,'torrent_pass':passkey}).content).decode(), download_dir = secret.directory)
    except transmissionrpc.TransmissionError:
        print("torrent "+str(torrent['id'])+" failed (script threw transmission error, this can happen if you have downloaded that torrent too many times), continuing...")
    #wait 5 seconds before looping
    time.sleep(5)
