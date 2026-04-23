import re
import requests
import xml.etree.ElementTree as ET
from datetime import datetime

TALLY_URL = "http://127.0.0.1:9000"
FROM_DATE = "20250401"
TO_DATE = "20260331"

xml_request = f"""
<ENVELOPE>
    <HEADER>
        <VERSION>1</VERSION>
        <TALLYREQUEST>Export</TALLYREQUEST>
        <TYPE>Collection</TYPE>
        <ID>MonthPurchaseVoucherColl</ID>
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
                    <SYSTEM TYPE="Formulae" NAME="OnlyPurchase">
                        $VoucherTypeName = "Purchase"
                    </SYSTEM>

                    <COLLECTION NAME="MonthPurchaseVoucherColl" ISINITIALIZE="Yes">
                        <TYPE>Voucher</TYPE>
                        <FETCH>
                            Date,
                            PartyLedgerName,
                            VoucherTypeName,
                            VoucherNumber,
                            MasterID,
                            AllLedgerEntries.*
                        </FETCH>
                        <FILTER>OnlyPurchase</FILTER>
                    </COLLECTION>
                </TDLMESSAGE>
            </TDL>
        </DESC>
    </BODY>
</ENVELOPE>
"""

print("STEP 1: Sending request to Tally...")

try:
    response = requests.post(
        TALLY_URL,
        data=xml_request.encode("utf-8"),
        headers={"Content-Type": "text/xml; charset=utf-8"},
        timeout=20
    )
except requests.exceptions.ConnectionError:
    print("ERROR: Could not connect to Tally on port 9000")
    raise SystemExit
except requests.exceptions.Timeout:
    print("ERROR: Request timed out")
    raise SystemExit
except Exception as e:
    print("ERROR while sending request:", e)
    raise SystemExit

print("HTTP Status Code:", response.status_code)
print("Response Length:", len(response.text))

if not response.text.strip():
    print("ERROR: Empty response from Tally")
    raise SystemExit

print("\n----- RAW RESPONSE PREVIEW -----\n")
print(response.text[:1000])
print("\n----- END PREVIEW -----\n")

# =========================================================
# CLEAN XML
# =========================================================
xml_data = response.text

xml_data = re.sub(r'\sxmlns:[A-Za-z0-9_]+="[^"]*"', "", xml_data)
xml_data = re.sub(r"<(/?)([A-Za-z0-9_]+):", r"<\1", xml_data)
xml_data = re.sub(r'&#(?:x[0-9A-Fa-f]+|\d+);', '', xml_data)
xml_data = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F]', '', xml_data)

# =========================================================
# PARSE XML
# =========================================================
try:
    root = ET.fromstring(xml_data)
    print("STEP 2: XML parsed successfully")
except ET.ParseError as e:
    print("XML Parse Error:", e)
    print("\nCleaned XML preview:\n")
    print(xml_data[:1500])
    raise SystemExit

status = root.find(".//STATUS")
if status is not None:
    print("Tally STATUS:", status.text)
    if status.text == "0":
        print("ERROR: Tally rejected the request internally.")
        raise SystemExit

def format_tally_date(date_text):
    if not date_text:
        return ""
    formats = ["%Y%m%d", "%d-%b-%Y", "%d-%m-%Y", "%Y-%m-%d", "%d/%m/%Y"]
    for fmt in formats:
        try:
            return datetime.strptime(date_text.strip(), fmt).strftime("%d-%b-%y")
        except ValueError:
            pass
    return date_text.strip()

rows = []

# =========================================================
# PARSE PURCHASE VOUCHERS
# =========================================================
for v in root.findall(".//VOUCHER"):
    date_val = (v.findtext("DATE") or "").strip()
    party_val = (v.findtext("PARTYLEDGERNAME") or "").strip()
    type_val = (v.findtext("VOUCHERTYPENAME") or "").strip()
    voucher_no_val = (v.findtext("VOUCHERNUMBER") or "").strip()

    if type_val.lower() != "purchase":
        continue

    # fallback if party name is empty
    if not party_val:
        first_ledger = v.find(".//ALLLEDGERENTRIES.LIST/LEDGERNAME")
        if first_ledger is not None and first_ledger.text:
            party_val = first_ledger.text.strip()

    # -----------------------------
    # CREDIT AMOUNT LOGIC ONLY
    # -----------------------------
    credit_amount = 0.0

    ledger_entries = v.findall(".//ALLLEDGERENTRIES.LIST")

    for entry in ledger_entries:
        amount_text = (entry.findtext("AMOUNT") or "").strip()
        is_deemed_positive = (entry.findtext("ISDEEMEDPOSITIVE") or "").strip().lower()

        try:
            amt = float(amount_text)
        except:
            amt = 0.0

        # Credit side logic
        if is_deemed_positive == "no":
            credit_amount += abs(amt)

    rows.append({
        "date": format_tally_date(date_val),
        "party": party_val,
        "credit_amount": round(credit_amount, 2),
        "voucher_type": type_val,
        "voucher_no": voucher_no_val
    })

print("Extracted rows:", len(rows))
print("First 3 rows:", rows[:3])

if not rows:
    print("No purchase voucher rows found.")
    print("\nFirst 100 text values for debugging:\n")
    shown = 0
    for elem in root.iter():
        if elem.text and elem.text.strip():
            print(f"{elem.tag} => {elem.text.strip()}")
            shown += 1
            if shown >= 100:
                break
    raise SystemExit

def sort_key(row):
    try:
        return datetime.strptime(row["date"], "%d-%b-%y"), row["voucher_no"]
    except ValueError:
        return datetime.max, row["voucher_no"]

rows.sort(key=sort_key)

print("\nOne Year Purchase Voucher Details")
print("-" * 125)
print(f"{'Date':<12}{'Party Name':<50}{'Credit Amount':>18}  {'Voucher Type':<15}{'Voucher No':<22}")
print("-" * 125)

for r in rows:
    print(
        f"{r['date']:<12}"
        f"{r['party'][:49]:<50}"
        f"{r['credit_amount']:>18}  "
        f"{r['voucher_type']:<15}"
        f"{r['voucher_no']:<22}"
    )

print("\nTotal Vouchers:", len(rows))
print("DONE")