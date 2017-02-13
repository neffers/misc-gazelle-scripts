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
    for torrent in transmission.get_torrents(arguments=['id','trackers','name']):
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

#avoid spam
time.sleep(2)

#get user data json object, for passkey and authkey
print("Getting auth and passkeys from server...")
userdata = requestsSession.get(secret.baseurl+'ajax.php', params = {'action':'index'}).json()
authkey = userdata['response']['authkey']
passkey = userdata['response']['passkey']

#to manage looping through different pages
done = False
page = 1
while not done:

    #avoid spam
    time.sleep(2)

    #use the search api to return the list of freetorrents
    flsearch = requestsSession.get(secret.baseurl+'ajax.php', params = {'action':'browse','freetorrent':1,'page':page}).json()
    print("\nSearch request returned "+flsearch['status']+"on page "+str(page)+' of '+str(flsearch['response']['pages']))

    #go through each group included in results
    for torrentGroup in flsearch['response']['results']:
        
        #avoid spam
        time.sleep(2)

        #get torrent group (album) id from the torrentgroup
        torrentGroupID = torrentGroup['groupId']
        groupInfoString = html.unescape(torrentGroup['groupName']+" by "+torrentGroup['artist'])
        print("\nFound group ID "+str(torrentGroupID)+", "+groupInfoString)

        #set up json object of torrent group (album) data
        groupJSON = requestsSession.get(secret.baseurl+'ajax.php', params = {'action':'torrentgroup','id':torrentGroupID}).json()

        #loop through torrents array to get each torrent id and use it to get a torrent file
        for torrent in groupJSON['response']['torrents']:

            #create infostring to present to user
            torrentInfoString = "id "+str(torrent['id'])+", "+str(torrent['media'])+" rip in "+str(torrent['format'])+", encoding "+str(torrent['encoding'])
            print("Found torrent "+torrentInfoString)
            
            #check if the torrent seems to already exist in transmission
            if trackerTorrents:
                if html.unescape(torrent['filePath']) in trackerTorrents:
                    print('It looks like you already have this torrent downloaded! Continuing with next torrent...')
                    continue

            #check if a torrent is marked as freeleech (as this is the purpose of the script) if not, print a warning and ask the user if they wish to continue
            if not torrent['freeTorrent']:
                print("WARNING! Torrent id "+str(torrent['id'])+" NOT marked as freeleech! (It could be marked neutral-leech; size "+str(round(torrent['size']/(1038576),2))+" MB) Do you wish to continue downloading?")
                validInput = False
                while not validInput:
                    choice = input()
                    if choice.lower() == "y" or choice.lower() == "yes" or choice.lower() == "n" or choice.lower() == "no":
                        validInput = True
                    else:
                        print("Invalid input, try again")
                if choice.lower() == "n" or choice.lower() == "no":
                    continue

            #wait 2 seconds before requesting torrent downloads
            time.sleep(2)

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

    if page == flsearch['response']['pages']:
        done = True
    else:
        page += 1
