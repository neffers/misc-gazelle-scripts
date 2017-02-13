import requests
import transmissionrpc
import secret
import base64
import time
import html

transmission = transmissionrpc.Client()
trackerTorrents = []

#compile array of torrents that use the specified tracker (if specified)
if secret.tracker:
    for torrent in transmission.get_torrents():
        for tracker in torrent.trackers:
            if secret.tracker in tracker['announce']:
                trackerTorrents.append(torrent.name)
else:
    print('Found no tracker specified in secret.py, I cannot reliably tell what torrents have already been added (without significant cpu cost) without it!')
    trackerTorrents = None

#set up requests session, log in to gazelle
requestsSession = requests.Session()
print("Logging in...")
requestsSession.post(secret.baseurl+'login.php', data = {'username':secret.username, 'password':secret.password})

#avoid spamming the server
time.sleep(2)

#get user data json object, for passkey and authkey
userdata = requestsSession.get(secret.baseurl+'ajax.php', params = {'action':'index'}).json()
print("Getting auth and passkeys from server...")
authkey = userdata['response']['authkey']
passkey = userdata['response']['passkey']

time.sleep(2)

#to manage looping through different pages
done = False
page = 1
while not done:

    #use the search api to return the list of freetorrents
    flsearch = requestsSession.get(secret.baseurl+'ajax.php', params = {'action':'browse','freetorrent':1,'page':page}).json()
    print("Search request returned "+flsearch['status']+"on page "+str(page)+' of '+str(flsearch['response']['pages']))

    #go through each group included in results
    for torrentGroup in flsearch['response']['results']:

        #get torrent group (album) id from the torrentgroup
        torrentGroupID = torrentGroup['groupId']
        groupInfoString = html.unescape(torrentGroup['groupName']+" by "+torrentGroup['artist'])
        print("\nFound group ID "+str(torrentGroupID)+", "+groupInfoString)

        #set up json object of torrent group (album) data
        groupJSON = requestsSession.get(secret.baseurl+'ajax.php', params = {'action':'torrentgroup','id':torrentGroupID}).json()

        #wait 2 seconds between getting json and requesting torrent downloads
        time.sleep(2)

        #loop through torrents array to get each torrent id and use it to get a torrent file
        ###!!!!USES secret.directory TO DETERMINE WHERE TORRENTS GET PLACED!!!!###
        for torrent in groupJSON['response']['torrents']:
            #create infostring to present to user
            torrentInfoString = "id "+str(torrent['id'])+", "+str(torrent['media'])+" rip in "+str(torrent['format'])+", encoding "+str(torrent['encoding'])

            print("Found torrent "+torrentInfoString)
            
            if trackerTorrents:
                if html.unescape(torrent['filePath']) in trackerTorrents:
                    print('It looks like you already have this torrent downloaded! Continuing with next torrent...')
                    continue


            #check if a torrent is marked as freeleech (as this is the purpose of the script)
            freetorrent = torrent['freeTorrent']
            if not freetorrent:
                print("WARNING! Torrent id "+str(torrent['id'])+" NOT marked as freeleech! (It could be marked neutral-leech; size:"+str(torrent['size']/1024)+"MB) Do you wish to continue downloading?")
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
            else:
                print("Successfully added to transmission!")
            #wait 2 seconds before looping
            time.sleep(2)
    if page == flsearch['response']['pages']:
        done = True
    else:
        page += 1
