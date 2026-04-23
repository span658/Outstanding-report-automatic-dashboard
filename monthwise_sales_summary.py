import re
import requests
import xml.etree.ElementTree as ET
from collections import defaultdict
from datetime import datetime

# =========================================================
# SETTINGS
# =========================================================
TALLY_URL = "http://127.0.0.1:9000"
FROM_DATE = "20250401"
TO_DATE = "20260331"

# True = only exact "Sales"
# False = all sales-related voucher types
ONLY_EXACT_SALES = True

# =========================================================
# XML REQUEST
# =========================================================
sales_formula = '$VoucherTypeName = "Sales"' if ONLY_EXACT_SALES else '$$IsSales:$VoucherTypeName'

xml_request = f"""
<ENVELOPE>
    <HEADER>
        <VERSION>1</VERSION>
        <TALLYREQUEST>Export</TALLYREQUEST>
        <TYPE>Collection</TYPE>
        <ID>OAIMonthSalesColl</ID>
    </HEADER>
    <BODY>
        <DESC>
            <STATICVARIABLES>
                <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
                <SVFROMDATE>{FROM_DATE}</SVFROMDATE>
                <SVTODATE>{TO_DATE}</SVTODATE>
            </STATICVARIABLES>
            <TDL>
                <TDLMESSAGE>
                    <SYSTEM TYPE="Formulae" NAME="OAIOnlySales">
                        {sales_formula}
                    </SYSTEM>

                    <COLLECTION NAME="OAIMonthSalesColl" ISINITIALIZE="Yes">
                        <TYPE>Voucher</TYPE>
                        <FETCH>Date,MasterID,VoucherTypeName</FETCH>
                        <FILTER>OAIOnlySales</FILTER>
                    </COLLECTION>
                </TDLMESSAGE>
            </TDL>
        </DESC>
    </BODY>
</ENVELOPE>
"""

print("STEP 1: Script started")
print("STEP 2: XML request prepared")

# =========================================================
# SEND REQUEST
# =========================================================
try:
    response = requests.post(
        TALLY_URL,
        data=xml_request.encode("utf-8"),
        headers={"Content-Type": "text/xml; charset=utf-8"},
        timeout=20
    )
except requests.exceptions.ConnectionError:
    print("ERROR: Could not connect to Tally on port 9000")
    print("Check that Tally is open and XML server is enabled.")
    raise SystemExit
except requests.exceptions.Timeout:
    print("ERROR: Request timed out")
    raise SystemExit
except Exception as e:
    print("ERROR while sending request:", e)
    raise SystemExit

print("STEP 3: Request sent")
print("HTTP Status Code:", response.status_code)
print("Response Length:", len(response.text))

if not response.text.strip():
    print("ERROR: Empty response from Tally")
    raise SystemExit

print("\n----- RAW RESPONSE PREVIEW -----\n")
print(response.text[:2000])
print("\n----- RAW RESPONSE END -----\n")

# =========================================================
# CLEAN XML TO AVOID 'unbound prefix' ERRORS
# =========================================================
xml_data = response.text

# remove common namespace declarations that sometimes break parsing
xml_data = re.sub(r'\sxmlns:[A-Za-z0-9_]+="[^"]*"', "", xml_data)

# remove tag prefixes like UDF:, TALLY:, etc.
xml_data = re.sub(r"<(/?)([A-Za-z0-9_]+):", r"<\1", xml_data)

# =========================================================
# PARSE XML
# =========================================================
try:
    root = ET.fromstring(xml_data)
    print("STEP 4: XML parsed successfully")
except ET.ParseError as e:
    print("XML Parse Error:", e)
    print("\nCould not parse cleaned XML.")
    print("First 1500 chars of cleaned XML:\n")
    print(xml_data[:1500])
    raise SystemExit

# =========================================================
# CHECK TALLY STATUS
# =========================================================
status = root.find(".//STATUS")
if status is not None:
    print("Tally STATUS:", status.text)
    if status.text == "0":
        print("ERROR: Tally rejected the request internally.")
        print("Check:")
        print("1. Company is open in Tally")
        print("2. Sales vouchers exist in selected date range")
        print("3. Voucher type name is really 'Sales'")
        raise SystemExit

# =========================================================
# EXTRACT DATE VALUES
# =========================================================
dates = []

for elem in root.iter():
    tag = elem.tag.upper() if elem.tag else ""
    txt = elem.text.strip() if elem.text else ""

    if tag == "DATE" and txt:
        dates.append(txt)

print("STEP 5: DATE extraction completed")
print("Total DATE values found:", len(dates))
print("Sample DATE values:", dates[:10])

if not dates:
    print("ERROR: No DATE values found in XML response.")
    print("\nFirst 100 text values for debugging:\n")
    shown = 0
    for elem in root.iter():
        if elem.text and elem.text.strip():
            print(f"{elem.tag} => {elem.text.strip()}")
            shown += 1
            if shown >= 100:
                break
    raise SystemExit

# =========================================================
# DATE PARSER
# =========================================================
def parse_tally_date(text):
    formats = [
        "%Y%m%d",
        "%d-%b-%Y",
        "%d-%m-%Y",
        "%Y-%m-%d",
        "%d/%m/%Y"
    ]
    for fmt in formats:
        try:
            return datetime.strptime(text.strip(), fmt)
        except ValueError:
            pass
    return None

# =========================================================
# MONTHWISE TOTAL COUNT
# =========================================================
monthwise = defaultdict(int)

for d in dates:
    dt = parse_tally_date(d)
    if dt is not None:
        month_label = dt.strftime("%B %Y")
        monthwise[month_label] += 1

if not monthwise:
    print("ERROR: Dates were found, but none could be converted.")
    raise SystemExit

sorted_rows = sorted(
    monthwise.items(),
    key=lambda x: datetime.strptime(x[0], "%B %Y")
)

# =========================================================
# FINAL OUTPUT
# =========================================================
print("\nMonth                              Total Vouchers")
print("-" * 70)

for month, total in sorted_rows:
    print(f"{month:<35}{total:>15}")

print("\nDONE")