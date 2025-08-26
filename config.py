# config.py
DEFAULT_USER_AGENT = "ishavarrier@address.com"

COMPANY_REVENUE_PREFERENCES = {
    "Intel": ["RevenueFromContractWithCustomerExcludingAssessedTax"],
    "Texas Instruments": ["RevenueFromContractWithCustomerExcludingAssessedTax","SalesRevenueNet"],
    "Apple": ["SalesRevenueNet"],
    "Microsoft": ["SalesRevenueNet"],
    "Google": ["Revenues"],
    "Alphabet": ["Revenues"],
    "Amazon": ["SalesRevenueNet"],
    "Tesla": ["SalesRevenueNet"],
    "NVIDIA": ["RevenueFromContractWithCustomerExcludingAssessedTax"],
}

DEFAULT_REVENUE_TAGS = [
    "RevenueFromContractWithCustomerExcludingAssessedTax",
    "SalesRevenueNet", "Revenues",
    "SalesRevenueGoodsNet", "SalesRevenueServicesNet",
]

COMMON_TAGS = {
    "Gross Profit": "GrossProfit",
    "Net Income": "NetIncomeLoss",
    "Cash Flow": "NetCashProvidedByUsedInOperatingActivities",
}

DEFAULT_COMPANIES = [
    "INTEL CORP", "Marvell Technology, Inc.", "CISCO SYSTEMS, INC.",
    "AMPHENOL CORP /DE/",
    "QUALCOMM INC/DE", "Broadcom Inc.", "NVIDIA CORP",
]


DEFAULT_MARKETS = [
    "Industrial",
    "Automotive",
    "Personal electronics",
    "Communications equipment",
    "Enterprise systems",
    "Calculators",
]
