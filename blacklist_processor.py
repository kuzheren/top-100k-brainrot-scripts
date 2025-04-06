def extract_ids(file_path):
    valid_ids = []
    with open(file_path, "r", encoding="utf-8") as file:
        for line in file:
            # Удаляем пробельные символы и разбиваем строку на токены
            tokens = line.strip().split()
            # Если есть хотя бы один токен и он состоит только из цифр, добавляем его
            if tokens and tokens[0].isdigit():
                valid_ids.append(tokens[0])
    return valid_ids

# Пример использования
if __name__ == "__main__":
    file_path = "blacklist/raw.txt"  # файл, содержащий строки, подобные данным
    ids = extract_ids(file_path)
    
    with open(f"{file_path}_processed.txt", "w", encoding="utf-8") as file:
        to_write = "\n".join(ids)
        file.write(to_write)
