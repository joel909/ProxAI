def crawl_website(website,app,):
    results = app.scrape(website)
    print("crawl_website results:", results)
    return results
