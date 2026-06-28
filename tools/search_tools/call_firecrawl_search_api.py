def raw_search(query,app,limit=20):
    results = app.search(query, limit=limit)
    return results
