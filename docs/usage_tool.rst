About fill_null
===================================================

This module provides a command-line interface for correcting missing or incomplete rows
in Fetch's database. It allows users to select a target table 
( `bitcoin_data`, `eth_data` or `market_data` ), specify a row number, and update that row 
by averaging the values from adjacent rows.

Features
----------
 - Supports targeted correction of single rows .
 - Interpolation using the linear mean of the immediate neighboring entries (e.g., rows 1144 and 1146).
 - Batch correction across all registered tables(`bitcoin_data`, `eth_data`, `market_data`).
 - Safeguards against invalid input and edge cases (e.g., row 1).
 - Designed to work with tables ordered chronologically by `date`.

