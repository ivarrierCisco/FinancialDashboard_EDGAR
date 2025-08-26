# services/sec_api.py 
#This file handles interactions with the SEC EDGAR API to fetch company financial data.
import requests
from typing import Dict, List, Optional
from config import DEFAULT_USER_AGENT, COMPANY_REVENUE_PREFERENCES, DEFAULT_REVENUE_TAGS

class SECDataFetcher:
    def __init__(self, user_agent: str = DEFAULT_USER_AGENT):
        self.headers = {"User-Agent": user_agent}
        self._cik_cache: Dict[str,str] = {}
        self._company_list_cache: Optional[List[Dict]] = None

    def get_company_list(self) -> List[Dict]:
        if self._company_list_cache is not None:
            return self._company_list_cache
        url = "https://www.sec.gov/files/company_tickers.json"
        r = requests.get(url, headers=self.headers, timeout=30)
        r.raise_for_status()
        raw = r.json()
        companies = [{
            "name": v["title"],
            "ticker": v["ticker"],
            "cik": str(v["cik_str"]).zfill(10)
        } for v in raw.values()]
        companies.sort(key=lambda x: x["name"])
        self._company_list_cache = companies
        return companies

    def get_company_cik(self, company_name: str) -> Optional[str]:
        if company_name in self._cik_cache:
            return self._cik_cache[company_name]
        for c in self.get_company_list():
            if c["name"] == company_name:
                self._cik_cache[company_name] = c["cik"]
                return c["cik"]
        return None

    def test_tag_availability(self, cik: str, tag: str) -> bool:
        url = f"https://data.sec.gov/api/xbrl/companyconcept/CIK{cik}/us-gaap/{tag}.json"
        r = requests.get(url, headers=self.headers, timeout=30)
        return r.status_code == 200

    def best_revenue_tag(self, company_name: str, cik: str) -> str:
        prefs = COMPANY_REVENUE_PREFERENCES.get(company_name, [])
        for t in prefs + DEFAULT_REVENUE_TAGS:
            if self.test_tag_availability(cik, t):
                return t
        return "SalesRevenueNet"

    def fetch_concept(self, cik: str, tag: str) -> Optional[Dict]:
        url = f"https://data.sec.gov/api/xbrl/companyconcept/CIK{cik}/us-gaap/{tag}.json"
        r = requests.get(url, headers=self.headers, timeout=30)
        if r.status_code == 200:
            return r.json()
        return None
