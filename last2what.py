# -*- coding: utf_8 -*-

__author__="devilcius"
__date__ ="$Oct 23, 2010 11:21:12 PM$"

import whatapi
import pylast
import time
import re
import shelve
import sys
import getopt
import ConfigParser


#params
config = ConfigParser.ConfigParser()
config.read('last2what.cfg')

API_KEY = config.get("last", "apikey")
what_cd_user = config.get("what", "username")
what_cd_pwd = config.get("what", "password")
proxy_enabled = config.getboolean("connection", "proxyenabled")
proxy_server = config.get("connection", "proxyserver")
proxy_port = config.get("connection", "proxyport")


#global
whatartist = None


class Artists():
    pass


def waitingDots (secs):
    """creates a line of dot, one by one, one dot per second.
    # Parameters:
        * secs int: number of seconds
    """
    for i in range(secs):
        sys.stdout.write(".")
        time.sleep(1)

def setArtistChecked(id,updated,existed):
    """Sets the what.cd artist checked in last2what.
    # Parameters:
        * id string: artist's id
        * updated int: 1 if artist updated by last2what, 0 if not
        * existed int: 1 if artist info already existed in what.cd, 0 if not
    """
    shelf = shelve.open('checked_artists')
    try:
        shelf[id] = {'updated':updated, 'existed':existed}
    finally:
        shelf.close()

def isArtistChecked(id):
    """Returns true if the what.cd's artist has already been checked by last2what.
    # Parameters:
        * id string: what.cd's artist id
    """
    shelf = shelve.open('checked_artists')
    try:
        return id in shelf.keys()
    finally:
        shelf.close()

def removeHTMLTags(data):
    """Removes all HTML tags from a given string.
    # Parameters:
        * data string: string to parse
    """
    p = re.compile(r'<.*?>')
    return p.sub('', data)

def removeBrackets(data):
    """Removes all HTML tags from a given string.
    # Parameters:
        * data string: string to parse
    """
    p = re.compile(r'\(.*?\)')
    return p.sub('', data)

def updateWhatCDArtistInfo(id, info):
    """Updates what.cd's artist info.
    # Parameters:
        * id str: artist's id
        * info str: artist's info.
    """
    if info[0]:
        if whatartist.setArtistInfo(id, info) == 1:
            return True
        else:
            return False

def getArtistInfoFromLastFm(artist):
    """Returns a tuple with last.fm's artist info (info, image).
    # Parameters:
        * artist str: artist name
    """
    info = []
    lfm_network = pylast.LastFMNetwork(api_key = API_KEY)
    if proxy_enabled:
        lfm_network.enable_proxy(host=proxy_server, port = proxy_port)
    #workaround to pylast bug with brackets in artist name
    lfm_artist = lfm_network.get_artist(removeBrackets(artist))
    try:
        if lfm_artist.get_bio_content():
            info.append(removeHTMLTags(lfm_artist.get_bio_content()))
        else:
            info.append(None)
        if lfm_artist.get_cover_image():
            info.append(lfm_artist.get_cover_image())
        else:
            info.append(None)
    except Exception as inst:
        print 'error while retrieving %s info from last.fm, skipping...' % artist
        print inst.args      # arguments stored in .args
        info.append(None)
        info.append(None)
    
    return info


def getArtistsFromUser(what, user, list, page=1):
    """Returns a list of tuples with artist name and artist id.
    # Parameters:
        * what object: what.cd object
        * user str: what.cd user name.
        * list str: list of torrents. Values: {'u':uploaded,'d':snatched,'s':seeding}
    """
    artists = Artists()
    found =[]
    whatuser = what.getUser(user)
    total_pages = 0
    #which list of torrents?
    if list == 'uploaded':
        torrents = whatuser.getTorrentsUploaded(page)
    elif list == 'seeding':
        torrents = whatuser.getTorrentsSeeding(page)
    elif list == 'downloaded':
        torrents = whatuser.getTorrentsSnatched(page)

    for torrent in torrents:
        if total_pages < 1:
            total_pages = torrents[0]['pages']
        if torrent['artist'][0] == 'Various Artists':
            pass
        elif len(torrent['artist']) > 1:
            #if 2 artists per torrent
            found.append((torrent['artist'][0], torrent['artistid'][0]))
            found.append((torrent['artist'][1], torrent['artistid'][1]))
        else:
            found.append((torrent['artist'][0], torrent['artistid'][0]))

    artists.pages = total_pages
    artists.result = found

    return artists

def checkArtists(list):
    """Main function. Checks if what.cd's artist has info, if not it checks it in last.fm and,
        if found, it updates what.cd
    # Parameters:
        * list list: what.cd artist list to check. One list per torrent page.
    """
    global whatartist
    for artist in list:
        if not isArtistChecked(str(artist[1])):
            print "getting %s's info from what.cd..." % artist[0]
            whatartist = whatcd.getArtist(artist[0].encode('utf-8'))
            artistinfo = whatartist.getArtistInfo()
            if len(artistinfo) < 1:
                print '...not found in what...'
                if getArtistInfoFromLastFm(artist[0])[0]:
                    print "...but found in last fm!"
                    print "updating now what.cd artist (%s)..." % (artist[1])
                    if updateWhatCDArtistInfo(str(artist[1]), getArtistInfoFromLastFm(artist[0])):
                        print "...done!"
                        setArtistChecked(str(artist[1]), 1, 0)
                    else:
                        print "what.cd update failed... Network down?"
                else:
                    print "...neither in last.fm, skipping"
                    setArtistChecked(str(artist[1]), 0, 0)
            else:
                print "...found in what.cd, skipping."
                setArtistChecked(str(artist[1]), 0, 1)
            print "Now let's wait 5 seconds, noblesse oblige."
            waitingDots(5)
            print "\n"
        else:
            print "artist %s already checked, skipping..." % artist[0]
            

def displayHelp():
    print "usage: python last2what.py [option] [arg]\n"\
        "-h     : print this help message and exit (also --help)\n"\
        "-l arg : updates artist info from a given list (also --list).\n"\
        "Args:\n"\
            "       uploaded: upload list\n"\
            "       downloaded: snatched list\n"\
            "       seeding: seeding list\n"\
            "-u arg : (mandatory) updates artist info from a given user (also --user).\n"\
        "Arg: what.cd username\n"\
        "--stats    : print stats and exits\n"\
        "Example    :python last2what.py -l uploaded -u devilcius"

    exit()

def showStats():
    s = shelve.open('checked_artists')
    checked = 0
    updated = 0
    existed = 0
    print "---------------- STATS ------------------\n"
    for key in s.keys():
        if s[key]['updated'] == 1:
            #print "updated artist's id: %s" % key
            updated = updated + 1
        else:
            if  s[key]['existed'] == 1:
                existed = existed + 1
        checked = checked + 1
    print "checked %d artists, updated: %d, already in what: %d" % (checked, updated, existed)
    print "-----------------------------------------"

    exit()


if __name__ == "__main__":

    list,user = ('u','')
    try:
        opts, extraparams = getopt.getopt(sys.argv[1:], 'l:u:s:h',['list','user','stats','help'])
    except:
        print 'unknown argument or missing value, quitting...\nType "python last2what.py -h" for help'
        exit()

    if not opts:
        print "you didn't provide an option "\
            "\ntry python last2what.py -h for more information"
        exit()

    for o,p in opts:
        if o in ('-h', '--help'):
            displayHelp()
        elif o in ('-l', '--list'):
            list = p
        elif o in ('-u', '--user'):
            user = p
        elif o in ('-s', '--stats'):
            showStats()

    whatcd = whatapi.getWhatcdNetwork(what_cd_user, what_cd_pwd)
    if proxy_enabled:
        whatcd.enableProxy(host=proxy_server, port = proxy_port)
    whatcd.enableCaching()
    pages = getArtistsFromUser(whatcd, user, list).pages
    pages_checked = 0
    artist_list = None
    while int(pages_checked) < int(pages):
        pages_checked = pages_checked + 1
        print "retrieving artist list from what.cd..."
        artist_list = getArtistsFromUser(whatcd, user,list, pages_checked).result
        print "...done!\nProceed to check:"
        print "=> page %d of %s" % (pages_checked, pages)
        checkArtists(artist_list)

    print "All done!\nBye"
