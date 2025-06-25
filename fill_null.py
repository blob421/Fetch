import sqlite3
import os 

def which_table():
    """
    Prompts the user to select a target database table for data correction.

    Offers a menu of options including specific tables (`bitcoin_data`, `eth_data`, `market_data`),
    the option to apply changes to all tables, or to exit the program.

    Returns:
        - str: The name of the selected table.
        - 'bitcoin_data'
        - 'eth_data'
        - 'market_data'
        - 'all' (to process every table)
        
    Side Effects:
        - Displays a menu to the console.
        - Prompts the user for input.
        - Terminates the program with exit code 0 if the user selects Exit (option 5).

    Raises:
        - None: All input validation is handled internally. Prompts the user again on invalid input.
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
        - int: The validated row number input by the user.

    Side Effects:
        - Displays prompts and error messages in the console.
        - Handles and reprompts on invalid input types.

    Raises:
        - None: All exceptions are caught and handled internally.
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
        - table_name (str): The name of the table to update. Must be one of:
        - 'market_data'
        - 'bitcoin_data'
        - 'eth_data'
        - row_number (int): The position (1-based index) of the row to update. This function will 
            use rows `row_number - 1` and `row_number + 1` to compute mean values.

    Returns:
        - None

    Side Effects:
        - Connects to `crypto_data.sqlite` database.
        - Executes an UPDATE statement that modifies one row based on surrounding row values.

    Raises:
        - sqlite3.Error: If a database access error occurs.
        - ValueError: If row_number < 2, which would make interpolation impossible.

    Notes:
        >>> Relies on SQLite's `rowid` and assumes the table is chronologically ordered by `date`.
        >>> Does not update non-numeric or textual columns (e.g. labels, timestamps).
    """
    if table_name == 'market_data':

        with sqlite3.connect('crypto_data.sqlite') as conn:
          
          cursor = conn.cursor()
          cursor.executescript(f"""
        
        WITH ordered AS (
            SELECT rowid AS rid, *
            FROM {table_name}
            ORDER BY date
        ),
        row_1144 AS (
            SELECT * FROM ordered
            LIMIT 1 OFFSET {row_number - 2}
        ),
        row_1146 AS (
            SELECT * FROM ordered
            LIMIT 1 OFFSET {row_number}
        ),
        mean_vals AS (
            SELECT
                (r1.marketCap + r3.marketCap)/2.0 AS avg_marketCap,
                (r1.volume + r3.volume)/2.0 AS avg_volume,
                (r1.btcDominance + r3.btcDominance)/2.0 AS avg_btcDominance,
                (r1.marketCapChange + r3.marketCapChange)/2.0 AS avg_marketCapChange,
                (r1.volumeChange + r3.volumeChange)/2.0 AS avg_volumeChange,
                (r1.btcDominanceChange + r3.btcDominanceChange)/2.0 AS avg_btcDominanceChange,
                (r1.fear_greed_value + r3.fear_greed_value)/2.0 AS avg_fear_greed_value
            FROM row_1144 r1, row_1146 r3
        ),
        target_row AS (
            SELECT rid FROM ordered LIMIT 1 OFFSET {row_number - 1}
        )
        UPDATE {table_name}
        SET
            marketCap = (SELECT avg_marketCap FROM mean_vals),
            volume = (SELECT avg_volume FROM mean_vals),
            btcDominance = (SELECT avg_btcDominance FROM mean_vals),
            marketCapChange = (SELECT avg_marketCapChange FROM mean_vals),
            volumeChange = (SELECT avg_volumeChange FROM mean_vals),
            btcDominanceChange = (SELECT avg_btcDominanceChange FROM mean_vals),
            fear_greed_value = (SELECT avg_fear_greed_value FROM mean_vals)
        WHERE rowid = (SELECT rid FROM target_row);
""")

    
    else:
        with sqlite3.connect('crypto_data.sqlite') as conn:
            cursor = conn.cursor()
            
            cursor.executescript(f"""
                                
        WITH ordered AS (
            SELECT rowid AS rid, *
            FROM {table_name}
            ORDER BY date
        ),
        row_1144 AS (
            SELECT * FROM ordered
            LIMIT 1 OFFSET {row_number - 2}
        ),
        row_1146 AS (
            SELECT * FROM ordered
            LIMIT 1 OFFSET {row_number}
        ),
        mean_vals AS (
            SELECT
                (r1.price + r3.price)/2.0 AS avg_price,
                (r1.volume + r3.volume)/2.0 AS avg_volume,
                (r1.marketCap + r3.marketCap)/2.0 AS avg_marketCap,
                (r1.availableSupply + r3.availableSupply)/2.0 AS avg_availableSupply,
                (r1.totalSupply + r3.totalSupply)/2.0 AS avg_totalSupply,
                (r1.fullyDilutedValuation + r3.fullyDilutedValuation)/2.0 AS avg_fdv,
                (r1.priceChange1h + r3.priceChange1h)/2.0 AS avg_priceChange1h,
                (r1.priceChange1d + r3.priceChange1d)/2.0 AS avg_priceChange1d,
                (r1.priceChange1w + r3.priceChange1w)/2.0 AS avg_priceChange1w
            FROM row_1144 r1, row_1146 r3
        ),
        target_row AS (
            SELECT rid FROM ordered LIMIT 1 OFFSET {row_number - 1}
        )
        UPDATE {table_name}
        SET
            price = (SELECT avg_price FROM mean_vals),
            volume = (SELECT avg_volume FROM mean_vals),
            marketCap = (SELECT avg_marketCap FROM mean_vals),
            availableSupply = (SELECT avg_availableSupply FROM mean_vals),
            totalSupply = (SELECT avg_totalSupply FROM mean_vals),
            fullyDilutedValuation = (SELECT avg_fdv FROM mean_vals),
            priceChange1h = (SELECT avg_priceChange1h FROM mean_vals),
            priceChange1d = (SELECT avg_priceChange1d FROM mean_vals),
            priceChange1w = (SELECT avg_priceChange1w FROM mean_vals)
        WHERE rowid = (SELECT rid FROM target_row);
                             
""")

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
        - None

    Side Effects:
        - Reads user input via the console.
        - Modifies rows in the `crypto_data.sqlite` database.
        - Prints status messages for each operation.

    Raises:
        - None: All user input and operational branches are internally validated.

    Notes:
        >>> The update logic relies on `fill_db()` and assumes tables are sorted chronologically by `date`.
        >>> To exit the program, the user can select "Exit" when prompted in the `which_table()` function.
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
