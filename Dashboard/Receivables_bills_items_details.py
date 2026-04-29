import re
import html

FILE_PATH = r"C:\Users\Admin\Desktop\xmlrequest\bills.details.xml"


def read_file(file_path):
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


def clean_text(value):
    if value is None:
        return ""
    return html.unescape(str(value)).strip()


def parse_amount(value):
    value = clean_text(value).replace(",", "")
    if value == "":
        return 0.0
    try:
        return float(value)
    except ValueError:
        return 0.0


def parse_int(value):
    value = clean_text(value)
    if value == "":
        return ""
    try:
        return int(float(value))
    except ValueError:
        return ""


def extract_data(raw_text):
    parts = re.split(r"<BILLFIXED>", raw_text, flags=re.IGNORECASE)
    rows = []

    for part in parts[1:]:
        date = re.search(r"<BILLDATE>(.*?)</BILLDATE>", part, re.I | re.S)
        ref = re.search(r"<BILLREF>(.*?)</BILLREF>", part, re.I | re.S)
        party = re.search(r"<BILLPARTY>(.*?)</BILLPARTY>", part, re.I | re.S)
        amount = re.search(r"<BILLCL>(.*?)</BILLCL>", part, re.I | re.S)
        due = re.search(r"<BILLDUE>(.*?)</BILLDUE>", part, re.I | re.S)
        overdue = re.search(r"<BILLOVERDUE>(.*?)</BILLOVERDUE>", part, re.I | re.S)

        row = [
            clean_text(date.group(1)) if date else "",
            clean_text(ref.group(1)) if ref else "",
            clean_text(party.group(1)) if party else "",
            abs(parse_amount(amount.group(1))) if amount else 0.0,
            clean_text(due.group(1)) if due else "",
            parse_int(overdue.group(1)) if overdue else "",
        ]

        if any(row):
            rows.append(row)

    return rows


def print_table(rows):
    headers = ["Date", "RefNo", "PartyName", "PendingAmount", "DueOn", "OverdueDays"]

    # column widths
    col_widths = [len(h) for h in headers]

    for row in rows:
        for i, val in enumerate(row):
            col_widths[i] = max(col_widths[i], len(str(val)))

    # print header
    header_row = " | ".join(h.ljust(col_widths[i]) for i, h in enumerate(headers))
    print(header_row)
    print("-" * len(header_row))

    # print all rows
    for row in rows:
        print(" | ".join(str(val).ljust(col_widths[i]) for i, val in enumerate(row)))

    print("\nTOTAL ROWS:", len(rows))


def main():
    raw_text = read_file(FILE_PATH)
    rows = extract_data(raw_text)
    print_table(rows)


if __name__ == "__main__":
    main()
