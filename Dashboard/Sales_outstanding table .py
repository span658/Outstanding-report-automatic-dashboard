import csv

file_path = r"C:\Users\Admin\Desktop\xmlrequest\Sales_details_output.csv"

with open(file_path, "r", encoding="utf-8-sig") as f:
    reader = csv.reader(f)
    rows = list(reader)

print("Total rows in CSV (including header):", len(rows))
print("Actual data rows:", len(rows) - 1)
