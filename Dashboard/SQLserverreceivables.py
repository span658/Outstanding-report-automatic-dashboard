import re
import html
import pyodbc

# ==============================
# 1. FILE PATH
# ==============================
FILE_PATH = r"C:\Users\Admin\Desktop\xmlrequest\bills.details.xml"

# ==============================
# 2. SQL SERVER CONNECTION
# ==============================
CONN_STR = (
    "Driver={SQL Server};"
    "Server=DESKTOP-EKDKIFK\\SQLEXPRESS;"
    "Database=BillDB;"
    "Trusted_Connection=yes;"
)

# ==============================
# 3. READ FILE
# ==============================
with open(FILE_PATH, "r", encoding="utf-8", errors="ignore") as f:
    raw_text = f.read()

# ==============================
# 4. HELPER FUNCTIONS
# ==============================
def clean_text(value):
    if value is None:
        return ""
    return html.unescape(str(value)).strip()

def parse_amount(value):
    value = clean_text(value).replace(",", "")
    if value == "":
        return 0.0
    try:
        return float(value)
    except:
        return 0.0

def parse_int(value):
    value = clean_text(value)
    if value == "":
        return None
    try:
        return int(float(value))
    except:
        return None

# ==============================
# 5. EXTRACT DATA
# ==============================
parts = re.split(r"<BILLFIXED>", raw_text, flags=re.IGNORECASE)
rows = []

for part in parts[1:]:
    date = re.search(r"<BILLDATE>(.*?)</BILLDATE>", part, re.I | re.S)
    ref = re.search(r"<BILLREF>(.*?)</BILLREF>", part, re.I | re.S)
    party = re.search(r"<BILLPARTY>(.*?)</BILLPARTY>", part, re.I | re.S)
    amount = re.search(r"<BILLCL>(.*?)</BILLCL>", part, re.I | re.S)
    due = re.search(r"<BILLDUE>(.*?)</BILLDUE>", part, re.I | re.S)
    overdue = re.search(r"<BILLOVERDUE>(.*?)</BILLOVERDUE>", part, re.I | re.S)

    row = (
        clean_text(date.group(1)) if date else "",
        clean_text(ref.group(1)) if ref else "",
        clean_text(party.group(1)) if party else "",
        abs(parse_amount(amount.group(1))) if amount else 0.0,
        clean_text(due.group(1)) if due else "",
        parse_int(overdue.group(1)) if overdue else None,
    )

    if any(row):
        rows.append(row)

print("TOTAL ROWS EXTRACTED:", len(rows))

# ==============================
# 6. CONNECT SQL SERVER
# ==============================
conn = pyodbc.connect(CONN_STR)
cursor = conn.cursor()

# ==============================
# 7. CREATE TABLE IF NOT EXISTS
# ==============================
cursor.execute("""
IF OBJECT_ID('dbo.BillsReceivableRaw', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.BillsReceivableRaw (
        ID INT IDENTITY(1,1) PRIMARY KEY,
        BillDate NVARCHAR(20),
        RefNo NVARCHAR(100),
        PartyName NVARCHAR(255),
        PendingAmount DECIMAL(18,2),
        DueOn NVARCHAR(20),
        OverdueDays INT
    )
END
""")
conn.commit()

# ==============================
# 8. DELETE OLD DATA
# ==============================
cursor.execute("DELETE FROM dbo.BillsReceivableRaw")
conn.commit()

# ==============================
# 9. INSERT NEW DATA
# ==============================
insert_sql = """
INSERT INTO dbo.BillsReceivableRaw
(BillDate, RefNo, PartyName, PendingAmount, DueOn, OverdueDays)
VALUES (?, ?, ?, ?, ?, ?)
"""

for row in rows:
    cursor.execute(insert_sql, row)

conn.commit()

# ==============================
# 10. VERIFY
# ==============================
cursor.execute("SELECT COUNT(*) FROM dbo.BillsReceivableRaw")
count = cursor.fetchone()[0]

print("TOTAL ROWS INSERTED INTO SQL SERVER:", count)

cursor.close()
conn.close()

print("Data stored successfully in Microsoft SQL Server.")
