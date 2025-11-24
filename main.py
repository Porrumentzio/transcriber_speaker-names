import xml.etree.ElementTree as ET
import os
import argparse
import pandas as pd

def argument_parsers():
    parser = argparse.ArgumentParser(description="Update 'name' and 'accent' attributes in <Speaker> elements from CSV mapping.")
    parser.add_argument("-p", "--path", dest="xml_path", required=True, help="Path to the XML TRS file to modify")
    parser.add_argument("-c", "--csv", dest="csv_path", required=True, help="Path to the CSV file with name and accent mappings")
    return parser.parse_args()

def get_name(name_file):
    base, ext = os.path.splitext(name_file)
    new_file = base + "_zuzenduta" + ext
    print(f"Modified file will be saved as: {new_file}")
    return new_file

def load_name_accent_mapping(csv_path):
    df = pd.read_csv(csv_path, delimiter=";")
    mapping = {}
    for idx, row in df.iterrows():
        name_upper = str(row['name']).strip().upper()
        correct_name = str(row['correct name']).strip()
        accent_value = row.get('accent', '')
        if pd.isna(accent_value):
            accent_value = ''
        else:
            accent_value = str(accent_value).strip()
        mapping[name_upper] = (correct_name, accent_value)
    return mapping

def write_xml_with_formatting(tree, file_path):
    declaration = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml_bytes = ET.tostring(tree.getroot(), encoding="utf-8", method="xml")
    xml_str = xml_bytes.decode("utf-8")
    xml_str = xml_str.replace(" />", "/>")
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(declaration)
        f.write(xml_str)
    print(f"File saved with cleaned XML formatting: {file_path}")

def get_doctype_line(xml_path):
    with open(xml_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip().startswith("<!DOCTYPE"):
                return line.strip()
    return None

def insert_doctype(xml_file, doctype_line):
    with open(xml_file, "r", encoding="utf-8") as f:
        lines = f.readlines()
    for i, line in enumerate(lines):
        if line.strip().startswith("<?xml"):
            insert_index = i + 1
            break
    else:
        insert_index = 0
    lines.insert(insert_index, doctype_line + "\n")
    with open(xml_file, "w", encoding="utf-8") as f:
        f.writelines(lines)
    print(f"DOCTYPE line inserted: {doctype_line}")

def update_speaker_attributes(xml_path, csv_path):
    tree = ET.parse(xml_path)
    root = tree.getroot()
    mapping = load_name_accent_mapping(csv_path)
    correct_names_upper = {v[0].upper(): v[0] for v in mapping.values()}

    changed_names = []
    changed_accents = []

    speakers_block = root.find(".//Speakers")
    if speakers_block is None:
        print("Speakers block not found in the XML file.")
        return

    for speaker in speakers_block.findall("Speaker"):
        orig_name = speaker.get("name")
        if not orig_name:
            continue

        orig_name_upper = orig_name.strip().upper()

        if orig_name_upper in mapping:
            new_name, new_accent = mapping[orig_name_upper]
            # Case 1: name matches CSV 'name' (key), replace by exact correct_name from CSV
            if orig_name != new_name:
                speaker.set("name", new_name)
                changed_names.append(f"'{orig_name}' -> '{new_name}'")
            # Accent update if empty and accent exists in CSV
            accent_cur = speaker.get("accent", "").strip()
            if not accent_cur and new_accent:
                speaker.set("accent", new_accent)
                changed_accents.append(f"'{new_name}' accent set to '{new_accent}'")

        elif orig_name_upper in correct_names_upper:
            # Case 2: name matches a 'correct_name' in CSV ignoring case but with different capitalization
            corrected_norm = correct_names_upper[orig_name_upper]
            if orig_name != corrected_norm.upper():
                speaker.set("name", corrected_norm.upper())
                changed_names.append(f"'{orig_name}' (just uppercase) -> '{corrected_norm.upper()}'")
            # Accent update if empty (optional: find accent for this correct_name)
            accent_cur = speaker.get("accent", "").strip()
            # Find accent by searching mapping values for correct_name match ignoring case
            matched_entry = next((v for v in mapping.values() if v[0].upper() == orig_name_upper), None)
            if matched_entry:
                new_accent = matched_entry[1]
                if not accent_cur and new_accent:
                    speaker.set("accent", new_accent)
                    changed_accents.append(f"'{corrected_norm.upper()}' accent set to '{new_accent}'")

    new_file = get_name(xml_path)
    write_xml_with_formatting(tree, new_file)

    doctype_line = get_doctype_line(xml_path)
    if doctype_line:
        insert_doctype(new_file, doctype_line)

    # Grouped logs
    if changed_names:
        print("\nChanged names:")
        for entry in changed_names:
            print(f"    {entry}")
    else:
        print("\nNo names changed.")

    if changed_accents:
        print("\nChanged accents:")
        for entry in changed_accents:
            print(f"    {entry}")
    else:
        print("\nNo accents changed.")

    print(
        f"\nTotal 'name' attributes modified: {len(changed_names)}\nTotal 'accent' attributes modified: {len(changed_accents)}"
    )

def main():
    args = argument_parsers()
    update_speaker_attributes(args.xml_path, args.csv_path)

if __name__ == "__main__":
    main()
