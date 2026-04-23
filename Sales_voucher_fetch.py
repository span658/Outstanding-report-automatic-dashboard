import requests

xml_request = """
<ENVELOPE>
    <HEADER>
        <VERSION>1</VERSION>
        <TALLYREQUEST>Export</TALLYREQUEST>
        <TYPE>Collection</TYPE>
        <ID>OAISalesVoucherColl</ID>
    </HEADER>
    <BODY>
        <DESC>
            <STATICVARIABLES>
                <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
            </STATICVARIABLES>
            <TDL>
                <TDLMESSAGE>
                    <COLLECTION NAME="OAISalesVoucherColl">
                        <TYPE>Vouchers : VoucherType</TYPE>
                        <CHILDOF>$$VchTypeSales</CHILDOF>
                        <FETCH>VoucherTypeName</FETCH>
                    </COLLECTION>
                </TDLMESSAGE>
            </TDL>
        </DESC>
    </BODY>
</ENVELOPE>
"""

response = requests.post(
    "http://127.0.0.1:9000",
    data=xml_request.encode("utf-8"),
    headers={"Content-Type": "text/xml; charset=utf-8"},
    timeout=20
)

xml_text = response.text

total_sales = xml_text.count("<VOUCHERTYPENAME>")

print("========= OUTPUT =========")
print("VoucherType : Sales")
print("Total Vouchers :", total_sales)
print("==========================")