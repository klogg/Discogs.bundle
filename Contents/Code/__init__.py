#Discogs.com Agent
#import re
import gzip

BASE_URL        = 'http://www.discogs.com'
DISCOGS_API_KEY = 'd07cb73b10'
DISCOGS_SEARCH  = BASE_URL + '/search?type=%s&q=%s&f=xml&api_key=' + DISCOGS_API_KEY #type = all | artists | releases | labels 
DISCOGS_ARTIST  = BASE_URL + '/artist/%s?f=xml&api_key=' + DISCOGS_API_KEY #add this to the metadata.id we assign to the artist
DISCOGS_RELEASE = BASE_URL + '/release/%s?f=xml&api_key=' + DISCOGS_API_KEY
DISCOGS_MASTER  = BASE_URL + '/master/%s?f=xml&api_key=' + DISCOGS_API_KEY
ALBUM_SEARCH_HTML = BASE_URL + '/advanced_search?artist=%s+&release_title=%s&track=%s&btn=Search+Releases'

def Start():
  HTTP.CacheTime = CACHE_1WEEK
  
class DiscogsAgent(Agent.Artist):
  name = 'Discogs'
  languages = [Locale.Language.English]
  
  def search(self, results, media, lang):
    score = 100
    if media.artist.lower().startswith('the '):
      searchArtist = media.artist[4:] + ', ' + media.artist[:3]
    else:
      searchArtist = media.artist
    
    searchResponse = XML.ElementFromURL(DISCOGS_SEARCH % ('artists', String.Quote(searchArtist)))
    
    #grab exact results
    artists = {} 
    
    for resultType in ['//exactresults/result', '//searchresults/result']:
      for a in searchResponse.xpath(resultType):
        name = a.xpath('./title')[0].text
        id = String.Encode(a.xpath('./uri')[0].text.replace(BASE_URL + '/artist/','').split('?')[0].encode('utf-8'))
        lev = lev_ratio(media.artist, name)
        #if lev > titles.get('best_lev_ratio').get('lev_ratio'):
        artists[lev] = {'id': id, 'name':name } #, 'lev_ratio': lev}
        #Log('id: ' + String.Decode(id) + '  name: '+ name + ' score: ' + str(score)) # + '   thumb: ' + str(r[2]))
        #results.Append(MetadataSearchResult(id = id, name = name, lang  = lang, score = score))
        #score = score - 1
    
    k = artists.keys()
    Log(k)
    k = sorted(k, reverse=True)
    Log(k)
    score = 100
    for r in k:
      results. Append(MetadataSearchResult(id = artists[r].get('id'), name = artists[r].get('name'), lang  = lang, score = score))
      score = score - 1
      
    # Finally, de-dupe the results.
    toWhack = []
    resultMap = {}
    for result in results:
      if not resultMap.has_key(result.id):
        resultMap[result.id] = True
      else:
        toWhack.append(result)
    for dupe in toWhack:
      results.Remove(dupe)
    
  def update(self, metadata, media, lang):
    artistXML = XML.ElementFromURL(DISCOGS_ARTIST % String.Decode(metadata.id))
    metadata.title = artistXML.xpath('//name')[0].text
    if metadata.title.lower().endswith(', the'):
      metadata.title = metadata.title[-3:] + ' ' + metadata.title[:-5]
    
    #summary = artistXML.xpath('//bio/content')[0]
    #if summary.text:
    #  metadata.summary = self.decodeXml(re.sub(r'<[^<>]+>', '', summary.text))
    
    #url = artistXML.xpath['//images/image[@type="primary"]'][0].get('uri')
    #metadata.posters[url] = Proxy.Media(HTTP.Request(url))

    i=1
    for imgType in ['//images/image[@type="primary"]', '//images/image[@type="secondary"]']:
      for img in artistXML.xpath(imgType):
        try:
          url = img.get('uri')
          if url not in metadata.posters:
            metadata.posters[url] = Proxy.Media(HTTP.Request(url), sort_order = i)
            i+=1
        except:
          pass
      
    #metadata.genres.clear()
    #for genre in artist.xpath('//artist/tags/tag/name'):
    #  metadata.genres.add(genre.text.capitalize())

  def decodeXml(self, text):
    trans = [('&amp;','&'),('&quot;','"'),('&lt;','<'),('&gt;','>'),('&apos;','\''),('\n ','\n')]
    for src, dst in trans:
      text = text.replace(src, dst)
    return text

class DiscogsAlbumAgent(Agent.Album):
  name = 'Discogs'
  languages = [Locale.Language.English] 
  
  def search(self, results, media, lang):
    if 1==0: #skip. this uses their advanced html search...not working well.
      #Log('***Search 0:')
      htmlSearch = HTML.ElementFromURL(ALBUM_SEARCH_HTML % (String.Decode(media.parent_metadata.id), String.Quote(media.album), '"' + String.Quote(media.tracks[1].title) + '","' + String.Quote(media.tracks[2].title) + '"'))
      id = htmlSearch.xpath('//div[@class="thumb"]/a')[0].get('href').split('/')[-1]
      releaseXML = XML.ElementFromURL(DISCOGS_RELEASE % id)
      name = releaseXML.xpath('//title')[0].text
      #Log('adding result: ' + name + ' score: ' + str(100))
      try:
        thumb = releaseXML.xpath('//images/image[@type="primary"]')[0].get('uri')
      except:
        try:
          thumb = releaseXML.xpath('//images/image[@type="secondary"]')[0].get('uri')
        except:
          thumb = None
      results.Append(MetadataSearchResult(id = id, name = name, thumb = thumb, lang  = lang, score = 100))
    try:
      #Log('***Search 1:')
      #searchResponse = XML.ElementFromURL(DISCOGS_SEARCH % ('releases', '"' + String.Decode(media.parent_metadata.id) + '"+"' + String.Quote(media.album) + '"'))
      searchResponse = XML.ElementFromURL(DISCOGS_SEARCH % ('all', '"' + String.Decode(media.parent_metadata.id) + '"+"' + String.Quote(media.album) + '"'))
      #Log('returned number of responses, search 1: ' + str(len(searchResponse)))
      searchReturned = True
    except: 
      searchReturned = False
    if searchReturned == False or searchResponse.xpath('//searchresults')[0].get('numResults') == '0':
      try:
        #Log('***Search 2:')
        searchResponse = XML.ElementFromURL(DISCOGS_SEARCH % ('releases', '"' + String.Decode(media.parent_metadata.id) + '"+' + String.Quote(media.album)))
        Log('returned number of responses, search 2: ' + str(len(searchResponse)))
        searchReturned = True
      except: 
        searchReturned = False
    if searchReturned == False or searchResponse.xpath('//searchresults')[0].get('numResults') == '0':
      #Log('***Falling back to artist page discog list 3:')
      artistXML = XML.ElementFromURL(DISCOGS_ARTIST % String.Decode(media.parent_metadata.id))
      
      titles = { 'best_lev_ratio': { 'id': None, 'name': None, 'lev_ratio': -1.0 } } # -1 to force > check later
      
      for r in artistXML.xpath('//releases/release'):
        id = r.get('id')
        name = r.xpath('./title')[0].text
        #dist = Util.LevenshteinDistance(media.album, name)
        lev = lev_ratio(media.album, name)
        if lev > titles.get('best_lev_ratio').get('lev_ratio'):
          titles['best_lev_ratio'] = {'id': id, 'name':name, 'lev_ratio': lev}
        #Log('Album from Scanner: ' + media.album)
        #Log('Album from Discogs: ' + name + ' || score: ' + str(lev))
      try:
        thumb = XML.ElementFromURL(DISCOGS_RELEASE % titles['best_lev_ratio']['id']).xpath('//images/image[@type="primary"]')[0].get('uri')
      except:
        thumb=None
      results.Append(MetadataSearchResult(id = titles['best_lev_ratio']['id'], name = titles['best_lev_ratio']['name'], thumb = thumb, lang = lang, score = 99))
    else:
      Log('***Using searchResponse to find best match:')
      score = 99
      #grab a list of all the tracks we have
      inTrackCount = len(media.tracks)
      #for t in media.tracks:
      #  Log('media.tracks[' + str(t) + ']: ' + media.tracks[t].title)
      
      #look at the top five results returned
      mainReleaseIDs = []
      for s in searchResponse.xpath('//result[@type="release" or @type="master"]')[:5]:
        id = s.xpath('./uri')[0].text.split('/')[-1]
        #Log(id)
        #if s.get('type') == 'master':
        #  releaseID = getReleaseFromMaster(id)
        if s.get('type') == 'release':
          #Log('type = release')
          try: 
            masterID = getMasterFromRelease(id)
            #Log('getMasterFromRelease('+ id + '): ' + str(masterID))
            mainReleaseID = getMainReleaseFromMaster(masterID)
            #Log('getMasterFromRelease('+ masterID + '): ' + str(mainReleaseID))
          except:
            mainReleaseID = id
            #type = 'release'
        elif s.get('type') == 'master':
          #Log('type = master')
          mainReleaseID = getMainReleaseFromMaster(id)
        if not mainReleaseID in mainReleaseIDs:
          #Log('new mainReleaseID: ' + mainReleaseID)
          mainReleaseIDs.append(mainReleaseID)
          mainReleaseXML = XML.ElementFromURL(DISCOGS_RELEASE % mainReleaseID)
          #***********this is where we should start comparing numbers of tracks / names of tracks to confirm we got the right thing
          mainReleaseTrackCount = len(mainReleaseXML.xpath('//track/title'))
          mainReleaseTracks = []
          for track in mainReleaseXML.xpath('//track/title'):
            #Log(track.text)
            mainReleaseTracks.append(track.text.strip().lower())
          scoreBoost = 10 - abs(inTrackCount-mainReleaseTrackCount)
          #Log('inTrackCount: ' +str(inTrackCount))
          #Log('mainReleaseTrackCount: ' + str(mainReleaseTrackCount))
          #Log('scoreBoost: ' + str(scoreBoost))
          name = mainReleaseXML.xpath('//title')[0].text
          #Log('adding result: ' + name + ' score: ' + str(score + scoreBoost))
          try:
            thumb = mainReleaseXML.xpath('//images/image[@type="primary"]')[0].get('uri')
          except:
            try:
              thumb = mainReleaseXML.xpath('//images/image[@type="secondary"]')[0].get('uri')
            except:
              thumb = None
          results.Append(MetadataSearchResult(id = mainReleaseID, name = name, thumb = thumb, lang  = lang, score = score + scoreBoost))
          score = score - 1
        #list(set(a).intersection(set(b)))
    results.Sort('score', descending=True)
    #for r in results:
    #  Log(r) 
      
  def update(self, metadata, media, lang):
    releaseXML = XML.ElementFromURL(DISCOGS_RELEASE % metadata.id)
    i=1
    for imgType in ['//images/image[@type="primary"]', '//images/image[@type="secondary"]']:
      for img in releaseXML.xpath(imgType):
        try:
          url = img.get('uri')
          if url not in metadata.posters:
            metadata.posters[url] = Proxy.Media(HTTP.Request(url), sort_order = i)
            i+=1
        except:
          pass
    metadata.title = releaseXML.xpath('//title')[0].text
    try:
      metadata.summary = releaseXML.xpath('//notes')[0].text
    except:
      pass
    try:
      metadata.studio = releaseXML.xpath('//labels/label')[0].get('name')
    except:
      pass
    try:
      date = releaseXML.xpath('//released')[0].text
    except:
      date = ''
    if len(date)==4:
      date = '1/1/' + date
    metadata.originally_available_at = None
    if len(date) > 0:
      try:
        metadata.originally_available_at = Datetime.ParseDate(date).date()
      except:
        try:
          metadata.originally_available_at = Datetime.ParseDate(date[:4]).date()
        except:
          pass
    for track in releaseXML.xpath('//track'):
      trackNum = track.xpath('./position')[0].text
      if not trackNum:
        trackNum = ''
      metadata.tracks[trackNum].name = track.xpath('./title')[0].text
      
    #Log("tracks:")
    #for t in metadata.tracks:
    #  Log(t)
    #Log('metadata.originally_available_at: ' + str(metadata.originally_available_at))
    #Log('date: ' + date)
    #Log('metadata.title: ' + metadata.title)
    #Log('metadata.studio: ' + metadata.studio)
    #Log('metadata.posters: ')
    #for p in metadata.posters:
    #  Log(p)
    
def getMasterFromRelease(id):          
  return XML.ElementFromURL(DISCOGS_RELEASE % id).xpath('//master_id')[0].text #grab the master id from the release xml

def getMainReleaseFromMaster(id):
  return XML.ElementFromURL(DISCOGS_MASTER % id).xpath('//main_release')[0].text #grab main release ID
  
def getReleaseFromMaster(id):       
  return XML.ElementFromURL(DISCOGS_MASTER % id).xpath('//versions/release')[0].get('id') #grab the first release in the master's release version list   

def lev_ratio(s1,s2):
  distance = Util.LevenshteinDistance(s1,s2)
  #Log('s1/s2: "%s" / "%s"' % (s1,s2))
  #Log('distance: %s' % distance)
  max_len  = float(max([ len(s1), len(s2) ]))
  #Log('max_len: %s' % max_len)
  ratio = 0.0
  try:
    ratio = float(1 - (distance/max_len))
  except:
    pass

  #Log('ratio: %s' % ratio)
  return ratio