import requests
from lxml import etree

xml_request = """<?xml version="1.0" encoding="UTF-8"?>
<ENVELOPE>
    <HEADER>
        <VERSION>1</VERSION>
        <TALLYREQUEST>Export Data</TALLYREQUEST>
        <TYPE>Collection</TYPE>
        <ID>OAIPurchaseVoucherColl</ID>
    </HEADER>
    <BODY>
        <DESC>
            <STATICVARIABLES>
                <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
            </STATICVARIABLES>
            <TDL>
                <TDLMESSAGE>

                    <SYSTEM TYPE="Formulae" NAME="OAIIsPurchase">
                        $VoucherTypeName = "Purchase"
                    </SYSTEM>

                    <COLLECTION NAME="OAIPurchaseVoucherColl">
                        <TYPE>Voucher</TYPE>
                        <FETCH>MasterID, IsOptional</FETCH>
                        <FILTER>OAIIsPurchase</FILTER>
                    </COLLECTION>

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
        timeout=20
    )

    parser = etree.XMLParser(recover=True)
    root = etree.fromstring(response.content, parser=parser)

    vouchers = root.xpath("//VOUCHER")
    unique_masterids = set()

    for v in vouchers:
        masterid = (v.findtext("MASTERID") or "").strip()
        is_optional = (v.findtext("ISOPTIONAL") or "").strip().lower()

        if is_optional in ("yes", "true", "1"):
            continue

        if masterid:
            unique_masterids.add(masterid)

    total_vouchers = len(unique_masterids)

    print("Voucher Type  : Purchase")
    print("Total Vouchers:", total_vouchers)

except requests.exceptions.RequestException as e:
    print("Request Error:", e)

except Exception as e:
    print("Parsing/Other Error:", e)