
import sqlite3
import os 
from datetime import datetime, timedelta
import math
import contextlib

DATASETS_DIR = os.path.join(os.path.dirname(__file__), 'datasets')

TABLE_SCHEMAS = {
    "bitcoin_data": ["price","volume","marketCap","availableSupply","totalSupply",
                     "fullyDilutedValuation","priceChange1h","priceChange1d","priceChange1w"],
    "eth_data":     ["price","volume","marketCap","availableSupply","totalSupply",
                     "fullyDilutedValuation","priceChange1h","priceChange1d","priceChange1w"],
    "market_data":  ["marketCap","volume","btcDominance","marketCapChange","volumeChange",
                     "btcDominanceChange","fear_greed_value","fear_greed_name"],
    # add the other 6 tables here
}


def add_missing_rows(table, DB_PATH):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(f'SELECT * FROM {table} ORDER BY date')
        rows = cursor.fetchall()
        columns = TABLE_SCHEMAS[table]

        prev_t = None
        prev_values = {}
        for row in rows:
            time = row[0]
            dt = datetime.fromisoformat(time)

            if prev_t is not None:
                gap = dt - prev_t
                if gap >= timedelta(minutes=5, seconds=20):
                    missing_rows = math.floor(gap.total_seconds() / 300) - 1  # 300s = 5min

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
                    for i in range(1, missing_rows + 1):
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
                        """, [date.isoformat()] + interpolated)

            # --- update prev_t and prev_values for next iteration ---
            prev_t = dt
            for idx, col in enumerate(columns, start=1):
                prev_values[col] = row[idx]



def interpolate_rows(table, DB_PATH):
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


def start():
    valid = sorted([f for f in os.listdir(DATASETS_DIR) if f.endswith('.sqlite')])
    if len(valid) == 0:
        print('No valid db in the datasets dir ... aborting ...')
        os._exit(1)
    print('\nChoose a database index to proceed : \n')
    for i, v in enumerate(valid):
        print(f'{i}    {v}')

    print('\n')
    while True:
        choice = input('Choice : ')
        try:
            index = int(choice.strip().lower())
            file_name = valid[index]
            break
        except:
            print('Index out of range , try again ...\n')
            continue

    DB_PATH = os.path.join(DATASETS_DIR, file_name)

    for table in tables:
        print('Interpolating NULL rows ...')
        print(DB_PATH)
        interpolate_rows(table, DB_PATH)
        print('Adding Missing rows ...')
        add_missing_rows(table, DB_PATH)

start()