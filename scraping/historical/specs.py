"""

    1. Data points to scrape
        - Teams stats: goals stats, events stats and wdl stats
        - H2H stats: date, gf(home goals), ga(away goals), venue(hh or aa)
        - Recent stats: date, gf, ga, teams names, odds
        - Fixture stats: date, league, kickoff, odds, league stats
        - HINT: for overall stats append 0 at the end of the key, for home 1 and away 2.
        - HINT: for home stats append h as prefix while for away a.
        - e.g h_over15_0 means

    2. Return a csv file with h2h and prev_matches cols as json object

    3. Proposed method for scraping
        - Get the fixture url and parse the desired data from that page
        - For recent matches, compare the opp team against the list of teams in the league to validate
            league matches.
        - Improvise a smart method of detecting the page structure to know which parser to use.

"""