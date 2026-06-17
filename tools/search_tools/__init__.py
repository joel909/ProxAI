from firecrawl import Firecrawl
import sys


YELLOW = "\033[33m"
BLUE = "\033[34m"
RESET = "\033[0m"
CLEAR_LINE = "\r\033[K"


class FireCrawlTool:
    def __init__(self, api_key=None):
        if api_key is None:
            import os

            api_key = os.environ.get("FIRECRAWL_API_KEY")

        self.app = Firecrawl(api_key=api_key)

    def search(self,queries,limit=20):
        # print("searching for queries:", queries)
        results = []
        for query in queries:
            sys.stdout.write(f"{CLEAR_LINE}{YELLOW}searching for:{RESET} {BLUE}{query}{RESET}")
            sys.stdout.flush()
            search_result = self.app.search(query, limit=limit)
            sys.stdout.write(CLEAR_LINE)
            sys.stdout.flush()
            results.append({query: "result is : \n" + str(search_result)})
        return results
