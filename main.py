import xml.etree.ElementTree as ET
import os
import argparse
import pandas as pd

def argument_parsers():
    parser = argparse.ArgumentParser(description="Actualizar atributo 'name' en elementos <Speaker> desde CSV.")
    parser.add_argument("-p", "--path", dest="xml_path", required=True, help="Ruta del archivo XML (TRS) a modificar")
    parser.add_argument("-c", "--csv", dest="csv_path", required=True, help="Ruta del archivo CSV con mapeo de nombres")
    return parser.parse_args()

def get_name(name_file):
    base, ext = os.path.splitext(name_file)
    new_file = base + "_zuzenduta" + ext
    print(f"El archivo modificado se guardará como: {new_file}")
    return new_file

def load_name_mapping(csv_path):
    # Leer CSV con columnas: 'name' y 'correct name'
    df = pd.read_csv(csv_path, delimiter=";")
    mapping = dict(zip(df['name'].str.strip(), df['correct name'].str.strip()))
    return mapping

def write_xml_with_formatting(tree, file_path):
    declaration = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml_bytes = ET.tostring(tree.getroot(), encoding="utf-8", method="xml")
    xml_str = xml_bytes.decode("utf-8")
    xml_str = xml_str.replace(" />", "/>")
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(declaration)
        f.write(xml_str)
    print(f"Archivo guardado con formato limpio: {file_path}")

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
    print(f"Línea DOCTYPE insertada: {doctype_line}")

def update_speaker_names(xml_path, csv_path):
    tree = ET.parse(xml_path)
    root = tree.getroot()
    mapping = load_name_mapping(csv_path)
    changes = 0

    # Buscar bloque <Speakers>
    speakers_block = root.find(".//Speakers")
    if speakers_block is None:
        print("No se encontró el bloque <Speakers> en el archivo XML.")
        return

    # Recorrer cada elemento <Speaker> y actualizar el atributo 'name' si está en el CSV
    for speaker in speakers_block.findall("Speaker"):
        orig_name = speaker.get("name")
        if orig_name and orig_name in mapping:
            new_name = mapping[orig_name]
            if orig_name != new_name:
                speaker.set("name", new_name)
                print(f"Actualizado Speaker '{orig_name}' a '{new_name}'")
                changes += 1

    new_file = get_name(xml_path)
    write_xml_with_formatting(tree, new_file)

    doctype_line = get_doctype_line(xml_path)
    if doctype_line:
        insert_doctype(new_file, doctype_line)

    print(f"Total de Speaker actualizados: {changes}")

def main():
    args = argument_parsers()
    update_speaker_names(args.xml_path, args.csv_path)

if __name__ == "__main__":
    main()
