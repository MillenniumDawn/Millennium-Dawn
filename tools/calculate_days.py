#!/usr/bin/env python3

"""
Calculate Days

This script counts the number of days to a date so you can trigger an event on the targeted date. Provide a month and a day. It will calculate from 2000.

Usage:
    python3 calculate_days.py
"""

days_per_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
start_year = 2000

while True:
    provided_date = [
        int(x)
        for x in input("Enter day you want the event to fire (YYYY.MM.DD):").split(".")
    ]

    # The final number
    days = 0

    # Check if provided year is in range
    if provided_date[0] - start_year >= 0:
        # Add years to days
        for x in range(provided_date[0] - start_year):
            for y in days_per_month:
                days += y
    else:
        print("Error: Year is less than " + str(start_year) + ".")
        continue

    # Check if provided month is in range
    if provided_date[1] > 0 and provided_date[1] <= 12:
        # Add months to days
        ix = -1
        for x in range(provided_date[1] - 1):
            ix += 1
            days += days_per_month[ix]
    else:
        print("Error: Month out of range.")
        continue

    # Check if provided date is in range
    if (
        provided_date[2] > 0
        and provided_date[2] <= days_per_month[provided_date[1] - 1]
    ):
        # Add days to days
        days += provided_date[2] - 1
    else:
        print("Error: Days out of range.")
        continue

    print("Days since 2000:", days)
