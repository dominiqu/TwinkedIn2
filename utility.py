# utilities
import oauth2 as oauth
import httplib2
from twitter import *
import simplejson 
import re
import unicodedata
import pymongo
import time
from datetime import datetime
from datetime import timedelta
from math import floor, ceil
import networkx as nx
from networkx import betweenness_centrality

def setUpLinkedInClient(user_token,user_secret):
	# specify keys (consumer: our app. user: the person logging into LinkedIn via our app (LinkedIn then gives us a placeholder user_token and user_secret to represent that user, without giving us the actual name and password of the user - although of course the username can be queried for later))
	consumer_key     =   'uszh5pfeb54o'     # this is the API key  (the 'username' of my app when talking to LinkedIn)
	consumer_secret  =   'pZsNH8d3omOpzrka' # this is the API secret (the 'password' of my app when talking to LinkedIn)
	 
	# Use your API key and secret to instantiate consumer object (consumer object = the app = api client)
	consumer = oauth.Consumer(consumer_key, consumer_secret)
	 
	# Use your developer token and secret to instantiate access token object
	access_token = oauth.Token(key=user_token,secret=user_secret)
	client = oauth.Client(consumer, access_token)

	return client

def setUpTwitterClient():
	# specify keys (consumer: our app. user: the person logging into LinkedIn via our app (LinkedIn then gives us a placeholder user_token and user_secret to represent that user, without giving us the actual name and password of the user - although of course the username can be queried for later))
	consumer_key = 'FBJuTrqQWlltW23FbthcTA'
	consumer_secret = 'NNUVmwKbV6GIIkCFON6qAMuIwaFpxaEdsylWEnCE'
	user_token       =   '1120675440-wCc8TXO3xF1D3li68yZI66ypJ68pYrQ4H8yRicu'  # OAuth User Token: this is the 'username' for the user that signed into the app 
	user_secret      =   'aaBKw61p9YR4mWDZwx2HTSjMeeZJtldcEk7RcWmaVPg'  # OAuth User secret: this is the 'password' for the user that signed into the app 

	# see "Authentication" section below for tokens and keys
	t = Twitter( auth=OAuth(user_token, user_secret, consumer_key, consumer_secret) )
	return t

def getLinkedInContacts(client):
	urlRoot = 'http://api.linkedin.com/v1/people/'
	jsonFormat = '?format=json' 
	resp,content = client.request(urlRoot+'~/connections:(id,first-name,last-name,headline,site-standard-profile-request)'+jsonFormat, 'GET', '')
	allLinkedInContacts = simplejson.loads(content)  # convert json into Python dict
	allContacts = []
	for contact in allLinkedInContacts['values']:
		allContacts.append(contact['firstName'] + ' ' + contact['lastName'])
	return allContacts

def cleanUpNamesOfLinkedInContacts(allLinkedInContacts):
	cleanNames = []
	for contact in allLinkedInContacts:
		if re.search('private',contact): 
			continue

		name = contact
		name = re.sub('\(.*\)', '', name)
		name = re.sub('\(.*\)', '', name)
		name = re.sub('^M\.','',name)
		name = re.sub('^Mr\.','',name)
		name = re.sub('^Mrs\.','',name)
		name = re.sub('^Ms\.','',name)
		name = re.sub('^Dr\.','',name)
		name = re.sub('^Igr\.','',name)
		name = re.sub('^M ','',name)
		name = re.sub('^Mr ','',name)
		name = re.sub('^Mrs ','',name)
		name = re.sub('^Ms ','',name)
		name = re.sub('^Dr ','',name)
		name = re.sub('^Igr ','',name)
		name = re.sub(',.*','',name)
		
		# get rid of initials
		name = re.sub(' \w\.\w\.\w\.','',name)
		name = re.sub(' \w\.\w\.','',name)
		name = re.sub(' \w\.','',name)

		# get rid of question marks
		#name = re.sub('?','',name)
		#name = re.sub('?','',name)
		name = re.sub('\?','',name)
		
		# get rid of leading and trailing white spaces 
		name = name.strip()

		# get rid of accents (using code I found online)
		if type(name)==unicode:
			name = unicodedata.normalize( "NFKD", name ).encode('ASCII', 'ignore')
		else:
			name = unicodedata.normalize( "NFKD", name.decode('utf-8') ).encode('ASCII', 'ignore')

		# append name
		cleanNames.append(name)
	return cleanNames

def checkWhetherLinkedInandTwitterMatch(linkedInName,twitterName,twitterScreenName):
	# get rid of accents 
	twitterName = twitterName.replace(u'\u0142','l')
	twitterName = twitterName.replace(u'\xe9','e')
	twitterName = twitterName.replace(u'\xf3','o')

	# get rid of further accents (using code I found online)
	if type(twitterName)==unicode:
		twitterName = unicodedata.normalize( "NFKD", twitterName ).encode('ASCII', 'ignore')
	else:
		twitterName = unicodedata.normalize( "NFKD", twitterName.decode('utf-8') ).encode('ASCII', 'ignore')

	# get rid of punctuation
	twitterName = twitterName.replace('.','')
	twitterName = twitterName.replace('-',' ')
	linkedInName = linkedInName.replace('.',' ')
	linkedInName = linkedInName.replace('-',' ')

	# tidy up spaces at the extremes of the Twitter string
	twitterName = twitterName.strip()
	linkedInName = linkedInName.strip()

	if linkedInName.lower() == twitterName.lower():
		return True

	if linkedInName.lower().replace(' ','') == twitterName.lower().replace(' ',''):
		return True

	if twitterScreenName.lower() == re.sub(' ','',linkedInName).lower():
		return True

	# check whether twitterName is alphanumeric. If not, reject
	temp = twitterName
	flag = temp.replace(' ', '').isalnum()
	if flag == False:
		return False

	# split Twitter name into components
	temp = twitterName
	temp = temp.split(' ')

	# check whether each part of the Twitter name is in the LinkedIn name (if so, return true)
	count = 0
	for namePart in temp:
		if namePart.lower() in linkedInName.lower().split(' '):
			count += 1
		
	# if all match, or at least two out of more, declare a match	
	if len(temp) == count:
		return True
	elif len(linkedInName.split(' ')) == count:
		return True
	elif len(temp) > 2 and count >= 2:
		return True
	else:
		return False

def checkWhetherTwitterHandleContainsProfanity(twitterScreenName):
	if 'shit' in twitterScreenName or 'fuck' in twitterScreenName or 'sex' in twitterScreenName or 'suck' in twitterScreenName:
		return True
	else:
		return False

def populateUsersFriendsAndFollowersCollection(twitterClient,userTwitterHandle,db,usersFriendsAndFollowersCollectionName,allNameSearchResultsCollectionName):
	print "Retrieving user's friends and followers..."

	# initialize collection (although remember it only gets created when the first document is inserted)
	usersFriendsAndFollowers = db[usersFriendsAndFollowersCollectionName]

	# get friends and followers
	idsFriends = twitterClient.friends.ids(screen_name=userTwitterHandle)
	idsFollowers = twitterClient.followers.ids(screen_name=userTwitterHandle)

	# look up profiles for all friends (up to 100 at a time)
	nrOfRequests = int(ceil(float(len(idsFriends['ids']))/100.0))
	beginningIndices = range(0,nrOfRequests*100,100)

	count = 0
	for index in beginningIndices:
		friendsProfiles = twitterClient.users.lookup(user_id=','.join([str(x) for x in idsFriends['ids'][index:(index+99)]]), _timeout=10)
		for profile in friendsProfiles:
			count+=1
			print 'Inserting friend profile ' + str(count) + ' into database.'
			profile['relationshipToUser'] = 'friend'
			usersFriendsAndFollowers.insert(profile)

	# look up profiles for all followers (up to 100 at a time)
	nrOfRequests = int(ceil(float(len(idsFollowers['ids']))/100.0))
	beginningIndices = range(0,nrOfRequests*100,100)

	count = 0
	for index in beginningIndices:
		followerProfiles = twitterClient.users.lookup(user_id=','.join([str(x) for x in idsFollowers['ids'][index:(index+99)]]), _timeout=10)
		for profile in followerProfiles:
			count+=1
			print 'Inserting follower profile ' + str(count) + ' into database.'
 			profile['relationshipToUser'] = 'follower'
			usersFriendsAndFollowers.insert(profile)

	# also add user's own profile to the allNameSearchResults collection
	print 'Adding user to allNameSearchResults collection...'
	profile = twitterClient.users.lookup(screen_name=userTwitterHandle, _timeout=10)
	profile = profile[0]
	profile['relationshipToUser'] = 'self'
	profile['linkedInName'] = "self"
	profile['hitNr'] = 1
	profile['numberOfSearchResults'] = 'LinkedInTwitterMatch'
	allNameSearchResults = db[allNameSearchResultsCollectionName]
	allNameSearchResults.insert(profile)

	return 0


def searchNamesOnTwitterAndStoreInMongoDB(twitterClient,cleanNames,db,allNameSearchResultsCollectionName,usersFriendsAndFollowersCollectionName):

	# create new collection with name specified by allNameSearchResultsCollectionName
	allNameSearchResults = db[allNameSearchResultsCollectionName]
	
	# see if any of the names in my contacts match those in the database of my Twitter friends and followers
	cleanNamesAlreadyInTwitterContacts = []
	if usersFriendsAndFollowersCollectionName in db.collection_names():    # check whether this has been created (yes if user Twitter handle was provided)
		print 'Looking for existing matches between LinkedIn and Twitter contacts...'
		databaseNames = db[usersFriendsAndFollowersCollectionName].distinct("name")
		for twitterName in databaseNames:
			twitterProfile = db[usersFriendsAndFollowersCollectionName].find_one({"name":twitterName})
			twitterScreenName = twitterProfile['screen_name']
			for cleanName in cleanNames:
				if checkWhetherLinkedInandTwitterMatch(cleanName,twitterName,twitterScreenName):
					print 'Match: LinkedIn (' + cleanName + ') and Twitter (' + twitterName + '). Adding to ' + allNameSearchResultsCollectionName + ' collection as unique hit.'
					# add to database
					twitterProfile['linkedInName'] = cleanName
					twitterProfile['hitNr'] = 1
					twitterProfile['numberOfSearchResults'] = -1
					allNameSearchResults.insert(twitterProfile)
					cleanNamesAlreadyInTwitterContacts.append(cleanName)
		cleanNamesAlreadyInTwitterContacts = list(set(cleanNamesAlreadyInTwitterContacts))
		cleanNames = [x for x in cleanNames if x not in cleanNamesAlreadyInTwitterContacts]

	#print cleanNamesAlreadyInTwitterContacts
	#print cleanNames
	#print len(cleanNames)

	# search all names on Twitter and enter results into MongoDB database
	cleanNamesNotFound = []
	count = 1
	waitPeriodInSeconds = 15*60+5 # add 5 seconds just in case...
	for cleanName in cleanNames:
		# perform the search (wait first if rate limit exceeded)
		print ' '
		print 'Searching LinkedIn contact nr. ' + str(count) + ': ' + cleanName
		try:
			twitterSearchJSONstring = twitterClient.users.search(q=cleanName,page=1,per_page=20,include_entities='true')
		except:
			print 'Rate limit exceed at ' + datetime.now().strftime('%H:%M:%S') +'. Waiting for ' + str(float(waitPeriodInSeconds)/float(60)) + ' minutes until ' + (datetime.now() + timedelta(float(waitPeriodInSeconds)/float(24*60*60))).strftime('%H:%M:%S') + '...'
			time.sleep(waitPeriodInSeconds)
			twitterSearchJSONstring = twitterClient.users.search(q=cleanName,page=1,per_page=20,include_entities='true')
		
		# determine number of search results
		numberOfSearchResults = len(twitterSearchJSONstring)

		# deal with case of zero search results 
		if numberOfSearchResults == 0:
			print cleanName + ' not found.'
			hitNr = 0
			enrichedJSONstring = {'linkedInName':cleanName,'hitNr':hitNr,'numberOfSearchResults':numberOfSearchResults}
			allNameSearchResults.insert(enrichedJSONstring)
			cleanNamesNotFound.append(cleanName)
			
			count = count + 1
			continue
		
		# deal with case of 1 or more search results 
		hitNr = 0
		cleanHitNr = 0
		linkedInName = cleanName
		for twitterProfile in twitterSearchJSONstring:

			# store Twitter profile if Twitter name is a reasonable match to the LinkedIn name
			twitterName = twitterProfile['name']
			twitterScreenName = twitterProfile['screen_name']
			if checkWhetherLinkedInandTwitterMatch(linkedInName,twitterName,twitterScreenName) == False:
				print linkedInName + ' : ' + twitterName + ' (@' + twitterScreenName + ') does not match.'
				hitNr += 1
				continue
			elif checkWhetherTwitterHandleContainsProfanity(twitterScreenName) == True:
				print linkedInName + ' : ' + twitterName + ' (@' + twitterScreenName + '). Handle contains profanity. Skipping...'
				hitNr += 1
				continue
			else:
				print linkedInName + ' : ' + twitterName + ' (@' + twitterScreenName + ') match.'
				hitNr += 1
				cleanHitNr += 1
				enrichedJSONstring = twitterProfile
				enrichedJSONstring['linkedInName'] = cleanName
				enrichedJSONstring['hitNr'] = hitNr
				enrichedJSONstring['numberOfSearchResults'] = numberOfSearchResults
				allNameSearchResults.insert(enrichedJSONstring)

		if cleanHitNr == 0:
			print 'No clean Twitter name matches found for ' + cleanName + '.'
			enrichedJSONstring = {'linkedInName':cleanName,'hitNr':cleanHitNr,'numberOfSearchResults':100}
			allNameSearchResults.insert(enrichedJSONstring)
			cleanNamesNotFound.append(cleanName)
		else:
			print 'Found ' + str(cleanHitNr) + ' clean hits for ' + cleanName + '.'
			
		count = count + 1	
	return cleanNamesNotFound

def searchFirstHitFriendsAndFollowersAndStoreInMongoDB(twitterClient,db,allNameSearchResultsCollectionName,topHitsFriendsAndFollowersCollectionName):
	# connect to mongoDB database (make sure mongodb is running - it's the server process that runs the database on local host)
	topHitsFriendsAndFollowers = db[topHitsFriendsAndFollowersCollectionName]
	db[topHitsFriendsAndFollowersCollectionName].remove() # make sure we're starting from scratch so no silly duplicates
	topHitsFriendsAndFollowers = db[topHitsFriendsAndFollowersCollectionName]
	
	# determine the handles of the top 2 hits
	cleanNames = db[allNameSearchResultsCollectionName].distinct("linkedInName")
	topHitHandles = []
	topHitIDs = []
	for cleanName in cleanNames:
		cursor = db[allNameSearchResultsCollectionName].find({"linkedInName":cleanName}).sort("hitNr")
		if 'screen_name' in cursor[0]:
		 	print cursor[0]['screen_name'] + '(hitNr: ' + str(cursor[0]['hitNr']) + ').'
		 	topHitHandles.append(cursor[0]['screen_name'])
		 	topHitIDs.append(cursor[0]['id'])
		 	if cursor.count()>1:
		 		topHitHandles.append(cursor[1]['screen_name'])
		 		topHitIDs.append(cursor[1]['id'])

	# start searching...
	waitPeriodInSeconds = 15*60+5 # add 5 seconds just in case...
	count = 1
	for handle in topHitHandles:
		print 'Searching for friends and followers of top hit candidate ' + str(count) + ' of ' + str(len(topHitHandles)) + ' (@' +  handle + ')...'
		JSONstring = db[allNameSearchResultsCollectionName].find({"screen_name":handle})
		twitterProfile = JSONstring[0]

		# take care of case where candidate id is protected (doesn't share tweets or follows or following)
		if twitterProfile['protected']:
			enrichedJSONstring = {'screen_name':handle, 'id':topHitIDs[count-1], 'friends':'protected', 'followers': 'protected'}
			topHitsFriendsAndFollowers.insert(enrichedJSONstring)	
		else:
			try:
				idsFollowing = twitterClient.friends.ids(screen_name=handle)
				idsFollowers = twitterClient.followers.ids(screen_name=handle)
			except:
				print 'Rate limit exceed at ' + datetime.now().strftime('%H:%M:%S') +'. Waiting for ' + str(float(waitPeriodInSeconds)/float(60)) + ' minutes until ' + (datetime.now() + timedelta(float(waitPeriodInSeconds)/float(24*60*60))).strftime('%H:%M:%S') + '...'
				time.sleep(waitPeriodInSeconds)
				idsFollowing = twitterClient.friends.ids(screen_name=handle)
				idsFollowers = twitterClient.followers.ids(screen_name=handle)
			enrichedJSONstring = {'screen_name':handle, 'id':topHitIDs[count-1], 'friends':idsFollowing['ids'], 'followers': idsFollowers['ids']}
			topHitsFriendsAndFollowers.insert(enrichedJSONstring)

		count += 1
	return 0

def printJSONfile(nodeNames,groupList,edgeTuplesList,fileName):
	# print out node list
	JSONlines = []
	JSONlines.append('{')
	JSONlines.append('    "nodes":[')
	for nodeName in nodeNames:
		JSONlines.append('      {"name":"'+ nodeName + '","group":' + str(groupList[nodeNames.index(nodeName)]) + '},')   # choose item rather than twitterSoup[item][0]['name'] because the former is the LinkedIn name and usually better maintained (i.e. with capital letters)	
	JSONlines[-1] = '      {"name":"'+ nodeName + '","group":' + str(groupList[nodeNames.index(nodeName)]) + '}'   
	JSONlines.append('],')

	# print edge info ({"source":nodeNr,"target":targetNr,"value":1},)
	JSONlines.append('  "links":[')
	for edgeTuple in edgeTuplesList:
		JSONlines.append('{"source":' + str(nodeNames.index(edgeTuple[0])) + ',"target":' + str(nodeNames.index(edgeTuple[1])) + ',"value":1},')
	JSONlines[-1] = '{"source":' + str(nodeNames.index(edgeTuple[0])) + ',"target":' + str(nodeNames.index(edgeTuple[1])) + ',"value":1}'
	JSONlines.append('    ]')
	JSONlines.append('}')

	# print contents into JSON file
	f = open(fileName, 'w')
	for item in JSONlines:
	   f.write("%s\n" % item)
	f.close()

	return JSONlines


def printGEXFfile(nodeNames,weightList,edgeTuplesList,fileName):
	GEXFlines = []
	GEXFlines.append('<?xml version="1.0" encoding="UTF-8"?>')
	GEXFlines.append('<gexf xmlns:viz="http:///www.gexf.net/1.1draft/viz" version="1.1" xmlns="http://www.gexf.net/1.1draft">')
	GEXFlines.append('<meta lastmodifieddate="2010-03-03+23:44">')
	GEXFlines.append('<creator>Gephi 0.7</creator>')
	GEXFlines.append('</meta>')
	GEXFlines.append('<graph defaultedgetype="directed" idtype="string" type="static">')
	GEXFlines.append('<nodes count="' + str(len(nodeNames)) + '">')
	idNr = 0
	for nodeName in nodeNames:
		GEXFlines.append('<node id="' + str(idNr) + '" label="' + nodeName + '"/>')
		idNr += 1
	GEXFlines.append('</nodes>')
	GEXFlines.append('<edges count="' + str(len(edgeTuplesList)) + '">')
	edgeNr = 0
	for edgeTuple in edgeTuplesList:
		GEXFlines.append('<edge id="' + str(edgeNr) + '" source="' + str(nodeNames.index(edgeTuple[0])) + '" target="' + str(nodeNames.index(edgeTuple[1])) + '" weight="' + str(weightList[nodeNames.index(nodeName)]) + '"/>')
		edgeNr += 1
	GEXFlines.append('</edges>')
	GEXFlines.append('</graph>')
	GEXFlines.append('</gexf>')

	# print contents into JSON file
	f = open(fileName, 'w')
	for item in GEXFlines:
	   f.write("%s\n" % item)
	f.close()

	return GEXFlines

def printHTMLtables(matchDict,nrOfTablesInInitialGroup):
	# get names in order of importance
	linkedInNameListOrdered = matchDict['linkedInNameListOrdered']

	# generate list of first names:
	firstNamesOrdered = []
	for name in linkedInNameListOrdered:
		firstNamesOrdered.append(re.match(r'(\w+)',name).group(1))

	# create new matchDict with only names that have at least one hit
	newMatchDict = {}
	for name in linkedInNameListOrdered:
		if len(matchDict[name])>0:
			newMatchDict[name] = matchDict[name]

	# print out tables, six images at a time, in rows of three
	count = 1;
	nrOfImages = len(newMatchDict)
	nrOfTables = int(ceil(    float(len(newMatchDict)-1)/float(6)    ))
	tableList = range(1,nrOfTables+1,1) 
	rowList = [1,2]
	colList = [1,2,3]

	jinjaString = ''			
	for table in tableList:

		if table == nrOfTablesInInitialGroup+1:
			jinjaString +=  '<span id=commentedOutTables><!--'

		jinjaString +=  '<table style="display: inline-block; float: left; ">'
		
		for row in rowList:
			jinjaString +=  '<tr>'

			for col in colList:
				jinjaString +=  '<td>'
				if count <(len(linkedInNameListOrdered)+1) and linkedInNameListOrdered[count-1] in newMatchDict	:
					jinjaString +=  '<div>'
					jinjaString +=  '<img id="twitImg_slot' + str(count) + '" class="croppedImage" src="https://api.twitter.com/1/users/profile_image?screen_name=' + newMatchDict[linkedInNameListOrdered[count-1]][0] + '&size=original" title="@' + newMatchDict[linkedInNameListOrdered[count-1]][0] + '">'
					jinjaString +=  '</div>'
					jinjaString +=  '<div id="slot' + str(count) + '" style="text-align: center; color:white; font: 15px/30px Helvetica, sans-serif;">'
					jinjaString +=  linkedInNameListOrdered[count-1]
					jinjaString +=  '</div>'
					jinjaString +=  '<div style="text-align: center;">'
					jinjaString +=  '<span id="twitterButton' + str(count) + '"><a href="https://twitter.com/' + newMatchDict[linkedInNameListOrdered[count-1]][0] + '" class="twitter-follow-button" data-show-count="false" data-size="small">Follow @' + newMatchDict[linkedInNameListOrdered[count-1]][0] + '</a></span>'
					jinjaString +=  '<script>!function(d,s,id){var js,fjs=d.getElementsByTagName(s)[0];if(!d.getElementById(id)){js=d.createElement(s);js.id=id;js.src="//platform.twitter.com/widgets.js";fjs.parentNode.insertBefore(js,fjs);}}(document,"script","twitter-wjs");</script>'
					jinjaString +=  '</div>'
					jinjaString +=  '<div id="allTextUnderNeathImage' + str(count) + '" style="text-align: center; margin-top: -7px; margin-bottom: 2px">'
					#jinjaString +=  '<span><a id="buttonNr' + str(count) + '" class = "textButton" onClick="myFunction_slot(this);" style="text-align: center;">Different <span id="buttonFirstName' + str(count) + '">' + firstNamesOrdered[count-1] + '</span>?</a></span><span style="font-size: 6pt;"> | </span><span><a id="buttonNrb' + str(count) + '" class = "textButton" onClick="myFunction_slotBack(this);" style="text-align: center;">back</a></span>'
					jinjaString +=  '<span><a id="buttonNr' + str(count) + '" class = "textButton" onClick="myFunction_forward(this);" style="text-align: center;">Different <span id="buttonFirstName' + str(count) + '">' + firstNamesOrdered[count-1] + '</span>?</a></span>'
					jinjaString +=  '<span id="printUndoTextButton' + str(count) + '"></span>'
					jinjaString +=  '</div>'
				count += 1
				jinjaString +=  '</td>'

			jinjaString +=  '</tr>'
		jinjaString += '</table>'
	jinjaString += '--></span>'

	jinjaStringAndNrOfTables = [jinjaString,nrOfTables,nrOfImages]	
	return jinjaStringAndNrOfTables

def constructGraph(db,allNameSearchResultsCollectionName,topHitsFriendsAndFollowersCollectionName):

	# find all nodes in the allNameSearchResults collection
	fullIDList = db[allNameSearchResultsCollectionName].distinct("id")

	# go through all friends and followers in topHitsFriendsAndFollowers collection, and see whether any of them are in the full handle list
	allHandlesWithContacts = db[topHitsFriendsAndFollowersCollectionName].distinct("screen_name")

	edgeTuplesList = []
	edgeNr = 0
	for handle in allHandlesWithContacts:
		try:    # try except statement is just here because I forgot to rerun my entire script on the top friends and followers and now the dbs don't match anymore... can get rid of this statement later...
			handleLinkedInName = db[allNameSearchResultsCollectionName].find_one({"screen_name":handle})['linkedInName']
		except:
			continue
		friendsList = db[topHitsFriendsAndFollowersCollectionName].find_one({"screen_name":handle})['friends'] # doing this by handles rather than ids because initial DB download had bug on the ids but not handles
		followersList = db[topHitsFriendsAndFollowersCollectionName].find_one({"screen_name":handle})['followers']
		if friendsList == 'protected': 
			print handle + ' is protected.'
			continue

		for idNr in fullIDList:
			if idNr in friendsList:
				fullListIDnrLinkedInName = db[allNameSearchResultsCollectionName].find_one({"id":idNr})['linkedInName']
				fullListIDnrHandle = db[allNameSearchResultsCollectionName].find_one({"id":idNr})['screen_name']
				print handle + ' is following ' + fullListIDnrHandle + '.'
				if handleLinkedInName == fullListIDnrLinkedInName: 
					print 'Oh wait! ' + handleLinkedInName + ' (' + handle + ') is just following himself: ' + fullListIDnrLinkedInName + ' (' + fullListIDnrHandle + ')! Skipping...'
					continue
				edgeNr += 1
				if (handle,fullListIDnrHandle) not in edgeTuplesList: edgeTuplesList.append((handle,fullListIDnrHandle))
			if idNr in followersList:
				fullListIDnrLinkedInName = db[allNameSearchResultsCollectionName].find_one({"id":idNr})['linkedInName']
				fullListIDnrHandle = db[allNameSearchResultsCollectionName].find_one({"id":idNr})['screen_name']
				print fullListIDnrHandle + ' is following ' + handle + '.'
				if handleLinkedInName == fullListIDnrLinkedInName: 
					print 'Oh wait! ' + handleLinkedInName + ' (' + handle + ') is just following himself: ' + fullListIDnrLinkedInName + ' (' + fullListIDnrHandle + ')! Skipping...'
					continue
				edgeNr += 1
				if (fullListIDnrHandle,handle) not in edgeTuplesList: edgeTuplesList.append((fullListIDnrHandle,handle))

	nodeNames = db[allNameSearchResultsCollectionName].distinct("screen_name")
	
	graph = [nodeNames,edgeTuplesList]

	return graph

def computeNumberOfEdgesInvolvedInAndStoreInAllNameSearchResultsCollection(edgeTuples,db,allNameSearchResultsCollectionName):

	#1. number of directed edges involved in (store in allNameSearchResults collection)
	fullScreenNameList = db[allNameSearchResultsCollectionName].distinct("screen_name")
	numberOfDirectedEdgesForEachNode = [0]*len(fullScreenNameList)
	for screen_name in fullScreenNameList:
		for edgeTuple in edgeTuples:
			if screen_name in edgeTuple:
				numberOfDirectedEdgesForEachNode[fullScreenNameList.index(screen_name)] += 1

	# store number of directed edges for each node in database
	for screen_name in fullScreenNameList:
		profiles = db[allNameSearchResultsCollectionName].find({"screen_name":screen_name})
		for profile in profiles:
			objectID = profile["_id"]
			screen_name = profile['screen_name']
			numberOfDirectedEdgesInvolvedIn = numberOfDirectedEdgesForEachNode[fullScreenNameList.index(screen_name)]
			profile['numberOfDirectedEdgesInvolvedIn'] = numberOfDirectedEdgesInvolvedIn
			db[allNameSearchResultsCollectionName].update({"_id":objectID}, profile, safe=True)

	return 0

def computeBetweennessCentralityAndStoreInAllNameSearchResultsCollection(nodeList,edgeTuples,db,allNameSearchResultsCollectionName):

	G=nx.Graph()
	G.add_nodes_from(nodeList)
	G.add_edges_from(edgeTuples)
	betweennessCentralityDict = betweenness_centrality(G, normalized=False)

	fullScreenNameList = db[allNameSearchResultsCollectionName].distinct("screen_name")
	for screen_name in fullScreenNameList:
		profiles = db[allNameSearchResultsCollectionName].find({"screen_name":screen_name})
		for profile in profiles:
			objectID = profile["_id"]
			betweennessCentrality = betweennessCentralityDict[screen_name]
			profile['betweennessCentrality'] = betweennessCentrality
			db[allNameSearchResultsCollectionName].update({"_id":objectID}, profile, safe=True)

	return betweennessCentralityDict

def computeMatchDictWithOrderingByNumberOfEdgesInvolvedIn(db,allNameSearchResultsCollectionName):

	cleanNames = db[allNameSearchResultsCollectionName].distinct("linkedInName")
	matchDict = {}
	for cleanName in cleanNames:
		profiles = db[allNameSearchResultsCollectionName].find({"linkedInName":cleanName}).sort([("numberOfDirectedEdgesInvolvedIn",-1), ("hitNr", 1), ("numberOfSearchResults", 1)])
		orderedScreenNameList = []
		for profile in profiles:
			if profile['numberOfSearchResults'] == 0 or profile['numberOfSearchResults'] == 100:
				continue
			orderedScreenNameList.append(profile['screen_name'])
			print cleanName + ': ' + orderedScreenNameList[-1] + ': ' + str(profile['numberOfDirectedEdgesInvolvedIn'])
		matchDict[cleanName] = orderedScreenNameList

	# get ordered list of the keys based on relevance of first screen_name associated with each cleanName
	temp = db[allNameSearchResultsCollectionName].find().sort([("numberOfDirectedEdgesInvolvedIn",-1), ("hitNr", 1), ("numberOfSearchResults", 1)])
	linkedInNameListOrdered = []
	for profile in temp:
		if profile['linkedInName'] not in linkedInNameListOrdered:
			linkedInNameListOrdered.append(profile['linkedInName'])
	matchDict['linkedInNameListOrdered'] = linkedInNameListOrdered

	return matchDict

def computeMatchDictWithOrderingBybetweennessCentrality(db,allNameSearchResultsCollectionName):

	cleanNames = db[allNameSearchResultsCollectionName].distinct("linkedInName")
	matchDict = {}
	for cleanName in cleanNames:
		profiles = db[allNameSearchResultsCollectionName].find({"linkedInName":cleanName}).sort([("betweennessCentrality",-1), ("hitNr", 1), ("numberOfSearchResults", 1)])
		orderedScreenNameList = []
		for profile in profiles:
			if profile['numberOfSearchResults'] == 0 or profile['numberOfSearchResults'] == 100:
				continue
			orderedScreenNameList.append(profile['screen_name'])
			print cleanName + ': ' + orderedScreenNameList[-1] + ': ' + str(profile['betweennessCentrality'])
		matchDict[cleanName] = orderedScreenNameList

	# get ordered list of the keys based on relevance of first screen_name associated with each cleanName
	temp = db[allNameSearchResultsCollectionName].find().sort([("betweennessCentrality",-1), ("hitNr", 1), ("numberOfSearchResults", 1)])
	linkedInNameListOrdered = []
	for profile in temp:
		if profile['linkedInName'] not in linkedInNameListOrdered:
			linkedInNameListOrdered.append(profile['linkedInName'])
	matchDict['linkedInNameListOrdered'] = linkedInNameListOrdered

	return matchDict

def computeMatchDictWithOrderingBybetweennessCentralityThenNrOfEdgesInvolvedIn(db,allNameSearchResultsCollectionName):

	cleanNames = db[allNameSearchResultsCollectionName].distinct("linkedInName")
	matchDict = {}
	for cleanName in cleanNames:
		profiles = db[allNameSearchResultsCollectionName].find({"linkedInName":cleanName}).sort([("betweennessCentrality",-1), ("numberOfDirectedEdgesInvolvedIn",-1), ("hitNr", 1), ("numberOfSearchResults", 1)])
		orderedScreenNameList = []
		for profile in profiles:
			if profile['numberOfSearchResults'] == 0 or profile['numberOfSearchResults'] == 100:
				continue
			orderedScreenNameList.append(profile['screen_name'])
			print cleanName + ': ' + orderedScreenNameList[-1] + ': ' + str(profile['betweennessCentrality'])
		matchDict[cleanName] = orderedScreenNameList

	# get ordered list of the keys based on relevance of first screen_name associated with each cleanName
	temp = db[allNameSearchResultsCollectionName].find().sort([("betweennessCentrality",-1), ("numberOfDirectedEdgesInvolvedIn",-1), ("hitNr", 1), ("numberOfSearchResults", 1)])
	linkedInNameListOrdered = []
	for profile in temp:
		if profile['linkedInName'] not in linkedInNameListOrdered:
			linkedInNameListOrdered.append(profile['linkedInName'])
	matchDict['linkedInNameListOrdered'] = linkedInNameListOrdered

	return matchDict
