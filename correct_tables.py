
import sqlite3
import os 
from datetime import datetime, timedelta
import math
import contextlib

DB_PATH = os.path.join(os.path.dirname(__file__), 'crypto_data.sqlite')

TABLE_SCHEMAS = {
    "bitcoin_data": ["price","volume","marketCap","availableSupply","totalSupply",
                     "fullyDilutedValuation","priceChange1h","priceChange1d","priceChange1w"],
    "eth_data":     ["price","volume","marketCap","availableSupply","totalSupply",
                     "fullyDilutedValuation","priceChange1h","priceChange1d","priceChange1w"],
    "market_data":  ["marketCap","volume","btcDominance","marketCapChange","volumeChange",
                     "btcDominanceChange","fear_greed_value","fear_greed_name"],
    # add the other 6 tables here
}


def add_missing_rows(table):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(f'SELECT * FROM {table} ORDER BY date')
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
                        """, [date.strftime("%Y-%m-%d %H:%M:%S.%f") + date.strftime("%z")[:3] + ":" + date.strftime("%z")[3:]] + interpolated)

            # --- update prev_t and prev_values for next iteration ---
            prev_t = dt
            for idx, col in enumerate(columns, start=1):
                prev_values[col] = row[idx]



def interpolate_rows(table):
    with sqlite3.connect(DB_PATH) as conn:
        with contextlib.closing(conn.cursor()) as cur:
            rows_query = f'SELECT * FROM {table} ORDER BY date'
            cur.execute(rows_query)
            rows = cur.fetchall()

            first = None
            last = None
            rows_in_between = []
            invalid_row_detected = False
            sql_query_string = "=? ,".join(TABLE_SCHEMAS[table]) + '=?'
          

            last_row = None
            for row in rows:
                
                if row[1] is not None: 
                    if invalid_row_detected:
                        last = row
                        print(f'Fist Valid row : {first[0]} ')
                        print(f'Last valid row : {last[0]} ')
                       
                        number_of_null_row = len(rows_in_between)
            
                        diffs = {}

                        for idx , col in enumerate(TABLE_SCHEMAS[table], start=1):
                            try: 
                               diffs[idx] = round(float(last[idx] - float(first[idx])), 5)
                            except:
                                diffs[idx] = first[idx]

                        print(diffs)
                        

                        for idx, date in enumerate(rows_in_between, start=1):
                    
                          new_values = []
                          for n in range(len(TABLE_SCHEMAS[table])):
                           
                              if isinstance(diffs[n + 1], float):
                                new_val = first[n + 1] + ((diffs[n + 1] / (number_of_null_row + 1)) * idx)
                                new_values.append(new_val)
                              else:
                                  new_val = diffs[n + 1]
                                  new_values.append(new_val)
                          print(f'New values: {new_values}')

                          cur.execute(f'''UPDATE {table} SET {sql_query_string} 
                                          WHERE date=?''', new_values + [date])

                      
                        invalid_row_detected = False
                        rows_in_between = []

                    else:
                     
                       first = row
  
                if table == 'market_data' and not row[8]:
                    cur.execute(f'''UPDATE {table} SET fear_greed_value=?, fear_greed_name=? 
                                          WHERE date=?''', [last_row[7]] + [last_row[8]] + [row[0]])
                if table == 'market_data' and row[8]:
                    last_row = row

                if row[1] is None:
                    invalid_row_detected = True
                    print(f'Detected row {row[0]} as NULL TABLE: {table}')
                    rows_in_between.append(row[0])

tables = ['bitcoin_data', 'eth_data', 'market_data']


for table in tables:
    print('Interpolating NULL rows ...')
    interpolate_rows(table)
    print('Adding Missing rows ...')
    add_missing_rows(table)