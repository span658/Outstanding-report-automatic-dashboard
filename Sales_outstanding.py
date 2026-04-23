import xml.etree.ElementTree as ET
import os

# Correct filename and path
xml_file = r"C:\Users\Admin\Desktop\xmlrequest\Sales_details.xml"

try:
    if not os.path.exists(xml_file):
        raise FileNotFoundError(f"File not found at: {xml_file}")

    tree = ET.parse(xml_file)
    root = tree.getroot()

    row_count = 0

    # Print all child tags to understand structure
    for elem in root.iter():
        print(elem.tag, elem.text)
        row_count += 1

    print(f"\n✅ Total elements scanned: {row_count}")

except Exception as e:
    print(f"❌ Error: {e}")
