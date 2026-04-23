import requests
from lxml import etree
from collections import defaultdict
from datetime import datetime

xml_request = """<?xml version="1.0" encoding="UTF-8"?>
<ENVELOPE>
    <HEADER>
        <VERSION>1</VERSION>
        <TALLYREQUEST>Export Data</TALLYREQUEST>
        <TYPE>Collection</TYPE>
        <ID>OAIReceiptLevel2Coll</ID>
    </HEADER>
    <BODY>
        <DESC>
            <STATICVARIABLES>
                <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
                <SVFROMDATE>20250401</SVFROMDATE>
                <SVTODATE>20260331</SVTODATE>
            </STATICVARIABLES>
            <TDL>
                <TDLMESSAGE>
                    <COLLECTION NAME="OAIReceiptLevel2Coll">
                        <TYPE>Voucher</TYPE>
                        <FETCH>Date, MasterID, VoucherTypeName</FETCH>
                        <FILTER>OAIIsReceipt</FILTER>
                    </COLLECTION>

                    <SYSTEM TYPE="Formulae" NAME="OAIIsReceipt">
                        $VoucherTypeName = "Receipt"
                    </SYSTEM>
                </TDLMESSAGE>
            </TDL>
        </DESC>
    </BODY>
</ENVELOPE>
"""

try:
    response = requests.post(
        "http://127.0.0.1:9000",
        data=xml_request.encode("utf-8"),
        headers={"Content-Type": "text/xml; charset=utf-8"},
        timeout=30
    )
    print("HTTP Status:", response.status_code)
except Exception as e:
    print("Connection Error:", e)
    exit()

print("\n--- RAW RESPONSE PREVIEW ---\n")
print(response.text[:1000])

try:
    parser = etree.XMLParser(recover=True, encoding="utf-8")
    root = etree.fromstring(response.content, parser=parser)
except Exception as e:
    print("XML Parse Error:", e)
    exit()

# Fetch all DATE nodes from Receipt vouchers
date_nodes = root.xpath("//*[local-name()='DATE']")

print("\nTotal Receipt Vouchers Found:", len(date_nodes))

month_count = defaultdict(int)

for node in date_nodes:
    raw_date = (node.text or "").strip()

    try:
        dt = datetime.strptime(raw_date, "%Y%m%d")
        month_key = dt.strftime("%B %Y")
        month_count[month_key] += 1
    except:
        continue

# Sort month-wise
sorted_months = sorted(
    month_count.keys(),
    key=lambda x: datetime.strptime(x, "%B %Y")
)

print("\n==============================")
print("LEVEL 2 OUTPUT")
print("==============================")

for month in sorted_months:
    print(f"{month} -> {month_count[month]}")

print("\nGrand Total =", sum(month_count.values()))