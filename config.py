import os
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side

DATA_ROWS = [
    ("01_АНАПА (Таманская)", "271", "Январь", 950000, 1),
    ("01_АНАПА (Таманская)", "271", "Февраль", 450000, 3),
    ("01_АНАПА (Таманская)", "271", "Март", 0, None),
    ("01_АНАПА (Таманская)", "1505", "Январь", 950000, 1),
    ("01_АНАПА (Таманская)", "1505", "Февраль", 450000, 3),
    ("01_АНАПА (Таманская)", "1505", "Март", 0, None),
    ("01_АНАПА (Таманская)", "538", "Январь", 950000, 1),
    ("01_АНАПА (Таманская)", "538", "Февраль", 0, None),
    ("01_АНАПА (Таманская)", "538", "Март", 0, None),
    ("01_АНАПА (Таманская)", "537", "Январь", 950000, 1),
    ("01_АНАПА (Таманская)", "537", "Февраль", 0, None),
    ("01_АНАПА (Таманская)", "537", "Март", 0, None),
    ("02_ИНДУСТРИАЛЬНАЯ Краснодар", "Основной участок", "Январь", 1200000, 1),
    ("02_ИНДУСТРИАЛЬНАЯ Краснодар", "Основной участок", "Февраль", 850000, 2),
    ("02_ИНДУСТРИАЛЬНАЯ Краснодар", "Основной участок", "Март", 0, None)
]

MONTHS_LIST = ["Январь", "Февраль", "Март"]
DOCUMENTS_LIST = ["Акт КС-2", "Справка КС-3", "Счет-фактура", "Счет"]

FOLDER_NAME = ""
FILE_NAME = "Трекер_Акт_Выполнения.xlsx"
FULL_PATH = os.path.join(FOLDER_NAME, FILE_NAME)

FONT_HDR = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
FONT_DIR = Font(name="Calibri", size=12, bold=True, color="FFFFFF")
FONT_OBJ = Font(name="Calibri", size=11, bold=True, color="000000")
FONT_MTH = Font(name="Calibri", size=11, bold=True, italic=True, color="000000")
FONT_DATA = Font(name="Calibri", size=11)

FILL_HDR = FILL_DIR = PatternFill(start_color="1F4E78", end_color="1F4E78", fill_type="solid")
FILL_OBJ = PatternFill(start_color="D9D9D9", end_color="D9D9D9", fill_type="solid")
FILL_MTH = PatternFill(start_color="EAEAEA", end_color="EAEAEA", fill_type="solid")

THIN_BORDER = Border(
    left=Side(style='thin', color='B0B0B0'), right=Side(style='thin', color='B0B0B0'),
    top=Side(style='thin', color='B0B0B0'), bottom=Side(style='thin', color='B0B0B0')
)

ALIGN_C = Alignment(horizontal="center", vertical="center", wrap_text=True)
ALIGN_L = Alignment(horizontal="left", vertical="center", wrap_text=True)
ALIGN_R = Alignment(horizontal="right", vertical="center")

HEADERS = [
    "№ п/п", "Наименование объекта / Месяц / Документ", "Сумма (руб.)", 
    "Строительный контроль", "Сметчик заказчика", "Руководитель", "Текущий статус акта"
]
