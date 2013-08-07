NAME = "DIY"
BASE_URL = "http://www.diynetwork.com"
ART = 'art-default.jpg'
ICON = 'icon-default.png'


# Full Episode URLs
SHOW_LINKS_URL = "http://www.diynetwork.com/full-episodes/package/index.html"

# modified links to work with DIY feeds
# NB: this is a "made up" URL, they don't have direct play URLs
# for videos (actually they do have direct play URLs but almost never use them)
# and even their listing pages are all over the map
# therefore the URL service is local (within the plugin) as opposed
# to putting it globally within the services.bundle for use with PlexIt and the like
VIDEO_URL = "http://www.diynetwork.com/video/?videoId=%s&showId=%s"

VPLAYER_MATCHES = Regex("SNI.DIY.Player.FullSize\('vplayer-1','([^']*)'")
RE_AMPERSAND = Regex('&(?!amp;)')

####################################################################################################
def Start():

	# Setup the artwork and name associated with the plugin
	ObjectContainer.title1 = NAME
	HTTP.CacheTime = CACHE_1HOUR
	ObjectContainer.art = R(ART)
	DirectoryItem.thumb = R(ICON)

####################################################################################################
@handler('/video/diy', NAME)
def MainMenu():

	oc = ObjectContainer()
	
	Log.Debug("*** Begin Processing!  Good luck!")
	
	for s in HTML.ElementFromURL(SHOW_LINKS_URL).xpath("//div[@id='full-episodes']/div/ul/li/a[@href[starts-with(.,'/diy')]]"):
		
		Log.Debug("***series*** Inside the loop.")
		
		title = s.text
		
		Log.Debug("***series*** Found {t}.".format(t=title))

		url = s.xpath("./@href")[0]
		thumb_url = s.xpath("./../div/a[@class='banner']/img/@src")[0]
		
		oc.add(
			DirectoryObject(
				key = Callback(GetSeasons, path=BASE_URL + url, title=title, thumb_url=thumb_url),
				title = title,
				thumb = Resource.ContentsOfURLWithFallback(url=thumb_url)
			)
		)
		Log.Debug("***series*** Added {t} to the DirectoryObject.".format(t=title))

	# sort our shows into alphabetical order here
	oc.objects.sort(key = lambda obj: obj.title)

	return oc

####################################################################################################
@route('/video/diy/seasons')
def GetSeasons(path, title, thumb_url):

	oc = ObjectContainer(title2=title)
	html = HTTP.Request(path).content
	matches = VPLAYER_MATCHES.search(html)

	# grab the current season link and title only on this pass, grab each season's actual shows in GetShows()
	try:
		show_id = matches.group(1)
		xml = HTTP.Request('http://www.diynetwork.com/diy/channel/xml/0,,%s,00.xml' % show_id).content.strip()
		xml = RE_AMPERSAND.sub('&amp;', xml)
		title = XML.ElementFromString(xml).xpath("//title/text()")[0].strip()

		oc.add(
			DirectoryObject(
				key = Callback(GetShows, path=path, title=title),
				title = title,
				thumb = Resource.ContentsOfURLWithFallback(url=thumb_url)
			)
		)
		Log.Debug("***season*** Added {t} to the DirectoryObject.".format(t=title))
	except:
		pass

	# now try to grab any additional seasons/listings via xpath
	data = HTML.ElementFromURL(path)

	for season in data.xpath("//ul[@class='channel-list']/li"):
		try:
			title = season.xpath("./h4/text()")[0].strip()
			url = season.xpath("./div/div[@class='crsl-wrap']/ul/li[1]/a/@href")[0]

			oc.add(
				DirectoryObject(
					key = Callback(GetShows, path= BASE_URL + url, title=title),
					title = title,
					thumb = Resource.ContentsOfURLWithFallback(url=thumb_url)
				)
			)
			Log.Debug("***addtnlSeason*** Added {t} to the DirectoryObject.".format(t=title))
			
		except:
			pass

	if len(oc) < 1:
		oc = ObjectContainer(header="Sorry", message="This section does not contain any videos")

	return oc

####################################################################################################
@route('/video/diy/shows')
def GetShows(path, title):

	oc = ObjectContainer(title2=title)
	html = HTTP.Request(path).content
	matches = VPLAYER_MATCHES.search(html)

	show_id = matches.group(1)
	xml = HTTP.Request('http://www.diynetwork.com/diy/channel/xml/0,,%s,00.xml' % show_id).content.strip()
	xml = RE_AMPERSAND.sub('&amp;', xml)

	for c in XML.ElementFromString(xml).xpath("//video"):
		try:
			title = c.xpath("./clipName")[0].text.strip()
			duration = Datetime.MillisecondsFromString(c.xpath("./length")[0].text)
			desc = c.xpath("./abstract")[0].text
			video_id = c.xpath("./videoId")[0].text
			thumb_url = c.xpath("./thumbnailUrl")[0].text.replace('_92x69.jpg', '_480x360.jpg')

			oc.add(
				EpisodeObject(
					url = VIDEO_URL % (video_id, show_id),
					title = title,
					duration = duration,
					summary = desc,
					thumb = Resource.ContentsOfURLWithFallback(url=thumb_url)
				)
			)
			Log.Debug("***episode*** Added {t} to the EpisodeObject.".format(t=title))
		except:
			pass

	if len(oc) < 1:
		oc = ObjectContainer(header="Sorry", message="This section does not contain any videos")

	return oc
