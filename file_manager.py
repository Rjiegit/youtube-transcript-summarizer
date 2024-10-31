class FileManager:
    @staticmethod
    def save_text(text, output_file):
        print(f"Saving text to {output_file}...")
        with open(output_file, "w", encoding="utf-8") as file:
            file.write(text)
        print(f"Text saved to {output_file}")