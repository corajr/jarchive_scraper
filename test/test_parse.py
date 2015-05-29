import urlparse
import urllib
import scraperwiki
import os
from scraper import *

conn = None
curs = None

def path2url(path):
    path = os.path.abspath(path)
    return urlparse.urljoin(
      'file:', urllib.pathname2url(path))


def check_sql_for(uid):
    count = scraperwiki.sql.execute(
        'SELECT count(*) FROM swdata WHERE uid = ?', (uid,))
    return count['data'][0] > 0


def test_scrape_episode():
    episode = path2url('test/sample_show.html')
    scrape_episode(episode, '7079', 1432785600)
    assert check_sql_for('7079PSYCHOLOGY$1600')
    assert check_sql_for("7079BOOKS' FIRST LINES$400")
    assert check_sql_for('7079AMERICAN LITERATUREFJ')
