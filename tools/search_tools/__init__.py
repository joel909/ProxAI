from firecrawl import Firecrawl
import sys

from storage.tool_credentials import get_tool_api_key


YELLOW = "\033[33m"
BLUE = "\033[34m"
RESET = "\033[0m"
CLEAR_LINE = "\r\033[K"


class FireCrawlTool:
    def __init__(self, api_key=None):
        if api_key is None:
            api_key = get_tool_api_key("firecrawl")

        self.api_key = api_key
        self.app = None

    def get_app(self):
        if not self.api_key:
            raise RuntimeError("Firecrawl API key is not configured. Run /setup-tools to set it up.")

        if self.app is None:
            self.app = Firecrawl(api_key=self.api_key)

        return self.app

    def search(self,queries,limit=20):
        # print("searching for queries:", queries)
        app = self.get_app()
        results = []
        for query in queries:
            sys.stdout.write(f"{CLEAR_LINE}{YELLOW}searching for:{RESET} {BLUE}{query}{RESET}")
            sys.stdout.flush()
            try:
                search_result = app.search(query, limit=limit)
            finally:
                sys.stdout.write(CLEAR_LINE)
                sys.stdout.flush()
            results.append({query: "result is : \n" + str(search_result)})
        return results
    def crawl(self,websites):
        app = self.get_app()
        results = []
        for website in websites:
            sys.stdout.write(f"{CLEAR_LINE}{YELLOW}crawling website:{RESET} {BLUE}{website}{RESET}")
            sys.stdout.flush()
            try:
                crawl_result = app.scrape(website)
            finally:
                sys.stdout.write(CLEAR_LINE)
                sys.stdout.flush()
            results.append({website: "result is : \n" + str(crawl_result)})
        return results
