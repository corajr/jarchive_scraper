from bs4 import BeautifulSoup
import scraperwiki
import datetime
import time
import re
import sys

seasons_url = 'http://www.j-archive.com/listseasons.php'
base_url = 'http://www.j-archive.com/'

def scrape_all_seasons(url):

    soup = BeautifulSoup(scraperwiki.scrape(url))
    
    #Grab all of the seasons listed
    seasons = soup.find('div', {"id":"content"}).find_all('a', limit=3)
    for season in seasons:
        scrape_season(base_url+season['href'])

def scrape_season(url):
    
    soup = BeautifulSoup(scraperwiki.scrape(url))
    
    #Grab the div that contains the content and search for any links
    episodes = soup.find('div', {"id":"content"}).findAll('a',{"href":re.compile('showgame\.php')})
    for episode in episodes:
        
        ep_data = episode.text.split(',')
        ep_num = ep_data[0][1:]

        #Fuck this is messy
        air_data = ep_data[1].replace(u'\xa0', '-').split('-')[1:]
        air_date = datetime.date (int(air_data[0]), int(air_data[1]), int(air_data[2]))
        timestamp = time.mktime(air_date.timetuple())

        scrape_episode(episode['href'], ep_num, timestamp)

def scrape_episode(url, episode, air_date):
    
    soup = BeautifulSoup(scraperwiki.scrape(url))

    allCategories = soup.findAll('td', {"class" : "category_name"})
    cats = [] # List of categories without any html
    for cat in allCategories:
        cats.append(cat.text)

    allClues = soup.findAll(attrs={"class" : "clue"})
    for clue in allClues:

        clue_attribs = get_clue_attribs(clue, cats)
        if clue_attribs:
            clue_attribs['air_date'] = air_date
            clue_attribs['episode'] = episode

            #a shitty unique id but it should do
            clue_attribs['uid'] = str(episode)+clue_attribs['category']+str(clue_attribs['dollar_value'])
            scraperwiki.sql.save(['uid'], clue_attribs)
            

def extract_mouseover(parent):
    mouseover_js = parent['onmouseover'].split(",", 2)
    answer_soup = BeautifulSoup(mouseover_js[2])
    answer = answer_soup.find('em', {"class" : re.compile("correct_response")}).text

    clue_props = mouseover_js[1].split("_") #contains the unique ID of the clue for this specific game
                                            #format: clue_["DJ"||"J"]_[Category(1-6)]_[Row(1-5)]||clue_["FJ"]
    return answer, clue_props

def get_clue_attribs(clue, cats):
    #Because of the way jarchive hides the answers to clues
    #this is here to keep things a bit more tidy
    div = clue.find('div')
    
    if div: # J or DJ
        answer, clue_props = extract_mouseover(div)                                   
        cat_n = int(clue_props[2])-1
        #Are we in double jeopardy?

        if clue_props[1] == "J":
            cat = cats[cat_n]
        elif clue_props[1] == "DJ":
            cat = cats[cat_n+6]

        dollar_value = clue.find(attrs={"class" : re.compile('clue_value*')}).text
    else: # FJ
        parent = clue.find_parent('table', {"class": 'final_round'})
        if parent is None:
            print clue.prettify()
            sys.exit(1)
            return None
        answer, clue_props = extract_mouseover(parent.find('div'))
        cat = cats[-1]
        dollar_value = "FJ"

    clue_text = clue.find(attrs={"class" : "clue_text"}).text
        
    return {"answer" : answer, "category" : cat, "text" : clue_text, "dollar_value": dollar_value}

if __name__ == '__main__':
    scrape_all_seasons(seasons_url)
