import pandas as pd
import os
import sqlite3
import contextlib
import csv

### EXPORT the 3 tables to csv and run this script in the same folder ###
small_intervals = {'market_data.csv': [], 'bitcoin_data.csv': [], 'eth_data.csv': []}

MAIN_DIR = os.path.dirname(__file__)
DB_PATH = os.path.join(os.path.dirname(__file__), 'crypto_data.sqlite')


def analyze_intervals(csv_path, expected_minutes=5, tolerance_seconds=30):
    global small_intervals

    # CONVERT CSV TO DATAFRAME
    df = pd.read_csv(csv_path)

    # CONVERT DATE ROW TO DATETIME OBJECTS
    df['date'] = pd.to_datetime(df['date'], errors='coerce')

    # Drop rows where date could not be parsed
    df = df.dropna(subset=['date'])

    ### DROP TABLE INDEX AND SORT BY DATE
    df = df.sort_values('date').reset_index(drop=True) 

    # Compute differences
    df['diff'] = df['date'].diff()

    expected = pd.Timedelta(minutes=expected_minutes)
    tolerance = pd.Timedelta(seconds=tolerance_seconds)

    # Too short (< expected - tolerance)
    too_short = df[df['diff'] < (expected - tolerance)]

    # Too long (> expected + tolerance)
    too_long = df[df['diff'] > (expected + tolerance)]

    # BUILD A LIST OF DUPLICATES
    less_than_1s = df[df['diff'] < pd.Timedelta(seconds=5)]
   
    formatted = less_than_1s['date'].dt.strftime("%Y-%m-%d %H:%M:%S.%f%z")
    formatted = formatted.str.replace(r'(\+|\-)(\d{2})(\d{2})$', r'\1\2:\3', regex=True)

    small_intervals[csv_path.split('\\')[-1]] = formatted.tolist()
        

    print("\n=== Interval Analysis ===")
    print(f"Expected interval: {expected}")
    print(f"Tolerance: ±{tolerance}")

    if too_short.empty:
        print("✔ No intervals shorter than expected (within tolerance)")
    else:
        print(f"❗ {len(too_short)} intervals shorter than expected:")
        print(too_short[['date', 'diff']])

    if too_long.empty:
        print("✔ No intervals longer than expected (within tolerance)")
    else:
        print(f"❗ {len(too_long)} intervals longer than expected:")
        print(too_long[['date', 'diff']])

    print("\n=== Summary ===")
    print(f"Total rows: {len(df)}")
    print(f"Intervals < expected: {len(too_short)}")
    print(f"Intervals > expected: {len(too_long)}")

    return df

def make_csv():
    if not os.path.exists(DB_PATH) :
         print("")
         print('No database detected, please ensure you are in the right directory\n')
         print('Program exiting ...')
         os._exit(1)

    with sqlite3.connect(DB_PATH) as conn:
        with contextlib.closing(conn.cursor()) as cur:

            # Get all tables
            cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [row[0] for row in cur.fetchall()]

            for table in tables:
                cur.execute(f"SELECT * FROM {table}")
                rows = cur.fetchall()
                columns = [desc[0] for desc in cur.description]

                csv_path = os.path.join(MAIN_DIR, f"{table}.csv")

                with open(csv_path, "w", newline="", encoding="utf-8") as f:
                    writer = csv.writer(f)
                    writer.writerow(columns)
                    writer.writerows(rows)

                print(f"Exported {table} → {csv_path}")

def delete_less_than_1s_intervals(table):
  table_name = table.split('.')[0]
  with sqlite3.connect(DB_PATH) as conn:
      with contextlib.closing(conn.cursor()) as cur :
          placeholders = ",".join("?" for _ in small_intervals[table])

          sql_command = f'''DELETE FROM {table_name}
                            WHERE date IN ({placeholders});'''
          
          cur.execute(sql_command, [d for d in small_intervals[table]])
      conn.commit()


csv_names = ['market_data.csv', 'bitcoin_data.csv', 'eth_data.csv']
def main():
 try:
    print("")
    print('WELCOME TO FETCH INTERVALS ANALYSIS TOOL')
    print("----------------------------------------\n")

    while True: 
 
    
        choice = input('Start Analyzis ? (y, n) : ')
        if choice.lower().strip() == 'y':
            make_csv()

  
           
            for n in csv_names:
                if os.path.exists(os.path.join(MAIN_DIR, n)):
                    print(f'\n❗❗❗❗❗ Analyzing {n} ... ❗❗❗❗❗ ')
                    analyze_intervals(os.path.join(MAIN_DIR, n))
       
         
            break

        elif choice.lower().strip() == 'n':
            print('Program Exiting ...')
            clear_csv()
            os._exit(0)

        elif choice.lower().strip() != 'y' or choice.lower().strip() != 'n':
            print('\nWrong input, please enter "y" or "n"\n')
            continue
            

  
    if (len(small_intervals['market_data.csv']) > 0 
         or len(small_intervals['bitcoin_data.csv']) > 0 
         or len(small_intervals['eth_data.csv']) > 0):

        while True:
            print("")
       
            choice_2 = input('❗❗ DUPLICATES DETECTED , delete them from the database ? (Y, N)❗❗ : ' )
            if choice_2.lower().strip() == 'y':
                for t in csv_names:
                   print(f'Removing {len(small_intervals[t])} rows from {t.split('.')[0]}...')
                   delete_less_than_1s_intervals(t)
                   
                break


            elif choice_2.lower().strip() == 'n':
                print('\nProgram Exiting ...')
                clear_csv()
                os._exit(0)

            elif choice_2.lower().strip() != 'y' or choice_2.lower().strip() != 'n':
                print('\nWrong input, please enter "y" or "n"')
                continue

      
    clear_csv()

 except KeyboardInterrupt:
    clear_csv()
     
def clear_csv():
    for f in csv_names:
       if os.path.exists(os.path.join(MAIN_DIR ,f)):
          os.remove(os.path.join(MAIN_DIR ,f))
          print("")
          print(f'Cleared {f} from disk')
main()