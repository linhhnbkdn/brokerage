#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'be.settings')
django.setup()

from exchange.models import MarketDataSnapshot
from decimal import Decimal

# Check market data
print(f"Market data records: {MarketDataSnapshot.objects.count()}")

# Get latest 10 records
latest = MarketDataSnapshot.objects.all().order_by('-timestamp')[:10]
if latest:
    print("\nLatest market data:")
    for snapshot in latest:
        print(f"{snapshot.symbol}: ${snapshot.price} (Change: {snapshot.change_percent}%) at {snapshot.timestamp}")
else:
    print("No market data found")

# Show all symbols with data
symbols = MarketDataSnapshot.objects.values_list('symbol', flat=True).distinct()
print(f"\nSymbols with data: {list(symbols)}")