#Discogs.com Agent
#import re
import gzip

BASE_URL = 'http://www.discogs.com'
DISCOGS_API_KEY = 'd07cb73b10'
DISCOGS_SEARCH = BASE_URL + '/search?type=%s&q=%s&f=xml&api_key=' + DISCOGS_API_KEY #type = all | artists | releases | labels 
DISCOGS_ARTIST = BASE_URL + '/artist/%s?f=xml&api_key=' + DISCOGS_API_KEY #add this to the metadata.id we assign to the artist

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
        id = a.xpath('./uri')[0].text.replace(BASE_URL + '/artist/','').split('?')[0]
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
    artistXML = XML.ElementFromURL(DISCOGS_ARTIST % metadata.id)
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
        url = img.get('uri')
        if url not in metadata.posters:
          metadata.posters[url] = Proxy.Media(HTTP.Request(url), sort_order = i)
          i+=1
          
    for x in metadata.posters:
      Log(x)
      
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
    #for album in lastfm.ArtistAlbums(String.Unquote(media.parent_metadata.id)):
    #  (name, artist, thumb, url) = album
    #  albumID = url.split('/')[-1]
    #  id = media.parent_metadata.id + '/' + albumID.replace('+', '%20')
    #  dist = Util.LevenshteinDistance(name, media.album)
    #  Log(media.album) 
    #  Log(name + ': ' + str(dist))
    #  results.Append(MetadataSearchResult(id = id, name = name, thumb = thumb, lang  = lang, score = 90-dist))
    #results.Sort('score', descending=True)
    return
 
  def update(self, metadata, media, lang):
    (artistName, albumName) = metadata.id.split('/')
    artistName = String.Unquote(artistName).encode('utf-8')
    albumName = String.Unquote(albumName).encode('utf-8')

    album = XML.ElementFromURL(lastfm.ALBUM_INFO % (String.Quote(artistName, True), String.Quote(albumName, True)))
    thumb = album.xpath("//image[@size='extralarge']")[0].text
    metadata.title = album.xpath("//name")[0].text
    date = album.xpath("//releasedate")[0].text.split(',')[0].strip()
    metadata.originally_available_at = None
    if len(date) > 0:
      metadata.originally_available_at = Datetime.ParseDate(date).date()
    if thumb not in metadata.posters:
      metadata.posters[thumb] = Proxy.Media(HTTP.Request(thumb))
    
    tracks = lastfm.AlbumTrackList(artistName, albumName)
    for num in range(len(tracks)):
      metadata.tracks[str(num+1)].name = tracks[num][0]
      
#from: http://code.google.com/p/jwsandbox/source/browse/trunk/Discogs/py_tag.py
#      def clean_file(f):
#          """
#              Removes unwanted characters from file names
#          """
#          a = unicode(f).encode("utf-8")
#          for k,v in CHAR_EXCEPTIONS.iteritems():
#              a = a.replace(k, v)
#          cf = re.compile(r'[^-\w.\(\)_]')
#          return cf.sub('', str(a))
#--
#      if __name__ == "__main__":
#          if len(sys.argv) != 3:
#              print "Usage: py_tag.py <folder of mp3s> <discogs release id>"
#              sys.exit()
#          files = prep_files(sys.argv[1],1)
#          disc = Discogs(sys.argv[2])
#          tot = str(len(disc.track_list))

