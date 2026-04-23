import requests
from lxml import etree
from datetime import datetime
import time

# =========================================
# MONTH CONFIG (APR 2025 TO MAR 2026)
# =========================================
months = [
    ("April 2025", 4, 2025, "OAIReceiptApril2025Coll", "OAIApril2025"),
    ("May 2025", 5, 2025, "OAIReceiptMay2025Coll", "OAIMay2025"),
    ("June 2025", 6, 2025, "OAIReceiptJune2025Coll", "OAIJune2025"),
    ("July 2025", 7, 2025, "OAIReceiptJuly2025Coll", "OAIJuly2025"),
    ("August 2025", 8, 2025, "OAIReceiptAugust2025Coll", "OAIAugust2025"),
    ("September 2025", 9, 2025, "OAIReceiptSeptember2025Coll", "OAISeptember2025"),
    ("October 2025", 10, 2025, "OAIReceiptOctober2025Coll", "OAIOctober2025"),
    ("November 2025", 11, 2025, "OAIReceiptNovember2025Coll", "OAINovember2025"),
    ("December 2025", 12, 2025, "OAIReceiptDecember2025Coll", "OAIDecember2025"),
    ("January 2026", 1, 2026, "OAIReceiptJanuary2026Coll", "OAIJanuary2026"),
    ("February 2026", 2, 2026, "OAIReceiptFebruary2026Coll", "OAIFebruary2026"),
    ("March 2026", 3, 2026, "OAIReceiptMarch2026Coll", "OAIMarch2026"),
]

TALLY_URL = "http://127.0.0.1:9000"

# =========================================
# HELPER FUNCTIONS
# =========================================
def get_text(node, tag_name):
    value = node.findtext(tag_name)
    if value is not None:
        return value.strip()

    result = node.xpath(f"./*[local-name()='{tag_name.upper()}']/text()")
    if result:
        return (result[0] or "").strip()

    result = node.xpath(f"./*[local-name()='{tag_name}']/text()")
    if result:
        return (result[0] or "").strip()

    return ""

def get_ledger_entries(voucher_node):
    entries = voucher_node.findall(".//ALLLEDGERENTRIES.LIST")
    if entries:
        return entries
    return voucher_node.xpath(".//*[local-name()='ALLLEDGERENTRIES.LIST']")

def build_xml(collection_name, formula_name, month_num, year_num):
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<ENVELOPE>
    <HEADER>
        <VERSION>1</VERSION>
        <TALLYREQUEST>Export Data</TALLYREQUEST>
        <TYPE>Collection</TYPE>
        <ID>{collection_name}</ID>
    </HEADER>
    <BODY>
        <DESC>
            <STATICVARIABLES>
                <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
            </STATICVARIABLES>
            <TDL>
                <TDLMESSAGE>

                    <COLLECTION NAME="{collection_name}">
                        <TYPE>Voucher</TYPE>
                        <FETCH>Date, VoucherNumber, VoucherTypeName, PartyLedgerName, MasterID, AllLedgerEntries.*</FETCH>
                        <FILTER>OAIIsReceipt, {formula_name}</FILTER>
                    </COLLECTION>

                    <SYSTEM TYPE="Formulae" NAME="OAIIsReceipt">
                        $VoucherTypeName = "Receipt"
                    </SYSTEM>

                    <SYSTEM TYPE="Formulae" NAME="{formula_name}">
                        $$MonthOfDate:$Date = {month_num} AND $$YearOfDate:$Date = {year_num}
                    </SYSTEM>

                </TDLMESSAGE>
            </TDL>
        </DESC>
    </BODY>
</ENVELOPE>
"""

# =========================================
# MASTER STORAGE
# =========================================
all_rows = []
month_summary = []

# =========================================
# LOOP THROUGH ALL MONTHS
# =========================================
for month_label, month_num, year_num, collection_name, formula_name in months:
    print(f"\nFetching {month_label} ...")

    xml_request = build_xml(collection_name, formula_name, month_num, year_num)

    try:
        response = requests.post(
            TALLY_URL,
            data=xml_request.encode("utf-8"),
            headers={"Content-Type": "text/xml; charset=utf-8"},
            timeout=120
        )
        print("HTTP Status:", response.status_code)
    except requests.exceptions.Timeout:
        print(f"Timeout while fetching {month_label}")
        continue
    except Exception as e:
        print(f"Connection Error in {month_label}: {e}")
        continue

    try:
        parser = etree.XMLParser(recover=True, encoding="utf-8")
        root = etree.fromstring(response.content, parser=parser)
    except Exception as e:
        print(f"XML Parse Error in {month_label}: {e}")
        continue

    vouchers = root.xpath("//*[local-name()='VOUCHER']")
    if not vouchers:
        vouchers = root.xpath("//COLLECTION/*")

    month_rows = []

    for v in vouchers:
        raw_date = get_text(v, "DATE")
        party_name = get_text(v, "PARTYLEDGERNAME")
        voucher_no = get_text(v, "VOUCHERNUMBER")
        voucher_type = get_text(v, "VOUCHERTYPENAME")

        # Skip invalid rows silently
        if not raw_date or len(raw_date) != 8 or not raw_date.isdigit():
            continue

        try:
            dt = datetime.strptime(raw_date, "%Y%m%d")
            formatted_date = dt.strftime("%d-%m-%Y")
            sort_date = dt
        except Exception:
            continue

        fallback = ""
        credit_amount = 0.0

        for entry in get_ledger_entries(v):
            ledger = get_text(entry, "LEDGERNAME")
            amt_text = get_text(entry, "AMOUNT")

            if not fallback and ledger:
                fallback = ledger

            try:
                amt = float(amt_text) if amt_text else 0.0
            except Exception:
                amt = 0.0

            if amt < 0:
                credit_amount += abs(amt)

        if not party_name:
            party_name = fallback

        row = {
            "sort": sort_date,
            "Month": month_label,
            "Date": formatted_date,
            "Party": party_name,
            "VoucherNo": voucher_no,
            "VoucherType": voucher_type,
            "Credit": credit_amount
        }

        month_rows.append(row)
        all_rows.append(row)

    month_rows.sort(key=lambda x: x["sort"])
    month_summary.append((month_label, len(month_rows)))
    print(f"{month_label} Actual Total Vouchers = {len(month_rows)}")

    # Small pause so Tally does not get overloaded
    time.sleep(1)

# =========================================
# FINAL SORT
# =========================================
all_rows.sort(key=lambda x: x["sort"])

# =========================================
# MONTH-WISE SUMMARY
# =========================================
print("\n" + "=" * 80)
print("MONTH-WISE RECEIPT SUMMARY (APR 2025 TO MAR 2026)")
print("=" * 80)

for month_label, total in month_summary:
    print(f"{month_label:<20} -> {total}")

# =========================================
# FULL YEAR DRILLDOWN
# =========================================
print("\n" + "=" * 130)
print("FULL YEAR RECEIPT DRILLDOWN (APR 2025 TO MAR 2026)")
print("=" * 130)

print(f"{'Date':<15} {'Month':<18} {'Particulars / PartyName':<40} {'VoucherNo':<15} {'VoucherType':<15} {'CreditAmount':>15}")
print("-" * 130)

for r in all_rows:
    print(
        f"{r['Date']:<15} "
        f"{r['Month']:<18} "
        f"{r['Party'][:39]:<40} "
        f"{r['VoucherNo']:<15} "
        f"{r['VoucherType']:<15} "
        f"{r['Credit']:>15.2f}"
    )

print("-" * 130)
print("FULL YEAR ACTUAL TOTAL VOUCHERS =", len(all_rows))