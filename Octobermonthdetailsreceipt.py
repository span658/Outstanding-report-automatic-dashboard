import requests
from lxml import etree
from datetime import datetime

# =========================================
# XML REQUEST (OCTOBER 2025 ONLY)
# =========================================
xml_request = """<?xml version="1.0" encoding="UTF-8"?>
<ENVELOPE>
    <HEADER>
        <VERSION>1</VERSION>
        <TALLYREQUEST>Export Data</TALLYREQUEST>
        <TYPE>Collection</TYPE>
        <ID>OAIReceiptOctober2025Coll</ID>
    </HEADER>
    <BODY>
        <DESC>
            <STATICVARIABLES>
                <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
            </STATICVARIABLES>
            <TDL>
                <TDLMESSAGE>

                    <COLLECTION NAME="OAIReceiptOctober2025Coll">
                        <TYPE>Voucher</TYPE>
                        <FETCH>Date, VoucherNumber, VoucherTypeName, PartyLedgerName, MasterID, AllLedgerEntries.*</FETCH>
                        <FILTER>OAIIsReceipt, OAIOctober2025</FILTER>
                    </COLLECTION>

                    <SYSTEM TYPE="Formulae" NAME="OAIIsReceipt">
                        $VoucherTypeName = "Receipt"
                    </SYSTEM>

                    <SYSTEM TYPE="Formulae" NAME="OAIOctober2025">
                        $$MonthOfDate:$Date = 10 AND $$YearOfDate:$Date = 2025
                    </SYSTEM>

                </TDLMESSAGE>
            </TDL>
        </DESC>
    </BODY>
</ENVELOPE>
"""

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

# CALL TALLY
response = requests.post(
    "http://127.0.0.1:9000",
    data=xml_request.encode("utf-8"),
    headers={"Content-Type": "text/xml; charset=utf-8"},
    timeout=120
)

parser = etree.XMLParser(recover=True, encoding="utf-8")
root = etree.fromstring(response.content, parser=parser)

vouchers = root.xpath("//*[local-name()='VOUCHER']")
if not vouchers:
    vouchers = root.xpath("//COLLECTION/*")

rows = []

for v in vouchers:
    raw_date = get_text(v, "DATE")
    party_name = get_text(v, "PARTYLEDGERNAME")
    voucher_no = get_text(v, "VOUCHERNUMBER")
    voucher_type = get_text(v, "VOUCHERTYPENAME")

    # 🚫 Skip invalid rows silently
    if not raw_date or len(raw_date) != 8 or not raw_date.isdigit():
        continue

    try:
        dt = datetime.strptime(raw_date, "%Y%m%d")
        formatted_date = dt.strftime("%d-%m-%Y")
        sort_date = dt
    except:
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
        except:
            amt = 0.0

        if amt < 0:
            credit_amount += abs(amt)

    if not party_name:
        party_name = fallback

    rows.append({
        "sort": sort_date,
        "Date": formatted_date,
        "Party": party_name,
        "VoucherNo": voucher_no,
        "VoucherType": voucher_type,
        "Credit": credit_amount
    })

rows.sort(key=lambda x: x["sort"])

# OUTPUT
print("\n" + "=" * 115)
print("OCTOBER 2025 RECEIPT DRILLDOWN")
print("=" * 115)

print(f"{'Date':<15} {'Particulars / PartyName':<40} {'VoucherNo':<15} {'VoucherType':<15} {'CreditAmount':>15}")
print("-" * 115)

for r in rows:
    print(
        f"{r['Date']:<15} "
        f"{r['Party'][:39]:<40} "
        f"{r['VoucherNo']:<15} "
        f"{r['VoucherType']:<15} "
        f"{r['Credit']:>15.2f}"
    )

print("-" * 115)
print("Actual Total Vouchers =", len(rows))