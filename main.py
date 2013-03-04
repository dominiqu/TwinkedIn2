from utility import setUpLinkedInClient, setUpTwitterClient, getLinkedInContacts, cleanUpNamesOfLinkedInContacts, populateUsersFriendsAndFollowersCollection, searchNamesOnTwitterAndStoreInMongoDB, searchFirstHitFriendsAndFollowersAndStoreInMongoDB, constructGraph, printJSONfile, printGEXFfile, computeNumberOfEdgesInvolvedInAndStoreInAllNameSearchResultsCollection, computeBetweennessCentralityAndStoreInAllNameSearchResultsCollection, computeMatchDictWithOrderingBybetweennessCentralityThenNrOfEdgesInvolvedIn, computeMatchDictWithOrderingByNumberOfEdgesInvolvedIn
import pymongo
import pickle

# get LinkedIn credentials (normally from user login), set up client and get contacts. For Twitter I'll just use my own credentials
linkedIn_user_token       =   '1802fb97-fc3a-4dff-904a-647d989784db'  # OAuth User Token: this is the 'username' for the user that signed into the app 
linkedIn_user_secret      =   '8ad8d623-0655-48c8-869d-bcf45e3426ea'  # OAuth User secret: this is the 'password' for the user that signed into the app 
linkedInClient = setUpLinkedInClient(linkedIn_user_token,linkedIn_user_secret)
allLinkedInContacts = getLinkedInContacts(linkedInClient)
cleanNames = cleanUpNamesOfLinkedInContacts(allLinkedInContacts)
pkl_file = open('giovannaCleanNames.pkl', 'rb')
cleanNames = pickle.load(pkl_file)
del cleanNames[0]
pkl_file.close()

# set up Twitter client (using my own credentials) and optionally supply user's twitter handle
#userTwitterHandle = 'dvdsompel'   # fill in with a handle starting by 'none' if no Twitter handle provided, and the following code will take care of itself (it just won't have the user included in the final network)
userTwitterHandle = 'gmiritello'
#userTwitterHandle = 'akuhn'
twitterClient = setUpTwitterClient()

# start new collections in the database if they don't exist yet
conn = pymongo.Connection()
db = conn.twinkedIn
usersFriendsAndFollowersCollectionName = userTwitterHandle + '_usersFriendsAndFollowers'
allNameSearchResultsCollectionName = userTwitterHandle + '_allNameSearchResults'
topHitsFriendsAndFollowersCollectionName = userTwitterHandle + '_topHitsFriendsAndFollowers'

# db.drop_collection(usersFriendsAndFollowersCollectionName) # remove collection from the database
# db.drop_collection(allNameSearchResultsCollectionName) # remove collection from the database
# db.drop_collection(topHitsFriendsAndFollowersCollectionName) # remove collection from the database
if allNameSearchResultsCollectionName not in db.collection_names():   # dowload collections 
	if userTwitterHandle[0:4] != 'none':
		populateUsersFriendsAndFollowersCollection(twitterClient,userTwitterHandle,db,usersFriendsAndFollowersCollectionName,allNameSearchResultsCollectionName)

	searchNamesOnTwitterAndStoreInMongoDB(twitterClient,cleanNames,db,allNameSearchResultsCollectionName,usersFriendsAndFollowersCollectionName)  # search all LinkedIn contacts on Twitter and store into MongoDB database (as 'allNameSearchResults' collection)
	searchFirstHitFriendsAndFollowersAndStoreInMongoDB(twitterClient,db,allNameSearchResultsCollectionName,topHitsFriendsAndFollowersCollectionName)  # # search for friends and followers of all first and second hits in 'allNameSearchResults' collection and store into MongoDB database (as 'firstHitFriendsAndFollowers' collection)

#... code below leads all the way to the (a) pickled matchDict and (b) json file of the graph

# construct graph
graph = constructGraph(db,allNameSearchResultsCollectionName,topHitsFriendsAndFollowersCollectionName)
nodeList = graph[0]
groupList = [1]*len(nodeList)
edgeTuples = graph[1]

# print out json file of full graph
JSONlines = printJSONfile(nodeList,groupList,edgeTuples,'./static/json/twinkedInGraph.json')  # print out json file of graph with all nodes

# print json file with connected nodes only
newNodeNames = []
for edgeTuple in edgeTuples:
	if edgeTuple[0] not in newNodeNames:
		newNodeNames.append(edgeTuple[0])
	if edgeTuple[1] not in newNodeNames:
		newNodeNames.append(edgeTuple[1])
newGroupList = [1]*len(newNodeNames)
newJSONlines = printJSONfile(newNodeNames,newGroupList,edgeTuples,'./static/json/twinkedInGraph_connectedOnly.json')

# print gexf file
weightList = [1]*len(nodeList)
GEXFlines = printGEXFfile(nodeList,weightList,edgeTuples,'./static/json/twinkedInGraph.gexf')

# analyze modularity
#1. compute number of directed edges involved in and store in allNameSearchResults collection
computeNumberOfEdgesInvolvedInAndStoreInAllNameSearchResultsCollection(edgeTuples,db,allNameSearchResultsCollectionName)

#2. in-betweenness using networkx
betweennessCentralityDict = computeBetweennessCentralityAndStoreInAllNameSearchResultsCollection(nodeList,edgeTuples,db,allNameSearchResultsCollectionName)

# store results in matchDict by order of number of edges involved in, or by betweenness centrality
matchDict = computeMatchDictWithOrderingBybetweennessCentralityThenNrOfEdgesInvolvedIn(db,allNameSearchResultsCollectionName)
#matchDict = computeMatchDictWithOrderingByNumberOfEdgesInvolvedIn(db,allNameSearchResultsCollectionName)

#del matchDict['Keoki Seu']
#linkedInNameListOrdered = matchDict['linkedInNameListOrdered']
#del linkedInNameListOrdered[linkedInNameListOrdered.index('Keoki Seu')]
#matchDict['linkedInNameListOrdered'] = linkedInNameListOrdered 

#totalNr= 0
#hitNr = 0
#for key in matchDict:
#	if len(matchDict[key])>0:
#		hitNr+=1
#		totalNr += len(matchDict[key])
#		print len(matchDict[key])

# pickle the matchDict
output = open('matchDict.pkl', 'wb')
pickle.dump(matchDict, output)
output.close() 











### Rate limits:
# temp4 = twitterClient.followers.ids(screen_name='akuhn')
# rate limit: 15/15 mins, but get up to 5000 ids/show

# temp5 = twitterClient.friends.ids(screen_name='akuhn')
# rate limit: 15/15 mins, but get up to 5000 ids/show

# temp3 = twitterClient.statuses.user_timeline(screen_name='ay_shake')
# gets last 200 tweets for a user (have to set a 'count=200' argument). For each: mentions, text, hashtags, number of retweets, number of tweets, number of followers, number of following, whether user protected info
# rate limit: 180/15 mins

