import psycopg2
import os 

# Setting env variables windows : SET X = X
PGHOST=os.getenv("PGHOST")
PGPORT=os.getenv("PGPORT")
PGUSER=os.getenv("PGUSER")
PGDATABASE=os.getenv("PGDATABASE")
PGPASSWORD=os.getenv("PGPASSWORD") 


def which_table():
    """
    Prompts the user to select a target database table for data correction.

    Offers a menu of options including specific tables (`bitcoin_data`, `eth_data`, `market_data`),
    the option to apply changes to all tables, or to exit the program.

    Returns:
        str: The name of the selected table.
            - 'bitcoin_data'
            - 'eth_data'
            - 'market_data'
            - 'all' (to process every table)
        
    Side Effects:
        - Displays a menu to the console.
        - Prompts the user for input.
        - Terminates the program with exit code 0 if the user selects Exit (option 5).

    Raises:
        None: All input validation is handled internally. Prompts the user again on invalid input.
    """
    print("\nTables:")
    print("1. bitcoin_data")
    print("2. eth_data")
    print("3. market_data")
    print("4. All")
    print("5. Exit\n")

    while True:
            

            try:
                choice = int(input("Enter a table id : "))

                if choice == 1:
                    table = 'bitcoin_data'
                    return table
                    
                elif choice == 2:
                    table  = 'eth_data'
                    return table

                elif choice == 3:
                    table = 'market_data'
                    return table
                
                elif choice == 4:
                    table = 'all'
                    return table
                
                elif choice == 5:
                    print("Program exiting...")
                    os._exit(0)

                else:
                    print("Invalid id, try again")
                    continue

            except Exception:
                print("Invalid number")
                continue


def which_row():
    """
    Prompts the user to enter the row number they wish to correct.

    Continuously requests input until a valid integer is provided. 
    The row number will typically correspond to a position in an ordered dataset.

    Returns:
        int: The validated row number input by the user.

    Side Effects:
        - Displays prompts and error messages in the console.
        - Handles and reprompts on invalid input types.

    Raises:
        None: All exceptions are caught and handled internally.
    """

    while True: 

        try:
            row = int(input("\nWhich row to correct ?  "))
            return row
        
        except Exception:
            print("Invalid number")



def fill_db(table_name, row_number):
    """
    Fills in missing data for a specified row in a cryptocurrency data table by averaging 
    values from the rows immediately before and after it.

    For `market_data`, it interpolates fields like `marketCap`, `volume`, `btcDominance`, etc.
    For all other tables (e.g. `bitcoin_data`, `eth_data`), it interpolates financial and pricing metrics.

    Args:
        table_name (str): The name of the table to update. Must be one of:
            - 'market_data'
            - 'bitcoin_data'
            - 'eth_data'
        row_number (int): The position (1-based index) of the row to update. This function will 
            use rows `row_number - 1` and `row_number + 1` to compute mean values.

    Returns:
        None

    Side Effects:
        - Connects to `crypto_data.sqlite` database.
        - Executes an UPDATE statement that modifies one row based on surrounding row values.

    Raises:
        sqlite3.Error: If a database access error occurs.
        ValueError: If row_number < 2, which would make interpolation impossible.

    Notes:
        - Relies on SQLite's `rowid` and assumes the table is chronologically ordered by `date`.
        - Does not update non-numeric or textual columns (e.g. labels, timestamps).
    """
    if table_name == 'market_data':

       with psycopg2.connect(
        dbname = PGDATABASE,
        host = PGHOST,
        user = PGUSER,
        port = PGPORT,
        password =PGPASSWORD,
        connect_timeout=10,
        sslmode="prefer") as conn:

         cursor = conn.cursor()
         cursor.execute(f"""WITH gap_fill AS (
                SELECT
                id,
                marketCap,
                volume,
                btcDominance,
                marketCapChange,
                volumeChange,
                btcDominanceChange,
                fear_greed_value,
                date,

                LAG(marketCap) OVER (ORDER BY date) AS prev_marketCap,
                LEAD(marketCap) OVER (ORDER BY date) AS next_marketCap,

                LAG(btcDominance) OVER (ORDER BY date) AS prev_btcDominance,
                LEAD(btcDominance) OVER (ORDER BY date) AS next_btcDominance,

                LAG(marketCapChange) OVER (ORDER BY date) AS prev_marketCapChange,
                LEAD(marketCapChange) OVER (ORDER BY date) AS next_marketCapChange,

                LAG(volumeChange) OVER (ORDER BY date) AS prev_volumeChange,
                LEAD(volumeChange) OVER (ORDER BY date) AS next_volumeChange,

                LAG(btcDominanceChange) OVER (ORDER BY date) AS prev_btcDominanceChange,
                LEAD(btcDominanceChange) OVER (ORDER BY date) AS next_btcDominanceChange,

                LAG(fear_greed_value) OVER (ORDER BY date) AS prev_fear_greed_value,
                LEAD(fear_greed_value) OVER (ORDER BY date) AS next_fear_greed_value,

                LAG(volume) OVER (ORDER BY date) AS prev_volume,
                LEAD(volume) OVER (ORDER BY date) AS next_volume

                FROM {table_name}
                ),
                patched AS (
                SELECT *,
                (prev_marketCap + next_marketCap)/2.0 AS avg_marketCap,
                (prev_volume + next_volume)/2.0 AS avg_volume,
                (prev_prev_btcDominance + next_prev_btcDominance)/2.0 AS avg_btcDominance,
                (prev_marketCapChange + next_marketCapChange)/2.0 AS avg_marketCapChange,
                (prev_volumeChange + next_volumeChange)/2.0 AS avg_volumeChange,
                (prev_btcDominanceChange + next_btcDominanceChange)/2.0 AS avg_btcDominanceChange,
                (prev_fear_greed_value + next_fear_greed_value)/2.0 AS avg_fear_greed_value

                FROM gap_fill
                WHERE id = {row_number}
                )
                UPDATE {table_name}
                SET
                marketCap = COALESCE(marketCap, patched.avg_marketCap),
                volume = COALESCE(volume ,patched.avg_volume),
                btcDominance = COALESCE(btcDominance ,patched.avg_btcDominance),
                marketCapChange = COALESCE(marketCapChange ,patched.avg_marketCapChange),
                volumeChange = COALESCE(volumeChange ,patched.avg_volumeChange),
                btcDominanceChange = COALESCE(btcDominanceChange ,patched.avg_btcDominanceChange),
                avg_fear_greed_value = COALESCE(fear_greed_value ,patched.avg_fear_greed_value)
                FROM patched
                WHERE {table_name}.id = patched.id; """)

    
    else:
        with psycopg2.connect(
        dbname = PGDATABASE,
        host = PGHOST,
        user = PGUSER,
        port = PGPORT,
        password =PGPASSWORD,
        connect_timeout=10,
        sslmode="prefer") as conn:

         cursor = conn.cursor()
         cursor.execute(f"""WITH gap_fill AS (
                SELECT
                id,
                date,
                price,
                volume,
                marketCap,
                availableSupply,
                totalSupply,
                fullyDilutedValuation,
                priceChange1h,
                priceChange1d,
                priceChange1w,

                LAG(price) OVER (ORDER BY date) AS prev_price,
                LEAD(price) OVER (ORDER BY date) AS next_price,

                LAG(volume) OVER (ORDER BY date) AS prev_volume,
                LEAD(volume) OVER (ORDER BY date) AS next_volume,

                LAG(marketCap) OVER (ORDER BY date) AS prev_marketCap,
                LEAD(marketCap) OVER (ORDER BY date) AS next_marketCap,

                LAG(availableSupply) OVER (ORDER BY date) AS prev_availableSupply,
                LEAD(availableSupply) OVER (ORDER BY date) AS next_availableSupply,

                LAG(totalSupply) OVER (ORDER BY date) AS prev_totalSupply,
                LEAD(totalSupply) OVER (ORDER BY date) AS next_totalSupply,

                LAG(fullyDilutedValuation) OVER (ORDER BY date) AS prev_fdv,
                LEAD(fullyDilutedValuation) OVER (ORDER BY date) AS next_fdv,

                LAG(priceChange1h) OVER (ORDER BY date) AS prev_pc1h,
                LEAD(priceChange1h) OVER (ORDER BY date) AS next_pc1h,

                LAG(priceChange1d) OVER (ORDER BY date) AS prev_pc1d,
                LEAD(priceChange1d) OVER (ORDER BY date) AS next_pc1d,

                LAG(priceChange1w) OVER (ORDER BY date) AS prev_pc1w,
                LEAD(priceChange1w) OVER (ORDER BY date) AS next_pc1w
                FROM {table_name}
                ),
                patched AS (
                SELECT *,
                (prev_price + next_price)/2.0 AS avg_price,
                (prev_volume + next_volume)/2.0 AS avg_volume,
                (prev_marketCap + next_marketCap)/2.0 AS avg_marketCap,
                (prev_availableSupply + next_availableSupply)/2.0 AS avg_availableSupply,
                (prev_totalSupply + next_totalSupply)/2.0 AS avg_totalSupply,
                (prev_fdv + next_fdv)/2.0 AS avg_fullyDilutedValuation,
                (prev_pc1h + next_pc1h)/2.0 AS avg_priceChange1h,
                (prev_pc1d + next_pc1d)/2.0 AS avg_priceChange1d,
                (prev_pc1w + next_pc1w)/2.0 AS avg_priceChange1w

                FROM gap_fill
                WHERE id = {row_number}
                )
                UPDATE {table_name}
                SET
                price = COALESCE(price, patched.avg_price),
                volume = COALESCE(volume, patched.avg_volume),
                marketCap = COALESCE(marketCap, patched.avg_marketCap),
                availableSupply = COALESCE(availableSupply, patched.avg_availableSupply),
                totalSupply = COALESCE(totalSupply, patched.avg_totalSupply),
                fullyDilutedValuation = COALESCE(fullyDilutedValuation, patched.avg_fullyDilutedValuation),
                priceChange1h = COALESCE(priceChange1h, patched.avg_priceChange1h),
                priceChange1d = COALESCE(priceChange1d, patched.avg_priceChange1d),
                priceChange1w = COALESCE(priceChange1w, patched.avg_priceChange1w)
                FROM patched
                WHERE {table_name}.id = patched.id; """)

# Main program logic

table_list = ['bitcoin_data', 'eth_data', 'market_data']

def main():
    """
    Main control loop for launching the interactive row-correction utility.

    Allows the user to:
        - Choose a target table (`bitcoin_data`, `eth_data`, `market_data`, or all).
        - Specify a row number to correct via interpolation.
        - Confirm the update before execution.

    The function prevents editing the first row (row 1) due to insufficient context for interpolation.
    For "all" tables, it applies the correction across each table listed in `table_list`.

    Returns:
        None

    Side Effects:
        - Reads user input via the console.
        - Modifies rows in the `crypto_data.sqlite` database.
        - Prints status messages for each operation.

    Raises:
        None: All user input and operational branches are internally validated.

    Notes:
        - The update logic relies on `fill_db()` and assumes tables are sorted chronologically by `date`.
        - To exit the program, the user can select "Exit" when prompted in the `which_table()` function.
    """
    while True:
        
        table = which_table()

        if table == 'all':

            row = which_row()
            confirm = input(f"Proceed with row '{row}' . y/n ? \n ")
            
            if row == 1:
                print("\nCannot proceed with row 1")
                continue

            if confirm.lower() == 'y':
            
                for tables in table_list:
                
                    fill_db(tables, row)
                    print('Done !')
                    
                continue

            else: 
                continue


        else:
            row = which_row()
            confirm = input(f"Proceed with row '{row}' ? y/n ? ")
            
            if row == 1:

                print("\nCannot proceed with row 1")
                continue

            if confirm.lower() == 'y':

                fill_db(table, row)
                print('Done !')
                continue

            else: 
                continue

if __name__ == '__main__':
    main()
