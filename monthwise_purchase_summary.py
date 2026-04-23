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
                        <FETCH>MasterID, Date, IsOptional</FETCH>
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

    seen_masterids = set()
    monthwise_counts = defaultdict(int)

    for v in vouchers:
        masterid = (v.findtext("MASTERID") or "").strip()
        date_str = (v.findtext("DATE") or "").strip()
        is_optional = (v.findtext("ISOPTIONAL") or "").strip().lower()

        if is_optional in ("yes", "true", "1"):
            continue

        if not masterid or masterid in seen_masterids:
            continue

        seen_masterids.add(masterid)

        try:
            dt = datetime.strptime(date_str, "%Y%m%d")
            month_label = dt.strftime("%B %Y")
            monthwise_counts[month_label] += 1
        except:
            pass

    sorted_months = sorted(
        monthwise_counts.items(),
        key=lambda x: datetime.strptime(x[0], "%B %Y")
    )

    print("Voucher Type : Purchase\n")
    for month, count in sorted_months:
        print(f"{month} -> {count}")

except requests.exceptions.RequestException as e:
    print("Request Error:", e)

except Exception as e:
    print("Parsing/Other Error:", e)