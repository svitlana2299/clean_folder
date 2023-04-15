import gzip
import tarfile
import zipfile
import sys
import shutil
from pathlib import Path
import re
import os


CYRILLIC_SYMBOLS = "абвгдеёжзийклмнопрстуфхцчшщъыьэюяєіїґ"
TRANSLATION = ("a", "b", "v", "g", "d", "e", "e", "j", "z", "i", "j", "k", "l", "m", "n", "o", "p", "r", "s", "t", "u",
               "f", "h", "ts", "ch", "sh", "sch", "", "y", "", "e", "yu", "ya", "je", "i", "ji", "g")

TRANS = {}
for c, l in zip(CYRILLIC_SYMBOLS, TRANSLATION):
    TRANS[ord(c)] = l
    TRANS[ord(c.upper())] = l.upper()


def normalize(name: str) -> str:
    t_name = name.translate(TRANS)
    t_name = re.sub(r'\W', '_', t_name)
    return t_name.lower()


JPEG_IMAGES = []
PNG_IMAGES = []
JPG_IMAGES = []
SVG_IMAGES = []
AVI_VIDEO = []
MP4_VIDEO = []
MOV_VIDEO = []
MKV_VIDEO = []
DOC_DOCUMENT = []
DOCX_DOCUMENT = []
TXT_DOCUMENT = []
PDF_DOCUMENT = []
XLSX_DOCUMENT = []
PPTX_DOCUMENT = []
MP3_AUDIO = []
OGG_AUDIO = []
WAV_AUDIO = []
AMR_ARCIVES = []
ZIP_ARCIVES = []
GZ_ARCIVES = []
TAR_ARCIVES = []
MY_OTHER = []

REGISTER_EXTENSION = {
    'JPEG': JPEG_IMAGES,
    'PNG': PNG_IMAGES,
    'JPG': JPG_IMAGES,
    'SVG': SVG_IMAGES,
    'AVI': AVI_VIDEO,
    'MP4': MP4_VIDEO,
    'MOV': MOV_VIDEO,
    'MKV': MKV_VIDEO,
    'DOC': DOC_DOCUMENT,
    'DOCX': DOCX_DOCUMENT,
    'TXT': TXT_DOCUMENT,
    'PDF': PDF_DOCUMENT,
    'XLSX': XLSX_DOCUMENT,
    'PPTX': PPTX_DOCUMENT,
    'MP3': MP3_AUDIO,
    'OGG': OGG_AUDIO,
    'WAV': WAV_AUDIO,
    'AMR': AMR_ARCIVES,
    'ZIP': ZIP_ARCIVES,
    'GZ': GZ_ARCIVES,
    'TAR': TAR_ARCIVES,
}

FOLDERS = []
EXTENSION = set()
UNKNOWN = set()


def get_extension(filename: str) -> str:
    return Path(filename).suffix[1:].upper()


def scan(folder: Path):
    # перетворення folder в об'єкт Path та отримання абсолютного шляху до папки
    folder_path = Path(folder).resolve()
    for item in folder_path.iterdir():

        if item.is_dir():

            if item.name not in ('archives', 'video', 'audio', 'documents', 'images', 'other'):
                FOLDERS.append(item)
                scan(item)  # сканування вкладенної папки РЕКУРСІЯ
            continue  # перехід до наступного елемента в папці
        ext = get_extension(item.name)  # беремо розширення файлу
        full_name = folder_path / item.name  # беремо повний шлях файлу
        if ext:
            container = REGISTER_EXTENSION.get(ext)
            if container is not None:
                EXTENSION.add(ext)
                container.append(full_name)
            else:
                UNKNOWN.add(ext)
                MY_OTHER.append(full_name)
        else:
            MY_OTHER.append(full_name)

    scan(folder)
    print(f"Images jpeg: {JPEG_IMAGES}")
    print(f"Images png: {PNG_IMAGES}")
    print(f"Images jpg: {JPG_IMAGES}")
    print(f"Images svg: {SVG_IMAGES}")
    print(f"Video avi: {AVI_VIDEO}")
    print(f"Video mp4: {MP4_VIDEO}")
    print(f"Video mov: {MOV_VIDEO}")
    print(f"Video mkv: {MKV_VIDEO}")
    print(f"Document doc: {DOC_DOCUMENT}")
    print(f"Document docx: {DOCX_DOCUMENT}")
    print(f"Document txt: {TXT_DOCUMENT}")
    print(f"Document pdf: {PDF_DOCUMENT}")
    print(f"Document xlsx: {XLSX_DOCUMENT}")
    print(f"Document pptx: {PPTX_DOCUMENT}")
    print(f"Audio mp3: {MP3_AUDIO}")
    print(f"Audio ogg: {OGG_AUDIO}")
    print(f"Audio wav: {WAV_AUDIO}")
    print(f"Arcives amr: {AMR_ARCIVES}")
    print(f"Arcives zip: {ZIP_ARCIVES}")
    print(f"Arcives gz: {GZ_ARCIVES}")
    print(f"Arcives tar: {TAR_ARCIVES}")
    print('*' * 25)
    print(f'UNKNOWN: {UNKNOWN}')


def handle_media(filename: Path, target_folder: Path) -> None:
    # отримуємо нову назву файлу без розширення
    target_folder.mkdir(exist_ok=True, parents=True)
    new_filename = target_folder / filename.name  # змінено 'name' на 'filename.name'
    shutil.copy2(filename, new_filename)


def handle_other(filename: Path, target_folder: Path) -> None:
    target_folder.mkdir(exist_ok=True, parents=True)
    # отримуємо нову назву файлу без розширення
    new_filename = target_folder / normalize(filename.stem)
    new_filename = new_filename.with_suffix(
        filename.suffix)  # додаємо розширення
    filename.replace(new_filename)


def handle_archive(filename: Path, target_folder: Path) -> None:
    target_folder.mkdir(exist_ok=True, parents=True)
    folder_name = normalize(filename.stem)
    folder_for_file = target_folder / folder_name
    folder_for_file.mkdir(exist_ok=True, parents=True)
    # Визначаємо формат архіву та розпаковуємо його
    try:
        if filename.suffix == '.zip':
            with zipfile.ZipFile(filename, 'r') as zip_ref:
                zip_ref.extractall(folder_for_file)
        elif filename.suffix == '.gz':
            with gzip.open(filename, 'rb') as gz_file:
                with open(folder_for_file / filename.stem, 'wb') as extracted_file:
                    shutil.copyfileobj(gz_file, extracted_file)
        elif filename.suffix == '.tar':
            with tarfile.open(filename, 'r') as tar_ref:
                tar_ref.extractall(folder_for_file)
        else:
          # Якщо формат архіву невідомий, виводимо повідомлення та повертаємо None
            print(f"Unknown archive format: {filename.suffix}")
            return None

    except (shutil.ReadError, tarfile.TarError, gzip.BadGzipFile) as e:
        # Якщо сталася помилка при розпаковуванні архіву, виводимо повідомлення та повертаємо None
        print(f"Could not extract archive {filename}: {e}")
        return None
    filename.unlink()
    # Переносимо файли з розпакованої теки в цільову теку
    for file in folder_for_file.iterdir():
        if file.is_file():
            new_path = target_folder / 'archives' / \
                folder_name / file.name.replace(file.suffix, '')
            file.replace(new_path)


def handle_folder(folder: Path) -> None:
    try:
        folder.rmdir()
    except OSError:
        print(f'Sorry, we can not delete the folder: {folder}')


def main(folder: Path) -> None:
    scan(folder)
    for file in JPEG_IMAGES:
        handle_media(file, folder / 'images' / 'JPEG')
    for file in JPG_IMAGES:
        handle_media(file, folder / 'images' / 'JPG')
    for file in PNG_IMAGES:
        handle_media(file, folder / 'images' / 'PNG')
    for file in SVG_IMAGES:
        handle_media(file, folder / 'images' / 'SVG')

    for file in AVI_VIDEO:
        handle_media(file, folder / 'video' / 'AVI')
    for file in MP4_VIDEO:
        handle_media(file, folder / 'video' / 'MP4')
    for file in MOV_VIDEO:
        handle_media(file, folder / 'video' / 'MOV')
    for file in MKV_VIDEO:
        handle_media(file, folder / 'video' / 'MKV')

    for file in DOC_DOCUMENT:
        handle_media(file, folder / 'documents' / 'DOC')
    for file in DOCX_DOCUMENT:
        handle_media(file, folder / 'documents' / 'DOCX')
    for file in TXT_DOCUMENT:
        handle_media(file, folder / 'documents' / 'TXT')
    for file in PDF_DOCUMENT:
        handle_media(file, folder / 'documents' / 'PDF')
    for file in XLSX_DOCUMENT:
        handle_media(file, folder / 'documents' / 'XLSX')
    for file in PPTX_DOCUMENT:
        handle_media(file, folder / 'documents' / 'PPTX')

    for file in MP3_AUDIO:
        handle_media(file, folder / 'audio' / 'MP3')
    for file in OGG_AUDIO:
        handle_media(file, folder / 'audio' / 'OGG')
    for file in WAV_AUDIO:
        handle_media(file, folder / 'audio' / 'WAV')

    for file in AMR_ARCIVES:
        handle_media(file, folder / 'archives' / 'AMR')
    for file in ZIP_ARCIVES:
        handle_media(file, folder / 'archives' / 'ZIP')
    for file in GZ_ARCIVES:
        handle_media(file, folder / 'archives' / 'GZ')

    for file in MY_OTHER:
        handle_media(file, folder / 'other')

    for folder in FOLDERS[::-1]:
        handle_folder(folder)


if __name__ == '__main__':
    folder_for_scan = Path(sys.argv[1])
    main(folder_for_scan.resolve())
