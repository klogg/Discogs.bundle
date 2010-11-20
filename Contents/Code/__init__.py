#Discogs.com Agent
#import re
import gzip

BASE_URL        = 'http://www.discogs.com'
DISCOGS_API_KEY = 'd07cb73b10'
DISCOGS_SEARCH  = BASE_URL + '/search?type=%s&q=%s&f=xml&api_key=' + DISCOGS_API_KEY #type = all | artists | releases | labels 
DISCOGS_ARTIST  = BASE_URL + '/artist/%s?f=xml&api_key=' + DISCOGS_API_KEY #add this to the metadata.id we assign to the artist
DISCOGS_RELEASE = BASE_URL + '/release/%s?f=xml&api_key=' + DISCOGS_API_KEY

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
    for resultType in ['//exactresults/result', '//searchresults/result']:
      for a in searchResponse.xpath(resultType):
        name = a.xpath('./title')[0].text
        id = String.Encode(a.xpath('./uri')[0].text.replace(BASE_URL + '/artist/','').split('?')[0].encode('utf-8'))
        Log('id: ' + id + '  name: '+ name + ' score: ' + str(score)) # + '   thumb: ' + str(r[2]))
        results.Append(MetadataSearchResult(id = id, name = name, lang  = lang, score = score))
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
    searchResponse = XML.ElementFromURL(DISCOGS_SEARCH % ('all', '"' + String.Decode(media.parent_metadata.id) + '"+"' + String.Quote(media.album) + '"'))
    if searchResponse.xpath('//searchresults')[0].get('numResults') == '0':
      searchResponse = XML.ElementFromURL(DISCOGS_SEARCH % ('all', '"' + String.Decode(media.parent_metadata.id) + '"+' + String.Quote(media.album)))
    score = 100
    for s in searchResponse.xpath('//result[@type="release"]')[:5]: #@type="master" or 
      id = s.xpath('./uri')[0].text.split('/')[-1]
      releaseXML = XML.ElementFromURL(DISCOGS_RELEASE % id)
      name = releaseXML.xpath('//title')[0].text
      try:
        thumb = releaseXML.xpath('//images/image[@type="primary"]')[0].get('uri')
      except:
        try:
          thumb = releaseXML.xpath('//images/image[@type="secondary"]')[0].get('uri')
        except:
          thumb = None
      results.Append(MetadataSearchResult(id = id, name = name, thumb = thumb, lang  = lang, score = score))
      score = score - 1
 
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
      metadata.tracks[track.xpath('./position')[0].text].name = track.xpath('./title')[0].text
