import itertools
import math
import requests
import pandas as pd
from typing import List, Tuple

# Step 1: Get exchange rate data for a wide list of currencies
currencies = [
    'USD', 'EUR', 'JPY', 'GBP', 'CHF', 'CAD', 'AUD', 'NZD', 'INR', 'CNY', 'NOK',
    'SEK', 'SGD', 'BRL', 'MXN', 'ZAR', 'HKD', 'KRW', 'TRY', 'RUB', 'PLN', 'CZK',
    'HUF', 'DKK', 'THB', 'MYR', 'IDR', 'PHP', 'TWD', 'ILS'
]

# Fetch all conversion rates using ExchangeRate.host
def fetch_all_rates(base: str) -> dict:
    url = f"https://api.exchangerate.host/latest?base={base}"
    try:
        response = requests.get(url)
        data = response.json()
        return data['rate']
    except Exception as e:
        print(f"Failed to fetch rates for base {base}: {e}")
        return {}

# Create the conversion matrix: a dictionary of dictionaries
conversion_matrix = {}
for base in currencies:
    rates = fetch_all_rates(base)
    conversion_matrix[base] = {k: v for k, v in rates.items() if k in currencies}

# Step 2: Transform the graph: use -log(rate) as weights
def log_transform_matrix(matrix: dict) -> dict:
    transformed = {}
    for src in matrix:
        transformed[src] = {}
        for dst in matrix[src]:
            rate = matrix[src][dst]
            if rate > 0:
                transformed[src][dst] = -math.log(rate)
            else:
                transformed[src][dst] = float('inf')
    return transformed

log_graph = log_transform_matrix(conversion_matrix)

# Step 3: Use Bellman-Ford to detect negative cycles (arbitrage)
def detect_arbitrage(graph: dict, start: str) -> List[Tuple[List[str], float]]:
    vertices = list(graph.keys())
    distance = {v: float('inf') for v in vertices}
    predecessor = {v: None for v in vertices}
    distance[start] = 0

    for _ in range(len(vertices) - 1):
        for u in graph:
            for v in graph[u]:
                if distance[u] + graph[u][v] < distance[v]:
                    distance[v] = distance[u] + graph[u][v]
                    predecessor[v] = u

    # Detect negative cycle
    for u in graph:
        for v in graph[u]:
            if distance[u] + graph[u][v] < distance[v]:
                # Reconstruct the negative cycle
                cycle = []
                curr = v
                visited = set()
                while curr not in visited:
                    visited.add(curr)
                    curr = predecessor[curr]
                cycle_start = curr
                cycle.append(curr)
                curr = predecessor[curr]
                while curr != cycle_start:
                    cycle.append(curr)
                    curr = predecessor[curr]
                cycle.append(cycle_start)
                cycle.reverse()
                return [(cycle, distance[cycle[-1]])]
    return []

# Run arbitrage detection from each currency
arbitrage_opportunities = []
for currency in currencies:
    result = detect_arbitrage(log_graph, currency)
    if result:
        arbitrage_opportunities.extend(result)

# Convert results into a readable format
opportunity_data = []
for path, weight in arbitrage_opportunities:
    profit = math.exp(-weight) - 1
    opportunity_data.append({
        "Cycle": " → ".join(path),
        "Profit %": round(profit * 100, 4)
    })

df = pd.DataFrame(opportunity_data)
import ace_tools as tools; tools.display_dataframe_to_user(name="Arbitrage Opportunities", dataframe=df)
