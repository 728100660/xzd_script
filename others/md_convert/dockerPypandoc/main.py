import pypandoc

def convert_md_to_format(input_path, output_path, to_format):
    output = pypandoc.convert_file(input_path, to_format, outputfile=output_path)
    print(f"{to_format.upper()} saved to: {output_path}")

if __name__ == "__main__":
    convert_md_to_format("input.md", "output/output.pdf", "pdf")
    convert_md_to_format("input.md", "output/output.docx", "docx")
