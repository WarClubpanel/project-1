import os

class FileManager:
    """
    Android qurilmaning xotirasida (/sdcard/ARI_Store) fayl operatsiyalarini boshqaradi.
    """
    
    BASE_PATH = "/sdcard/ARI_Store"

    @staticmethod
    def _get_full_path(filename):
        """Faylning to'liq yo'lini qaytaradi va katalog mavjudligini tekshiradi."""
        os.makedirs(FileManager.BASE_PATH, exist_ok=True)
        # Fayl nomiga .txt kengaytmasini avtomatik qo'shamiz
        if not filename.lower().endswith('.txt'):
            filename += '.txt'
        return os.path.join(FileManager.BASE_PATH, filename)

    @staticmethod
    def create_file(filename: str, content: str = "") -> str:
        """Yangi fayl yaratadi yoki mavjud faylga matn yozadi."""
        full_path = FileManager._get_full_path(filename)
        try:
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(content)
            return f"File '{filename}' created successfully in {FileManager.BASE_PATH}."
        except Exception as e:
            return f"Error creating file '{filename}': {e}"

    @staticmethod
    def read_file(filename: str) -> str:
        """Faylning ichidagi matnni o'qiydi."""
        full_path = FileManager._get_full_path(filename)
        if os.path.exists(full_path):
            try:
                with open(full_path, "r", encoding="utf-8") as f:
                    content = f.read()
                return content
            except Exception as e:
                return f"Error reading file '{filename}': {e}"
        return f"File '{filename}' not found in {FileManager.BASE_PATH}."

    @staticmethod
    def append_to_file(filename: str, new_content: str) -> str:
        """Mavjud fayl oxiriga yangi matn qo'shadi (tahrirlash uchun)."""
        full_path = FileManager._get_full_path(filename)
        if not os.path.exists(full_path):
            return FileManager.create_file(filename, new_content)

        try:
            with open(full_path, "a", encoding="utf-8") as f:
                f.write("\n" + new_content)
            return f"Content successfully appended to '{filename}'."
        except Exception as e:
            return f"Error appending to file '{filename}': {e}"

    @staticmethod
    def delete_file(filename: str) -> str:
        """Faylni butunlay o'chiradi."""
        full_path = FileManager._get_full_path(filename)
        if os.path.exists(full_path):
            try:
                os.remove(full_path)
                return f"File '{filename}' successfully deleted."
            except Exception as e:
                return f"Error deleting file '{filename}': {e}"
        return f"File '{filename}' not found."

    @staticmethod
    def list_files() -> str:
        """Katalogdagi barcha fayllar ro'yxatini qaytaradi."""
        try:
            if not os.path.exists(FileManager.BASE_PATH):
                return "The storage directory is empty."
            
            files = [f for f in os.listdir(FileManager.BASE_PATH) if os.path.isfile(os.path.join(FileManager.BASE_PATH, f))]
            
            if files:
                return "The following files are available: " + ", ".join(files)
            return "The storage directory is currently empty."
        except Exception as e:
            return f"Error listing files: {e}"