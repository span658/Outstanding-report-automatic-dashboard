import requests
from lxml import etree

xml_request = """<?xml version="1.0" encoding="UTF-8"?>
<ENVELOPE>
    <HEADER>
        <VERSION>1</VERSION>
        <TALLYREQUEST>Export Data</TALLYREQUEST>
        <TYPE>Collection</TYPE>
        <ID>OAIReceiptOnlyColl</ID>
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

                    <COLLECTION NAME="OAIReceiptOnlyColl">
                        <TYPE>Voucher</TYPE>
                        <FETCH>MasterID, VoucherTypeName</FETCH>
                        <FILTER>OAIReceiptOnly</FILTER>
                    </COLLECTION>

                    <SYSTEM TYPE="Formulae" NAME="OAIReceiptOnly">
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

# Count MASTERID nodes only
master_ids = root.xpath("//*[local-name()='MASTERID']")
receipt_count = len(master_ids)

print("\n==============================")
print("LEVEL 1 OUTPUT")
print("==============================")
print("VoucherType : Receipt")
print("Total Vouchers :", receipt_count)