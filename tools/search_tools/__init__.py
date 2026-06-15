class FireCrawlTool:
    def __init__(self, api_key=None):
        from firecrawl import Firecrawl

        if api_key is None:
            import os

            api_key = os.environ.get("FIRECRAWL_API_KEY")

        self.app = Firecrawl(api_key=api_key)

    def search(self,queries,limit=20):
        results = []
        for query in queries:
            search_result = self.app.search(query, limit=limit)
            results.append({query: "result is : \n" + str(search_result)})
        return results
