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
    return new_file

def load_name_accent_mapping(csv_path):
    df = pd.read_csv(csv_path, delimiter=";")
    map_by_name = {}
    map_by_correct = {}

    for idx, row in df.iterrows():
        name_upper = str(row['name']).strip().upper()
        correct_name = str(row['correct name']).strip()
        correct_name_upper = correct_name.upper()

        accent_value = row.get('accent', '')
        if pd.isna(accent_value):
            accent_value = ''
        else:
            accent_value = str(accent_value).strip()

        map_by_name[name_upper] = (correct_name, accent_value)
        map_by_correct[correct_name_upper] = (correct_name, accent_value)

    return map_by_name, map_by_correct

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

def update_speaker_attributes(xml_path, csv_path):
    tree = ET.parse(xml_path)
    root = tree.getroot()
    map_by_name, map_by_correct = load_name_accent_mapping(csv_path)

    changed_attributes = {
        "name": [],
        "accent": []
    }

    speakers_block = root.find(".//Speakers")
    if speakers_block is None:
        print("Speakers block not found in the XML file.")
        return

    for speaker in speakers_block.findall("Speaker"):
        orig_name = speaker.get("name")
        if not orig_name:
            continue

        orig_name_upper = orig_name.strip().upper()

        mapping = None
        if orig_name_upper in map_by_name:
            mapping = map_by_name[orig_name_upper]
        elif orig_name_upper in map_by_correct:
            mapping = map_by_correct[orig_name_upper]

        if mapping:
            new_name, new_accent = mapping

            if orig_name != new_name:
                speaker.set("name", new_name)
                changed_attributes["name"].append(f"'{orig_name}' -> '{new_name}'")

            accent_cur = speaker.get("accent", "").strip()
            if not accent_cur and new_accent:
                speaker.set("accent", new_accent)
                changed_attributes["accent"].append(f"'{new_name}' accent set to '{new_accent}'")

    total_changes = len(changed_attributes["name"]) + len(changed_attributes["accent"])
    new_file = get_name(xml_path)
    write_xml_with_formatting(tree, new_file)

    doctype_line = get_doctype_line(xml_path)
    if doctype_line:
        insert_doctype(new_file, doctype_line)

    # Print grouped logs by attribute category
    for attr, changes_list in changed_attributes.items():
        if changes_list:
            print(f"\nChanged {attr}s:")
            for entry in changes_list:
                print(f"    {entry}")
        else:
            print(f"\nNo {attr}s changed.")

    print(f"\nTotal 'name' attributes modified: {len(changed_attributes['name'])}")
    print(f"Total 'accent' attributes modified: {len(changed_attributes['accent'])}")

def main():
    args = argument_parsers()
    update_speaker_attributes(args.xml_path, args.csv_path)

if __name__ == "__main__":
    main()
