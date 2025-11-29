
import sqlite3
import os 
from datetime import datetime, timedelta
import math


TABLE_SCHEMAS = {
    "bitcoin_data": ["price","volume","marketCap","availableSupply","totalSupply",
                     "fullyDilutedValuation","priceChange1h","priceChange1d","priceChange1w"],
    "eth_data":     ["price","volume","marketCap","availableSupply","totalSupply",
                     "fullyDilutedValuation","priceChange1h","priceChange1d","priceChange1w"],
    "market_data":  ["marketCap","volume","btcDominance","marketCapChange","volumeChange",
                     "btcDominanceChange","fear_greed_value","fear_greed_name"],
    # add the other 6 tables here
}


def correct_table(table):
    with sqlite3.connect('crypto_data.sqlite') as conn:
        cursor = conn.cursor()
        cursor.execute(f'SELECT * FROM {table}')
        rows = cursor.fetchall()
        columns = TABLE_SCHEMAS[table]

        prev_t = None
        prev_values = {}
        for row_index, row in enumerate(rows):
            time = row[0]
            dt = datetime.strptime(str(time), "%Y-%m-%d %H:%M:%S.%f%z")

            if prev_t is not None:
                gap = dt - prev_t
                if gap > timedelta(minutes=6):
                    missing_rows = math.ceil(gap.total_seconds() / 300)  # 300s = 5min

                    # --- compute diffs between current and previous row ---
                    diffs = {}
                    for idx, col in enumerate(columns, start=1):
                        val = row[idx]
                        prev_val = prev_values.get(col)
                        if prev_val is not None and isinstance(val, (int, float)):
                            diffs[col] = val - prev_val
                        else:
                            diffs[col] = None

                    # --- interpolate missing rows ---
                    for i in range(1, missing_rows):
                        date = prev_t + timedelta(minutes=5 * i)
                        interpolated = []
                        for idx, col in enumerate(columns, start=1):
                            prev_val = prev_values.get(col)
                            diff = diffs[col]
                            if diff is not None:
                                interpolated.append(prev_val + (diff / missing_rows) * i)
                            else:
                                interpolated.append(prev_val)
                        cursor.execute(f"""
                            INSERT INTO {table} (date,{",".join(columns)})
                            VALUES ({",".join(["?"] * (len(columns) + 1))})
                        """, [date.strftime("%Y-%m-%d %H:%M:%S.%f")] + interpolated)

            # --- update prev_t and prev_values for next iteration ---
            prev_t = dt
            for idx, col in enumerate(columns, start=1):
                prev_values[col] = row[idx]

tables = ['bitcoin_data', 'eth_data', 'market_data']

for table in tables:
    correct_table(table)