"""
Anh Minh Translate — Dữ liệu tĩnh, hằng số cấu hình, từ điển tiếng lóng & 7 chuyên đề ngữ pháp
Tác giả: Mai Văn Minh — Sinh viên năm 4, Chuyên ngành Đóng tàu, СПбГМТУ (Xanh-Petecbua)
"""

from pathlib import Path
from typing import Dict, List

GEMINI_API_KEY_URL = "https://aistudio.google.com/app/apikey"
AUTHOR_NOTIFICATION_EMAIL = "anhminh11062003@gmail.com"
FIXED_AUTHOR_AVATAR_BASE64_OR_URL = ""
MAX_MEM_CACHE_SIZE = 300
MAX_AI_CACHE_SIZE = 150
MAX_HISTORY_ITEMS = 50

SESSION_TOKEN_TTL_DAYS = 30
ENC_API_KEY_PREFIX = "enc::"
SQLITE_DB_PATH = Path("anhminh_users.db")

PREFERRED_GEMINI_MODELS_FAST: List[str] = [
    "gemini-3.5-flash-lite",
    "gemini-3.8-flash",
    "gemini-3.6-flash",
    "gemini-2.5-flash-lite",
    "gemini-2.5-flash",
    "gemini-2.0-flash-lite",
    "gemini-2.0-flash",
]

PREFERRED_GEMINI_MODELS_QUALITY: List[str] = [
    "gemini-3.8-flash",
    "gemini-3.6-flash",
    "gemini-3.5-flash-lite",
    "gemini-2.5-flash",
    "gemini-2.0-flash",
]

PREFERRED_GEMINI_MODELS: List[str] = PREFERRED_GEMINI_MODELS_FAST

STUDENT_YEAR_OPTIONS: List[str] = [
    "Dự bị tiếng Nga (Подфак)",
    "Sinh viên Năm 1",
    "Sinh viên Năm 2",
    "Sinh viên Năm 3",
    "Sinh viên Năm 4",
    "Sinh viên Năm 5 (Специалитет)",
    "Cao học / Thạc sĩ",
    "Nghiên cứu sinh",
    "Khác",
]

DIRECTION_OPTIONS: List[str] = [
    "Tự động (Nga ↔ Việt)",
    "Tiếng Nga → Tiếng Việt",
    "Tiếng Việt → Tiếng Nga",
    "Đối chiếu 3 ngôn ngữ (Nga · Việt · Anh)",
]

RUSSIAN_SLANG_DICT: List[Dict[str, str]] = [
    {"word": "препод", "accent": "пре́под", "full": "преподаватель", "en": "lecturer", "vi": "Giảng viên, thầy/cô đại học", "example": "Препод сегодня добрый, всех отпустил пораньше."},
    {"word": "курсач", "accent": "курса́ч", "full": "курсовая работа", "en": "course project", "vi": "Đồ án môn học / Tiểu luận", "example": "Мне нужно сдать курсач до пятницы."},
    {"word": "лаба", "accent": "ла́ба", "full": "лабораторная работа", "en": "lab work", "vi": "Bài thí nghiệm / Thực hành Lab", "example": "У нас сегодня две лабы по физике."},
    {"word": "хвост", "accent": "хвост", "full": "академическая задолженность", "en": "failed exam", "vi": "Nợ môn (cần thi lại)", "example": "Нужно закрыть все хвосты до начала сессии."},
    {"word": "зачетка", "accent": "зачётка", "full": "зачётная книжка", "en": "record book", "vi": "Sổ điểm sinh viên", "example": "Не забудь взять зачётку на экзамен!"},
    {"word": "автомат", "accent": "автома́т", "full": "зачёт/экзамен автоматом", "en": "automatic pass", "vi": "Được miễn thi (qua môn tự động)", "example": "Я ходил на все лекции и получил автомат!"},
    {"word": "пара", "accent": "па́ра", "full": "учебная пара (90 минут)", "en": "90-min class", "vi": "Ca học đại học (90 phút)", "example": "Во сколько завтра первая пара?"},
    {"word": "общага", "accent": "обща́га", "full": "общежитие", "en": "dormitory", "vi": "Ký túc xá sinh viên", "example": "Вечером собираемся в общаге готовиться к сессии."},
    {"word": "стипуха", "accent": "стипу́ха", "full": "стипендия", "en": "scholarship", "vi": "Tiền học bổng hàng tháng", "example": "Сегодня пришла стипуха!"},
    {"word": "окно", "accent": "окно́", "full": "перерыв между парами", "en": "free period", "vi": "Ca trống giữa các tiết học", "example": "У нас окно между второй и четвёртой парой."},
    {"word": "сессия", "accent": "се́ссия", "full": "экзаменационная сессия", "en": "exam period", "vi": "Kỳ thi học kỳ", "example": "Зимняя сессия начинается в январе."},
    {"word": "пересдача", "accent": "пересда́ча", "full": "повторная сдача", "en": "retake exam", "vi": "Thi lại", "example": "Комиссия назначила пересдачу на следующую неделю."},
    {"word": "деканат", "accent": "декана́т", "full": "администрация факультета", "en": "dean's office", "vi": "Văn phòng khoa / Giáo vụ khoa", "example": "Возьми справку об обучении в деканате."},
    {"word": "шпора", "accent": "шпо́ра", "full": "шпаргалка", "en": "cheat sheet", "vi": "Phao thi / Tờ ghi chú nhỏ", "example": "Писать шпоры полезно для памяти."},
    {"word": "домашка", "accent": "дома́шка", "full": "домашнее задание", "en": "homework", "vi": "Bài tập về nhà", "example": "Скинь домашку по матану, пожалуйста!"},
    {"word": "матан", "accent": "мата́н", "full": "математический анализ", "en": "calculus", "vi": "Môn Giải tích toán học", "example": "Завтра коллоквиум по матану."},
    {"word": "сопромат", "accent": "сопрома́т", "full": "сопротивление материалов", "en": "strength of materials", "vi": "Môn Sức bền vật liệu", "example": "Сдал сопромат — можно жениться!"},
    {"word": "научник", "accent": "нау́чник", "full": "научный руководитель", "en": "advisor", "vi": "Giảng viên hướng dẫn đồ án", "example": "Мой научник одобрил тему диплома."},
    {"word": "инфа", "accent": "инфа́", "full": "информация", "en": "info", "vi": "Thông tin (nhóm chat Telegram/VK)", "example": "Спасибо за инфу, передам группе!"},
    {"word": "преза", "accent": "пре́за", "full": "презентация", "en": "presentation", "vi": "Bài thuyết trình / Slide", "example": "Ты уже сделал презу к завтрашнему семинару?"},
    {"word": "коллок", "accent": "колло́к", "full": "коллоквиум", "en": "colloquium", "vi": "Kiểm tra vấn đáp giữa kỳ", "example": "В среду будет коллок по гидромеханике."},
    {"word": "госы", "accent": "го́сы", "full": "государственные экзамены", "en": "state exams", "vi": "Kỳ thi tốt nghiệp quốc gia", "example": "В июне сдаём госы и защищаем диплом."},
    {"word": "прогул", "accent": "прогу́л", "full": "пропуск без причины", "en": "skipping class", "vi": "Nghỉ học không phép", "example": "За прогулы без справки могут не поставить зачёт."},
    {"word": "отработка", "accent": "отрабо́тка", "full": "отработка занятия", "en": "make-up lab", "vi": "Học bù / Làm bù bài thí nghiệm", "example": "Мне нужно прийти на отработку лабы в пятницу."},
    {"word": "студак", "accent": "студа́к", "full": "студенческий билет", "en": "student ID", "vi": "Thẻ sinh viên", "example": "Покажи студак на входе в корпус."},
    {"word": "пропуск", "accent": "про́пуск", "full": "электронный пропуск", "en": "access pass", "vi": "Thẻ từ ra vào trường / KTX", "example": "Я забыл пропуск в комнате."},
    {"word": "столовка", "accent": "столо́вка", "full": "студенческая столовая", "en": "cafeteria", "vi": "Căng-tin / Nhà ăn sinh viên", "example": "Пойдём в столовку на большой перемене."},
    {"word": "академ", "accent": "акаде́м", "full": "академический отпуск", "en": "academic leave", "vi": "Bảo lưu kết quả học tập", "example": "Он взял академ на один год."},
    {"word": "староста", "accent": "ста́роста", "full": "староста группы", "en": "class monitor", "vi": "Lớp trưởng", "example": "Староста отметила всех в журнале."},
    {"word": "медосмотр", "accent": "медосмо́тр", "full": "медицинский осмотр", "en": "medical check-up", "vi": "Khám sức khỏe định kỳ (bắt buộc)", "example": "Нужно пройти медосмотр до конца месяца."},
]

STARTER_DECK_SURVIVAL: List[Dict[str, str]] = [
    {"ru_accent": "Здра́вствуйте", "pronunciation": "zdơ-rát-xờ-vuy-che", "vi": "Xin chào (lịch sự)", "en": "Hello (formal)", "example": "Здра́вствуйте, преподава́тель!"},
    {"ru_accent": "Приве́т", "pronunciation": "pri-viết", "vi": "Chào bạn (thân mật)", "en": "Hi (informal)", "example": "Приве́т, как дела́?"},
    {"ru_accent": "До́брое у́тро", "pronunciation": "đô-brơ-yê ú-trơ", "vi": "Chào buổi sáng", "en": "Good morning", "example": "До́брое у́тро! Пора́ на па́ру."},
    {"ru_accent": "До́брый день", "pronunciation": "đô-brưy đên", "vi": "Chào buổi trưa/chiều", "en": "Good afternoon", "example": "До́брый день, мо́жно войти́?"},
    {"ru_accent": "До́брый ве́чер", "pronunciation": "đô-brưy vê-cher", "vi": "Chào buổi tối", "en": "Good evening", "example": "До́брый ве́чер, соседа́!"},
    {"ru_accent": "Спаси́бо", "pronunciation": "xpa-xi-bơ", "vi": "Cảm ơn", "en": "Thank you", "example": "Спаси́бо большо́е за по́мощь!"},
    {"ru_accent": "Пожа́луйста", "pronunciation": "pa-zha-lu-xta", "vi": "Không có gì / Làm ơn", "en": "Please / You're welcome", "example": "Да́йте, пожа́луйста, во́ду."},
    {"ru_accent": "Извини́те", "pronunciation": "iz-vi-ni-che", "vi": "Xin lỗi (lịch sự)", "en": "Excuse me / Sorry", "example": "Извини́те, где метро́?"},
    {"ru_accent": "До свида́ния", "pronunciation": "đa xờ-vi-đa-ni-ya", "vi": "Tạm biệt (lịch sự)", "en": "Goodbye", "example": "До свида́ния, до за́втра!"},
    {"ru_accent": "Пока́", "pronunciation": "pa-ka", "vi": "Tạm biệt (bạn bè)", "en": "Bye", "example": "Пока́, уви́димся ве́чером!"},
    {"ru_accent": "Ско́лько сто́ит?", "pronunciation": "xkôn-kơ xto-it", "vi": "Bao nhiêu tiền?", "en": "How much does it cost?", "example": "Ско́лько сто́ит э́тот хлеб?"},
    {"ru_accent": "Магази́н", "pronunciation": "ma-ga-zin", "vi": "Cửa hàng / Siêu thị nhỏ", "en": "Shop / Store", "example": "Я иду́ в магази́н за продуктами."},
    {"ru_accent": "Суперма́ркет", "pronunciation": "xu-pêr-már-kêt", "vi": "Siêu thị lớn", "en": "Supermarket", "example": "Ря́дом с обща́гой есть суперма́ркет."},
    {"ru_accent": "Ка́сса", "pronunciation": "ká-xa", "vi": "Quầy thu ngân", "en": "Cashier / Checkout", "example": "Опла́та на ка́ссе картой."},
    {"ru_accent": "Паке́т", "pronunciation": "pa-kiết", "vi": "Túi ni-lông / Túi đựng đồ", "en": "Plastic bag", "example": "Ну́жен паке́т? — Да, спаси́бо."},
    {"ru_accent": "Чек", "pronunciation": "chếch", "vi": "Hóa đơn thanh toán", "en": "Receipt", "example": "Возьми́те, пожа́луйста, ваш чек."},
    {"ru_accent": "Вода́", "pronunciation": "va-đa", "vi": "Nước uống", "en": "Water", "example": "Мне ну́жна буты́лка воды́."},
    {"ru_accent": "Метро́", "pronunciation": "mê-trô", "vi": "Tàu điện ngầm", "en": "Metro / Subway", "example": "Станция метро́ недалеко́ отсю́да."},
    {"ru_accent": "Авто́бус", "pronunciation": "áp-tô-bux", "vi": "Xe buýt", "en": "Bus", "example": "Авто́бус идёт до университе́та."},
    {"ru_accent": "Остано́вка", "pronunciation": "a-xta-nốp-ka", "vi": "Trạm dừng xe buýt", "en": "Bus stop", "example": "Сле́дующая остано́вка — моя́."},
    {"ru_accent": "Нале́во / Напра́во", "pronunciation": "na-lê-vơ / na-pra-vơ", "vi": "Bên trái / Bên phải", "en": "To the left / To the right", "example": "Поверни́те напра́во за угло́м."},
    {"ru_accent": "Пря́мо", "pronunciation": "pria-mơ", "vi": "Đi thẳng", "en": "Straight ahead", "example": "Иди́те пря́мо пять мину́т."},
    {"ru_accent": "Оди́н / Два / Три", "pronunciation": "a-đin / dơ-va / tri", "vi": "Một / Hai / Ba", "en": "One / Two / Three", "example": "У меня́ оди́н вопро́с."},
    {"ru_accent": "Четы́ре / Пять", "pronunciation": "chi-tư-ri / piát", "vi": "Bốn / Năm", "en": "Four / Five", "example": "Через пять мину́т выхо́дим."},
    {"ru_accent": "Де́сять / Сто", "pronunciation": "đê-xít / xtô", "vi": "Mười / Một trăm", "en": "Ten / One hundred", "example": "Э́то сто́ит сто рубле́й."},
    {"ru_accent": "Помоги́те!", "pronunciation": "pa-ma-gi-che", "vi": "Hãy giúp tôi với!", "en": "Help me!", "example": "Помоги́те, я не говорю́ по-ру́сски."},
]

STARTER_DECK_PODFAK: List[Dict[str, str]] = [
    {"ru_accent": "Подготови́тельный факульте́т", "pronunciation": "pơt-ga-ta-vi-chên-nưy fa-kun-chết", "vi": "Khoa Dự bị tiếng Nga (Подфак)", "en": "Preparatory faculty", "example": "Я учу́сь на подготови́тельном факульте́те."},
    {"ru_accent": "Преподава́тель", "pronunciation": "pri-pa-da-va-chên", "vi": "Giảng viên / Thầy cô giáo", "en": "Teacher / Lecturer", "example": "Наш преподава́тель объясня́ет о́чень я́сно."},
    {"ru_accent": "Студе́нт / Студе́нтка", "pronunciation": "xtu-đênt / xtu-đênt-ka", "vi": "Sinh viên nam / Sinh viên nữ", "en": "Student (male/female)", "example": "Мы студе́нты из Вьетна́ма."},
    {"ru_accent": "Аудито́рия", "pronunciation": "a-u-đi-tô-ri-ya", "vi": "Phòng học / Giảng đường", "en": "Classroom / Lecture hall", "example": "Заня́тие в аудито́рии но́мер три́ста."},
    {"ru_accent": "Уро́к / Па́ра", "pronunciation": "u-rốc / pa-ra", "vi": "Tiết học / Ca học 90 phút", "en": "Lesson / 90-min class", "example": "Сего́дня у нас три па́ры."},
    {"ru_accent": "Переме́на", "pronunciation": "pi-ri-mê-na", "vi": "Giờ giải lao", "en": "Break between classes", "example": "На переме́не пойдём пить чай."},
    {"ru_accent": "Дома́шнее зада́ние", "pronunciation": "da-mát-nhi-yê za-đa-ni-yê", "vi": "Bài tập về nhà", "en": "Homework", "example": "Я уже́ сде́лал дома́шнее зада́ние."},
    {"ru_accent": "Упражне́ние", "pronunciation": "u-prazh-nhê-ni-yê", "vi": "Bài tập thực hành", "en": "Exercise", "example": "Откро́йте упражне́ние де́сять."},
    {"ru_accent": "Уче́бник", "pronunciation": "u-chếp-nhik", "vi": "Sách giáo trình", "en": "Textbook", "example": "Возьми́те уче́бник по ру́сскому языку́."},
    {"ru_accent": "Тетра́дь", "pronunciation": "chi-trát", "vi": "Quyển vở viết", "en": "Notebook", "example": "Запиши́те но́вые слова́ в тетра́дь."},
    {"ru_accent": "Ру́чка / Каранда́ш", "pronunciation": "rút-ka / ka-ran-đát", "vi": "Bút bi / Bút chì", "en": "Pen / Pencil", "example": "Мо́жно взять твою́ ру́чку?"},
    {"ru_accent": "Слова́рь", "pronunciation": "xla-va", "vi": "Từ điển", "en": "Dictionary", "example": "Посмотри́ э́то сло́во в словаре́."},
    {"ru_accent": "Повтори́те, пожа́луйста", "pronunciation": "pơp-ta-ri-che, pa-zha-lu-xta", "vi": "Xin hãy nhắc lại giúp em", "en": "Please repeat", "example": "Повтори́те, пожа́луйста, ещё раз."},
    {"ru_accent": "Ме́дленнее, пожа́луйста", "pronunciation": "mết-lên-nơ-yê, pa-zha-lu-xta", "vi": "Xin nói chậm lại một chút", "en": "Slower, please", "example": "Говори́те ме́дленнее, пожа́луйста."},
    {"ru_accent": "Я понима́ю / Не понима́ю", "pronunciation": "ya pa-ni-ma-yu / nhi pa-ni-ma-yu", "vi": "Tôi hiểu / Tôi không hiểu", "en": "I understand / I don't understand", "example": "Извини́те, я пока́ не понима́ю."},
    {"ru_accent": "Что э́то зна́чит?", "pronunciation": "xtô ê-tơ zna-chit", "vi": "Cái này nghĩa là gì?", "en": "What does this mean?", "example": "Скажи́те, что э́то зна́чит по-вьетна́мски?"},
    {"ru_accent": "Как э́то по-ру́сски?", "pronunciation": "kak ê-tơ pa-rút-xki", "vi": "Tiếng Nga cái này nói thế nào?", "en": "How do you say this in Russian?", "example": "Как э́то по-ру́сски: 'bảng đen'?"},
    {"ru_accent": "Мо́жно вопро́с?", "pronunciation": "môzh-nơ va-prôx", "vi": "Em hỏi một câu được không ạ?", "en": "May I ask a question?", "example": "Извини́те, мо́жно вопро́с?"},
    {"ru_accent": "Расписа́ние", "pronunciation": "rơx-pi-xa-ni-yê", "vi": "Thời khóa biểu", "en": "Schedule / Timetable", "example": "Посмотри́ расписа́ние на по́чте."},
    {"ru_accent": "Понеде́льник / Вто́рник", "pronunciation": "pa-ni-đên-nhik / pơ-tôr-nhik", "vi": "Thứ Hai / Thứ Ba", "en": "Monday / Tuesday", "example": "В понеде́льник у нас фоне́тика."},
    {"ru_accent": "Среда́ / Четве́рг", "pronunciation": "xrê-đa / chit-viếrc", "vi": "Thứ Tư / Thứ Năm", "en": "Wednesday / Thursday", "example": "В среду бу́дет дикта́нт."},
    {"ru_accent": "Пя́тница / Суббо́та", "pronunciation": "piát-nhi-txa / xu-bô-ta", "vi": "Thứ Sáu / Thứ Bảy", "example": "В суббо́ту у нас то́лько одна́ па́ра.", "en": "Friday / Saturday"},
    {"ru_accent": "Воскресе́нье", "pronunciation": "vơx-krê-xên-yê", "vi": "Chủ Nhật", "en": "Sunday", "example": "В воскресе́нье мы отдыха́ем."},
    {"ru_accent": "Сего́дня / За́втра", "pronunciation": "xi-vốt-nha / záp-tra", "vi": "Hôm nay / Ngày mai", "en": "Today / Tomorrow", "example": "Сего́дня холо́дная пого́да."},
    {"ru_accent": "Вчера́", "pronunciation": "pơ-chê-ra", "vi": "Hôm qua", "en": "Yesterday", "example": "Вчера́ мы писа́ли тест."},
    {"ru_accent": "Экза́мен / Зачёт", "pronunciation": "êc-za-mên / za-chốt", "vi": "Bài thi / Đạt môn (tính chỉ)", "en": "Exam / Pass test", "example": "В ма́е мы сдаём экза́мен по русскому."},
]

STARTER_DECK_DORM_DOCS: List[Dict[str, str]] = [
    {"ru_accent": "Общежи́тие", "pronunciation": "ap-si-zhư-chi-yê", "vi": "Ký túc xá", "en": "Dormitory", "example": "На́ше общежи́тие нахо́дится ря́дом с метро́."},
    {"ru_accent": "Ко́мната", "pronunciation": "kôm-na-ta", "vi": "Phòng ở", "en": "Room", "example": "Моя́ ко́мната на пя́том этаже́."},
    {"ru_accent": "Сосе́д по ко́мнате", "pronunciation": "xa-xiết pa kôm-na-chê", "vi": "Bạn cùng phòng", "en": "Roommate", "example": "Мой сосе́д по ко́мнате — то́же из Вьетна́ма."},
    {"ru_accent": "Коменда́нт", "pronunciation": "ka-mên-đánt", "vi": "Quản lý ký túc xá", "en": "Dormitory manager", "example": "Обрати́тесь к коменда́нту по по́воду ключей."},
    {"ru_accent": "Па́спорт", "pronunciation": "pát-xpơrt", "vi": "Hộ chiếu", "en": "Passport", "example": "Всегда́ носи́те с собо́й па́спорт."},
    {"ru_accent": "Ви́за", "pronunciation": "vi-za", "vi": "Thị thực (Visa)", "en": "Visa", "example": "Ну́жно продли́ть ви́зу заранее."},
    {"ru_accent": "Миграцио́нная ка́рта", "pronunciation": "mi-gra-txi-ôn-na-ya kár-ta", "vi": "Thẻ di trú (nhận ở sân bay)", "en": "Migration card", "example": "Не потеря́йте миграцио́нную ка́рту!"},
    {"ru_accent": "Регистра́ция", "pronunciation": "ri-gix-trá-txi-ya", "vi": "Giấy đăng ký tạm trú", "en": "Temporary registration", "example": "Когда́ бу́дет гото́ва моя́ регистра́ция?"},
    {"ru_accent": "Студе́нческий биле́т", "pronunciation": "xtu-đên-chix-ki bi-lết", "vi": "Thẻ sinh viên", "en": "Student ID card", "example": "Покажи́те студе́нческий биле́т на вхо́де."},
    {"ru_accent": "Про́пуск", "pronunciation": "prô-puxk", "vi": "Thẻ từ ra vào trường / KTX", "en": "Access pass", "example": "Я оста́вил про́пуск на столе́."},
    {"ru_accent": "Страхо́вка", "pronunciation": "xtra-khốp-ka", "vi": "Bảo hiểm y tế", "en": "Medical insurance", "example": "Без страхо́вки нельзя́ жить в общежи́тии."},
    {"ru_accent": "Медпу́нкт / Поликли́ника", "pronunciation": "mêt-punc / pa-li-kli-ni-ka", "vi": "Phòng y tế / Phòng khám đa khoa", "en": "Medical office / Clinic", "example": "Если температу́ра, иди́те в медпу́нкт."},
    {"ru_accent": "Спра́вка", "pronunciation": "xpráp-ka", "vi": "Giấy xác nhận / Giấy khám sức khỏe", "en": "Official certificate", "example": "Возьми́те спра́вку об обуче́нии в декана́те."},
    {"ru_accent": "Декана́т", "pronunciation": "đi-ka-nát", "vi": "Văn phòng khoa", "en": "Dean's office", "example": "Декана́т рабо́тает с девяти́ до пяти́."},
    {"ru_accent": "Ключ", "pronunciation": "kơ-liút", "vi": "Chìa khóa phòng", "en": "Key", "example": "Возьми́ ключ на ва́хте."},
    {"ru_accent": "Ва́хта", "pronunciation": "vák-ta", "vi": "Quầy bảo vệ / Lễ tân KTX", "en": "Security desk", "example": "Сда́йте ключ на ва́хту перед вы́ходом."},
    {"ru_accent": "Ку́хня", "pronunciation": "kúkh-nha", "vi": "Nhà bếp chung", "en": "Kitchen", "example": "На ку́хне есть плита́ и ра́ковина."},
    {"ru_accent": "Душ / Туале́т", "pronunciation": "đút / tu-a-lết", "vi": "Phòng tắm / Nhà vệ sinh", "en": "Shower / Toilet", "example": "Душ рабо́тает круглосу́точно."},
    {"ru_accent": "Пра́чечная", "pronunciation": "prá-chêt-na-ya", "vi": "Phòng giặt đồ", "en": "Laundry room", "example": "Стира́льные маши́ны сто́ят в пра́чечной."},
    {"ru_accent": "Одея́ло / Поду́шка", "pronunciation": "a-đê-ya-lơ / pa-đút-ka", "vi": "Chăn / Gối", "en": "Blanket / Pillow", "example": "Вы́дали одея́ло и поду́шку на скла́де."},
    {"ru_accent": "Холоди́льник", "pronunciation": "kha-la-đin-nhik", "vi": "Tủ lạnh", "en": "Refrigerator", "example": "Положи́ молоко́ в холоди́льник."},
    {"ru_accent": "Интерне́т / Вайфа́й", "pronunciation": "in-têr-nết / vai-fái", "vi": "Mạng Internet / Wi-Fi", "en": "Internet / Wi-Fi", "example": "Како́й паро́ль от вайфа́я?"},
    {"ru_accent": "Эта́ж", "pronunciation": "ê-tát", "vi": "Tầng lầu", "en": "Floor", "example": "Лифт не рабо́тает, пойдём на тре́тий эта́ж."},
    {"ru_accent": "Опла́та", "pronunciation": "a-pla-ta", "vi": "Tiền đóng phí (KTX/học phí)", "en": "Payment", "example": "Опла́та за общежи́тие до деся́того числа́."},
    {"ru_accent": "Квита́нция", "pronunciation": "kơ-vi-tán-txi-ya", "vi": "Biên lai đóng tiền", "en": "Payment slip", "example": "Сохрани́те квита́нцию об опла́те."},
    {"ru_accent": "Анке́та / Заявле́ние", "pronunciation": "an-kê-ta / za-yav-lê-ni-yê", "vi": "Tờ khai / Đơn xin", "en": "Form / Application", "example": "Запо́лните заявле́ние на регистра́цию."},
]

STARTER_DECK_CORE_VERBS_ADJ: List[Dict[str, str]] = [
    {"ru_accent": "де́лать / сде́лать", "pronunciation": "đê-lơt / zdê-lơt", "vi": "làm (НСВ / СВ)", "en": "to do / make", "example": "Что ты де́лаешь? — Я уже́ сде́лал зада́ние."},
    {"ru_accent": "говори́ть / сказа́ть", "pronunciation": "ga-va-rit / xka-zat", "vi": "nói (НСВ / СВ)", "en": "to speak / say", "example": "Он хорошо́ говори́т по-ру́сски."},
    {"ru_accent": "чита́ть / прочита́ть", "pronunciation": "chi-tát / pra-chi-tát", "vi": "đọc (НСВ / СВ)", "en": "to read", "example": "Я ка́ждый ве́чер чита́ю ру́сский текст."},
    {"ru_accent": "писа́ть / написа́ть", "pronunciation": "pi-xát / na-pi-xát", "vi": "viết (НСВ / СВ)", "en": "to write", "example": "Напиши́ мне сообще́ние в Телегра́ме."},
    {"ru_accent": "слу́шать / послу́шать", "pronunciation": "xlú-sơt / pa-xlú-sơt", "vi": "nghe (НСВ / СВ)", "en": "to listen", "example": "Слу́шайте внима́тельно диало́г."},
    {"ru_accent": "понима́ть / поня́ть", "pronunciation": "pa-ni-mat / pa-nhát", "vi": "hiểu (НСВ / СВ)", "en": "to understand", "example": "Наконе́ц я по́нял э́ту грамма́тику!"},
    {"ru_accent": "зна́ть / узна́ть", "pronunciation": "znat / uz-nát", "vi": "biết / tìm hiểu (НСВ / СВ)", "en": "to know / find out", "example": "Я не зна́ю, где декана́т."},
    {"ru_accent": "учи́ть / вы́учить", "pronunciation": "u-chit / vư-u-chit", "vi": "học thuộc / học (НСВ / СВ)", "en": "to learn / memorize", "example": "Ну́жно вы́учить де́сять но́вых слов."},
    {"ru_accent": "рабо́тать / порабо́тать", "pronunciation": "ra-bô-tơt / pa-ra-bô-tơt", "vi": "làm việc / hoạt động (НСВ / СВ)", "en": "to work", "example": "Сего́дня столо́вая не рабо́тает."},
    {"ru_accent": "покупа́ть / купи́ть", "pronunciation": "pa-ku-pát / ku-pít", "vi": "mua (НСВ / СВ)", "en": "to buy", "example": "Я хочу́ купи́ть тёплую ку́ртку."},
    {"ru_accent": "плати́ть / заплати́ть", "pronunciation": "pla-chit / za-pla-chit", "vi": "trả tiền (НСВ / СВ)", "en": "to pay", "example": "Мо́жно заплати́ть ка́ртой?"},
    {"ru_accent": "помога́ть / помо́чь", "pronunciation": "pa-ma-gát / pa-mốt", "vi": "giúp đỡ (НСВ / СВ)", "en": "to help", "example": "Друг помо́г мне с перево́дом."},
    {"ru_accent": "спра́шивать / спроси́ть", "pronunciation": "xprá-sư-vơt / xpra-xít", "vi": "hỏi (НСВ / СВ)", "en": "to ask", "example": "Спроси́те у коменда́нта."},
    {"ru_accent": "отвеча́ть / отве́тить", "pronunciation": "at-vi-chát / at-vê-chit", "vi": "trả lời (НСВ / СВ)", "en": "to answer", "example": "Она́ бы́стро отве́тила на вопро́с."},
    {"ru_accent": "бра́ть / взять", "pronunciation": "brat / vơ-ziát", "vi": "lấy / mượn (НСВ / СВ)", "en": "to take", "example": "Не забу́дь взять па́спорт!"},
    {"ru_accent": "дава́ть / да́ть", "pronunciation": "da-vát / đat", "vi": "đưa / cho (НСВ / СВ)", "en": "to give", "example": "Да́йте, пожа́луйста, чек."},
    {"ru_accent": "жи́ть / прожи́ть", "pronunciation": "zhưt / pra-zhưt", "vi": "sống / ở (НСВ / СВ)", "en": "to live", "example": "Я живу́ в Петербу́рге полго́да."},
    {"ru_accent": "хоте́ть / захоте́ть", "pronunciation": "kha-chết / za-kha-chết", "vi": "muốn (НСВ / СВ)", "en": "to want", "example": "Я хочу́ вы́учить ру́сский язы́к."},
    {"ru_accent": "хоро́ший ↔ плохо́й", "pronunciation": "kha-rô-sưy / pla-khôi", "vi": "tốt ↔ xấu / kém", "en": "good ↔ bad", "example": "Сего́дня хоро́шая пого́да."},
    {"ru_accent": "большо́й ↔ ма́ленький", "pronunciation": "ban-sôi / ma-lên-ki", "vi": "to lớn ↔ nhỏ bé", "en": "big ↔ small", "example": "В Петербу́рге большо́е метро́."},
    {"ru_accent": "но́вый ↔ ста́рый", "pronunciation": "nô-vưy / xtá-rưy", "vi": "mới ↔ cũ / già", "en": "new ↔ old", "example": "У нас но́вый уче́бник."},
    {"ru_accent": "дорого́й ↔ дешёвый", "pronunciation": "đa-ra-gôi / đi-sô-vưy", "vi": "đắt tiền ↔ rẻ tiền", "en": "expensive ↔ cheap", "example": "Э́то о́чень дешёвый биле́т."},
    {"ru_accent": "бы́стрый ↔ ме́дленный", "pronunciation": "bư-xtrưy / mết-lên-nưy", "vi": "nhanh ↔ chậm", "en": "fast ↔ slow", "example": "Ну́жен бы́стрый интерне́т."},
    {"ru_accent": "лёгкий ↔ тру́дный", "pronunciation": "liôkh-ki / trút-nưy", "vi": "dễ / nhẹ ↔ khó / nặng", "en": "easy ↔ difficult", "example": "Э́то лёгкое упражне́ние."},
    {"ru_accent": "холо́дный ↔ тёплый", "pronunciation": "kha-lôt-nưy / chiôp-lưy", "vi": "lạnh ↔ ấm áp", "en": "cold ↔ warm", "example": "Зимо́й о́чень холо́дный ве́тер."},
    {"ru_accent": "откры́тый ↔ закры́тый", "pronunciation": "at-krư-tưy / za-krư-tưy", "vi": "mở cửa ↔ đóng cửa", "en": "open ↔ closed", "example": "Магази́н ещё откры́т?"},
]

STARTER_VOCAB_DECKS: Dict[str, List[Dict[str, str]]] = {
    "1. Sinh tồn tuần đầu tại Nga": STARTER_DECK_SURVIVAL,
    "2. Lớp học Dự bị (Подфак)": STARTER_DECK_PODFAK,
    "3. Ký túc xá & Giấy tờ": STARTER_DECK_DORM_DOCS,
    "4. Động từ & Tính từ cốt lõi A1": STARTER_DECK_CORE_VERBS_ADJ,
}


RUSSIAN_ALPHABET_SAMPLES: List[Dict[str, str]] = [
    # Nhóm 1: Nhìn giống & đọc gần giống (6)
    {"letter": "А а", "group": "Nhóm 1", "sound": "a", "example": "а́дрес (địa chỉ)"},
    {"letter": "Е е", "group": "Nhóm 1", "sound": "yê / ê", "example": "е́сли (nếu)"},
    {"letter": "К к", "group": "Nhóm 1", "sound": "k", "example": "кни́га (quyển sách)"},
    {"letter": "М м", "group": "Nhóm 1", "sound": "m", "example": "ма́ма (mẹ)"},
    {"letter": "О о", "group": "Nhóm 1", "sound": "ô (có trọng âm) / a (không trọng âm)", "example": "окно́ (cửa sổ)"},
    {"letter": "Т т", "group": "Nhóm 1", "sound": "t (không bật hơi)", "example": "тетра́дь (quyển vở)"},
    # Nhóm 2: Bẫy thị giác (6)
    {"letter": "В в", "group": "Nhóm 2", "sound": "v (như v Việt)", "example": "вода́ (nước uống)"},
    {"letter": "Н н", "group": "Nhóm 2", "sound": "n (như n Việt)", "example": "но́вый (mới)"},
    {"letter": "Р р", "group": "Nhóm 2", "sound": "r (rung đầu lưỡi)", "example": "ру́чка (bút bi)"},
    {"letter": "С с", "group": "Nhóm 2", "sound": "x / s nhẹ", "example": "сло́во (từ vựng)"},
    {"letter": "У у", "group": "Nhóm 2", "sound": "u", "example": "уро́к (tiết học)"},
    {"letter": "Х х", "group": "Nhóm 2", "sound": "kh (như kh Việt)", "example": "хлеб (bánh mì)"},
    # Nhóm 3: Chữ Cyrillic đặc trưng & 2 dấu (21)
    {"letter": "Б б", "group": "Nhóm 3", "sound": "b", "example": "биле́т (vé / thẻ)"},
    {"letter": "Г г", "group": "Nhóm 3", "sound": "g (như g Việt)", "example": "го́род (thành phố)"},
    {"letter": "Д д", "group": "Nhóm 3", "sound": "đ", "example": "дом (nhà)"},
    {"letter": "Ё ё", "group": "Nhóm 3", "sound": "yô (luôn mang trọng âm)", "example": "ёлка (cây thông)"},
    {"letter": "Ж ж", "group": "Nhóm 3", "sound": "gi / zh (uốn lưỡi)", "example": "жизнь (cuộc sống)"},
    {"letter": "З з", "group": "Nhóm 3", "sound": "z (rung cổ họng)", "example": "за́втра (ngày mai)"},
    {"letter": "И и", "group": "Nhóm 3", "sound": "i", "example": "и́мя (tên)"},
    {"letter": "Й й", "group": "Nhóm 3", "sound": "i ngắn (ghép vần -ai/-oi)", "example": "музе́й (bảo tàng)"},
    {"letter": "Л л", "group": "Nhóm 3", "sound": "l", "example": "ла́мпа (cái đèn)"},
    {"letter": "П п", "group": "Nhóm 3", "sound": "p (mím môi, không bật hơi)", "example": "па́спорт (hộ chiếu)"},
    {"letter": "Ф ф", "group": "Nhóm 3", "sound": "ph / f", "example": "факульте́т (khoa)"},
    {"letter": "Ц ц", "group": "Nhóm 3", "sound": "tx (bật nhanh đầu lưỡi)", "example": "цена́ (giá cả)"},
    {"letter": "Ч ч", "group": "Nhóm 3", "sound": "ch (mềm, nhẹ)", "example": "час (giờ / tiếng)"},
    {"letter": "Ш ш", "group": "Nhóm 3", "sound": "s (uốn lưỡi cứng)", "example": "шко́ла (trường học)"},
    {"letter": "Щ щ", "group": "Nhóm 3", "sound": "x-ch (mềm dài)", "example": "общежи́тие (ký túc xá)"},
    {"letter": "Ъ ъ", "group": "Nhóm 3", "sound": "Dấu cứng (tách âm, không đọc)", "example": "объявле́ние (thông báo)"},
    {"letter": "Ы ы", "group": "Nhóm 3", "sound": "ư / ưi (kéo lưỡi lùi sau)", "example": "сын (con trai)"},
    {"letter": "Ь ь", "group": "Nhóm 3", "sound": "Dấu mềm (làm mềm phụ âm trước)", "example": "слова́рь (từ điển)"},
    {"letter": "Э э", "group": "Nhóm 3", "sound": "ê (mở miệng hơn е)", "example": "экза́мен (kỳ thi)"},
    {"letter": "Ю ю", "group": "Nhóm 3", "sound": "yu / iu", "example": "юг (phương Nam)"},
    {"letter": "Я я", "group": "Nhóm 3", "sound": "ya / ia", "example": "я́блоко (quả táo)"},
]


KNOWLEDGE_HUB_TOPICS: List[str] = [
    "0. Nhập môn: Chữ cái, Cách đọc & Giống",
    "1. 6 Cách · Danh từ",
    "2. Tính từ & Đại từ",
    "3. Động từ & Thể (НСВ/СВ)",
    "4. Động từ chuyển động",
    "5. Giới từ & Thời gian",
    "6. Số từ & Lượng từ",
    "7. Câu ghép & Từ nối",
]

KNOWLEDGE_HUB_CONTENT: Dict[str, str] = {
    '0. Nhập môn: Chữ cái, Cách đọc & Giống': """
<div class="clean-card">
    <div class="clean-label"><span>Phần A · Bảng 33 chữ cái tiếng Nga chia 3 nhóm dễ nhớ</span><span>А — Я (33 chữ)</span></div>
    <table class="clean-table">
        <thead><tr><th>Nhóm</th><th>Chữ cái</th><th>Cách đọc tiếng Việt gần đúng</th><th>Ví dụ có trọng âm</th></tr></thead>
        <tbody>
            <tr><td rowspan="6"><b>Nhóm 1</b><br/>Nhìn &amp; đọc gần giống</td><td><b>А а</b></td><td>a</td><td><b>а́дрес</b> (địa chỉ)</td></tr>
            <tr><td><b>Е е</b></td><td>yê / ê</td><td><b>е́сли</b> (nếu)</td></tr>
            <tr><td><b>К к</b></td><td>k</td><td><b>кни́га</b> (quyển sách)</td></tr>
            <tr><td><b>М м</b></td><td>m</td><td><b>ма́ма</b> (mẹ)</td></tr>
            <tr><td><b>О о</b></td><td>ô (có trọng âm) / a (không trọng âm)</td><td><b>окно́</b> (cửa sổ)</td></tr>
            <tr><td><b>Т т</b></td><td>t (không bật hơi)</td><td><b>тетра́дь</b> (quyển vở)</td></tr>
            <tr><td rowspan="6"><b>Nhóm 2</b><br/>Bẫy thị giác (giống Latin nhưng đọc khác)</td><td><b>В в</b></td><td>v (như v tiếng Việt)</td><td><b>вода́</b> (nước uống)</td></tr>
            <tr><td><b>Н н</b></td><td>n (như n tiếng Việt)</td><td><b>но́вый</b> (mới)</td></tr>
            <tr><td><b>Р р</b></td><td>r (rung đầu lưỡi)</td><td><b>ру́чка</b> (bút bi)</td></tr>
            <tr><td><b>С с</b></td><td>x / s nhẹ</td><td><b>сло́во</b> (từ vựng)</td></tr>
            <tr><td><b>У у</b></td><td>u</td><td><b>уро́к</b> (tiết học)</td></tr>
            <tr><td><b>Х х</b></td><td>kh (như kh tiếng Việt)</td><td><b>хлеб</b> (bánh mì)</td></tr>
            <tr><td rowspan="21"><b>Nhóm 3</b><br/>Chữ Cyrillic đặc trưng &amp; 2 dấu</td><td><b>Б б</b></td><td>b</td><td><b>биле́т</b> (vé / thẻ)</td></tr>
            <tr><td><b>Г г</b></td><td>g</td><td><b>го́род</b> (thành phố)</td></tr>
            <tr><td><b>Д д</b></td><td>đ</td><td><b>дом</b> (nhà)</td></tr>
            <tr><td><b>Ё ё</b></td><td>yô (luôn mang trọng âm)</td><td><b>ёлка</b> (cây thông)</td></tr>
            <tr><td><b>Ж ж</b></td><td>gi / zh (uốn lưỡi)</td><td><b>жизнь</b> (cuộc sống)</td></tr>
            <tr><td><b>З з</b></td><td>z (rung cổ họng)</td><td><b>за́втра</b> (ngày mai)</td></tr>
            <tr><td><b>И и</b></td><td>i</td><td><b>и́мя</b> (tên)</td></tr>
            <tr><td><b>Й й</b></td><td>i ngắn (ghép vần -ai / -oi)</td><td><b>музе́й</b> (bảo tàng)</td></tr>
            <tr><td><b>Л л</b></td><td>l</td><td><b>ла́мпа</b> (cái đèn)</td></tr>
            <tr><td><b>П п</b></td><td>p (mím môi)</td><td><b>па́спорт</b> (hộ chiếu)</td></tr>
            <tr><td><b>Ф ф</b></td><td>ph / f</td><td><b>факульте́т</b> (khoa)</td></tr>
            <tr><td><b>Ц ц</b></td><td>tx (bật nhanh đầu lưỡi)</td><td><b>цена́</b> (giá cả)</td></tr>
            <tr><td><b>Ч ч</b></td><td>ch (mềm, nhẹ)</td><td><b>час</b> (giờ)</td></tr>
            <tr><td><b>Ш ш</b></td><td>s (uốn lưỡi cứng)</td><td><b>шко́ла</b> (trường học)</td></tr>
            <tr><td><b>Щ щ</b></td><td>x-ch (mềm dài)</td><td><b>общежи́тие</b> (ký túc xá)</td></tr>
            <tr><td><b>Ъ ъ</b></td><td>Dấu cứng (tách âm, không phát âm)</td><td><b>объявле́ние</b> (thông báo)</td></tr>
            <tr><td><b>Ы ы</b></td><td>ư / ưi (kéo lưỡi lùi sau)</td><td><b>сын</b> (con trai)</td></tr>
            <tr><td><b>Ь ь</b></td><td>Dấu mềm (làm mềm phụ âm trước)</td><td><b>слова́рь</b> (từ điển)</td></tr>
            <tr><td><b>Э э</b></td><td>ê (mở miệng hơn е)</td><td><b>экза́мен</b> (kỳ thi)</td></tr>
            <tr><td><b>Ю ю</b></td><td>yu / iu</td><td><b>юг</b> (phương Nam)</td></tr>
            <tr><td><b>Я я</b></td><td>ya / ia</td><td><b>я́блоко</b> (quả táo)</td></tr>
        </tbody>
    </table>
</div>

<div class="clean-card">
    <div class="clean-label"><span>Phần B · 4 Quy tắc đọc sống còn cho người Việt</span><span>Phát âm chuẩn A0–A1</span></div>
    <table class="clean-table">
        <thead><tr><th>Quy tắc</th><th>Bản chất</th><th>Ví dụ thực tế</th></tr></thead>
        <tbody>
            <tr><td><b>1. Trọng âm &amp; Giảm âm (Аканье)</b></td><td><b>О</b> không có trọng âm đọc thành <b>А</b>; <b>Е / Я</b> không trọng âm đọc nhẹ thành <b>И</b>.</td><td><b>молоко́</b> → ma-la-kô · <b>хорошо́</b> → kha-ra-shô · <b>тетра́дь</b> → chi-trát</td></tr>
            <tr><td><b>2. Vô thanh hóa phụ âm cuối</b></td><td>Phụ âm hữu thanh đứng cuối từ bị đọc thành âm vô thanh: <b>б→п, в→ф, г→к, д→т, ж→ш, з→с</b>.</td><td><b>друг</b> → đrúc · <b>год</b> → gôt · <b>хлеб</b> → khơ-lếp · <b>глаз</b> → gơ-láx</td></tr>
            <tr><td><b>3. Cặp hay nhầm: Ш vs Щ · И vs Ы · Р</b></td><td><b>Ш</b> uốn lưỡi cứng, <b>Щ</b> mềm và kéo dài; <b>И</b> cười dẹt, <b>Ы</b> kéo lưỡi lùi về sau; <b>Р</b> rung đầu lưỡi.</td><td><b>шко́ла</b> (cứng) vs <b>общежи́тие</b> (mềm) · <b>мир</b> vs <b>мы</b></td></tr>
            <tr><td><b>4. Dấu mềm (Ь) &amp; Dấu cứng (Ъ)</b></td><td><b>Ь</b> không tự phát âm nhưng làm mềm phụ âm đứng trước; <b>Ъ</b> tách phụ âm với nguyên âm sau (о/е/я/ю).</td><td><b>мать</b> (t' mềm) · <b>объявле́ние</b> (đọc tách ob-yav-lê-ni-yê)</td></tr>
        </tbody>
    </table>
</div>

<div class="clean-card">
    <div class="clean-label"><span>Phần C · Mẹo nhận diện Giống của Danh từ trong 10 giây</span><span>Род существительных</span></div>
    <table class="clean-table">
        <thead><tr><th>Giống</th><th>Đuôi từ thường gặp</th><th>Ví dụ chuẩn</th><th>Ngoại lệ hay gặp ở Podfak</th></tr></thead>
        <tbody>
            <tr><td><b>Giống đực (Мужской род · он)</b></td><td>Phụ âm cứng, <b>-й</b></td><td>стол, музе́й, па́спорт, слова́рь</td><td><b>па́па</b> (bố), <b>де́душка</b> (ông), <b>мужчи́на</b> (đàn ông), <b>ко́фе</b> (cà phê)</td></tr>
            <tr><td><b>Giống cái (Женский род · она́)</b></td><td><b>-а, -я, -ия</b></td><td>кни́га, ко́мната, аудито́рия, семья́</td><td>Phần lớn danh từ đuôi <b>-ь</b> chỉ khái niệm trừu tượng/tập hợp: <b>тетра́дь, но́чь, пло́щадь</b></td></tr>
            <tr><td><b>Giống trung (Средний род · оно́)</b></td><td><b>-о, -е, -ие</b></td><td>окно́, мо́ре, общежи́тие, зда́ние</td><td>10 danh từ đuôi <b>-мя</b>: <b>вре́мя</b> (thời gian), <b>и́мя</b> (tên)</td></tr>
        </tbody>
    </table>
    <div class="note-callout">
        <b>Mẹo nhớ nhanh đuôi -ь:</b> Danh từ chỉ tháng (янва́рь, февра́ль...) và nghề nghiệp/người (преподава́тель, слова́рь) thường là <b>Giống đực</b>; danh từ chỉ vật dụng/khái niệm như <b>тетра́дь, дверь, крова́ть, ночь</b> là <b>Giống cái</b>.
    </div>
</div>
""",
    '1. 6 Cách · Danh từ': """
            <div class="clean-card">
                <div class="clean-label"><span>Tổng quan 6 cách trong tiếng Nga (Падежи)</span><span>Nền tảng cốt lõi</span></div>
                <table class="clean-table">
                    <thead><tr><th>Cách</th><th>Câu hỏi</th><th>Chức năng chính</th><th>Giới từ hay gặp</th><th>Ví dụ</th></tr></thead>
                    <tbody>
                        <tr><td><b>1. Именительный</b><br/>Nguyên cách</td><td>Кто? Что?</td><td>Chủ ngữ, định nghĩa, dạng gốc trong từ điển</td><td>Không có</td><td><b>Студе́нт</b> у́чится. <b>Кни́га</b> на столе́.</td></tr>
                        <tr><td><b>2. Родительный</b><br/>Sở hữu cách</td><td>Кого́? Чего́?</td><td>Sở hữu (của ai), phủ định (нет), số lượng (2–4 số ít; ≥5 số nhiều), xuất phát</td><td>у, без, до, из, с, от, о́коло, по́сле, для, кро́ме</td><td>Нет <b>вре́мени</b>. Два <b>студе́нта</b>. Из <b>Росси́и</b>.</td></tr>
                        <tr><td><b>3. Дательный</b><br/>Tặng cách</td><td>Кому́? Чему́?</td><td>Người nhận (cho ai), tuổi tác, trạng thái/cảm xúc (мне ну́жно), đối tượng hướng tới</td><td>к, по, благодаря́, вопреки́</td><td>Помога́ю <b>дру́гу</b>. <b>Мне</b> 21 год. По <b>пла́ну</b>.</td></tr>
                        <tr><td><b>4. Винительный</b><br/>Đối cách</td><td>Кого́? Что?</td><td>Tân ngữ trực tiếp (đọc gì, gặp ai), hướng chuyển động (куда́?), thứ trong tuần</td><td>в, на (hướng đi), че́рез, за, про</td><td>Чита́ю <b>кни́гу</b>. Иду́ в <b>университе́т</b>. В <b>сре́ду</b>.</td></tr>
                        <tr><td><b>5. Творительный</b><br/>Công cụ cách</td><td>Кем? Чем?</td><td>Công cụ (bằng gì), đi cùng ai (с кем?), nghề nghiệp (стать/рабо́тать), bị động</td><td>с, над, под, пе́ред, за, ме́жду</td><td>Пишу́ <b>ру́чкой</b>. Ко́фе с <b>молоко́м</b>. Ста́ну <b>инжене́ром</b>.</td></tr>
                        <tr><td><b>6. Предложный</b><br/>Giới cách</td><td>О ком? О чём? Где?</td><td>Vị trí tĩnh (ở đâu?), chủ đề (nói/nghĩ về gì), tháng/năm, phương tiện (на метро́)</td><td>в, на (vị trí), о (об), при</td><td>Живу́ в <b>Петербу́рге</b>. Ду́маю об <b>экза́мене</b>.</td></tr>
                    </tbody>
                </table>
            </div>

            <div class="clean-card">
                <div class="clean-label"><span>Bảng đuôi Danh từ Số ít &amp; Số nhiều</span></div>
                <table class="clean-table">
                    <thead><tr><th>Cách</th><th>Đực (ø/-й/-ь)</th><th>Cái (-а/-я/-ь)</th><th>Trung (-о/-е/-ие)</th><th>Số nhiều (Мн. ч.)</th></tr></thead>
                    <tbody>
                        <tr><td><b>1</b></td><td>ø / -й / -ь</td><td>-а / -я / -ь</td><td>-о / -е / -ие</td><td>-ы / -и · -а / -я</td></tr>
                        <tr><td><b>2</b></td><td>-а / -я / -я</td><td>-ы(-и) / -и / -и</td><td>-а / -я / -ия</td><td><b>-ов/-ев · -ей · ø · -ий</b></td></tr>
                        <tr><td><b>3</b></td><td>-у / -ю / -ю</td><td>-е (-и) / -и</td><td>-у / -ю / -ию</td><td>-ам / -ям</td></tr>
                        <tr><td><b>4</b></td><td>Vật=C1 · Người=C2</td><td>-у / -ю / -ь</td><td>Giống C1</td><td>Vật=C1 · Người=C2</td></tr>
                        <tr><td><b>5</b></td><td>-ом / -ем / -ем</td><td>-ой / -ей / -ью</td><td>-ом / -ем / -ием</td><td>-ами / -ями</td></tr>
                        <tr><td><b>6</b></td><td>-е (-ии)</td><td>-е (-ии/-и)</td><td>-е (-ии)</td><td>-ах / -ях</td></tr>
                    </tbody>
                </table>
                <div class="note-callout">
                    <b>Quy tắc 7 chữ cái (г, к, х, ж, ч, ш, щ):</b> Không bao giờ viết «ы», luôn đổi thành «и» (кни́га → кни́ги).<br/>
                    <b>Quy tắc 5 chữ cái (ж, ч, ш, щ, ц):</b> Không có trọng âm thì viết «е» thay cho «о» (това́рищем, хоро́шего).
                </div>
            </div>
            
""",
    '2. Tính từ & Đại từ': """
            <div class="clean-card">
                <div class="clean-label"><span>Biến cách Tính từ theo 6 cách</span></div>
                <table class="clean-table">
                    <thead><tr><th>Cách</th><th>Giống đực</th><th>Giống trung</th><th>Giống cái</th><th>Số nhiều</th></tr></thead>
                    <tbody>
                        <tr><td><b>1</b></td><td>-ый / -ой / -ий</td><td>-ое / -ее</td><td>-ая / -яя</td><td>-ые / -ие</td></tr>
                        <tr><td><b>2</b></td><td>-ого / -его</td><td>-ого / -его</td><td>-ой / -ей</td><td>-ых / -их</td></tr>
                        <tr><td><b>3</b></td><td>-ому / -ему</td><td>-ому / -ему</td><td>-ой / -ей</td><td>-ым / -им</td></tr>
                        <tr><td><b>4</b></td><td>Vật=C1 · Người=C2</td><td>-ое / -ее</td><td>-ую / -юю</td><td>Vật=C1 · Người=C2</td></tr>
                        <tr><td><b>5</b></td><td>-ым / -им</td><td>-ым / -им</td><td>-ой / -ей</td><td>-ыми / -ими</td></tr>
                        <tr><td><b>6</b></td><td>-ом / -ем</td><td>-ом / -ем</td><td>-ой / -ей</td><td>-ых / -их</td></tr>
                    </tbody>
                </table>
            </div>

            <div class="clean-card">
                <div class="clean-label"><span>6 Cách của Đại từ nhân xưng</span></div>
                <table class="clean-table">
                    <thead><tr><th>Cách</th><th>я</th><th>ты</th><th>он / оно́</th><th>она́</th><th>мы</th><th>вы</th><th>они́</th></tr></thead>
                    <tbody>
                        <tr><td><b>1</b></td><td>я</td><td>ты</td><td>он / оно́</td><td>она́</td><td>мы</td><td>вы</td><td>они́</td></tr>
                        <tr><td><b>2</b></td><td>меня́</td><td>тебя́</td><td>его́ (него́)</td><td>её (неё)</td><td>нас</td><td>вас</td><td>их (них)</td></tr>
                        <tr><td><b>3</b></td><td>мне</td><td>тебе́</td><td>ему́ (нему́)</td><td>ей (ней)</td><td>нам</td><td>вам</td><td>им (ним)</td></tr>
                        <tr><td><b>4</b></td><td>меня́</td><td>тебя́</td><td>его́ (него́)</td><td>её (неё)</td><td>нас</td><td>вас</td><td>их (них)</td></tr>
                        <tr><td><b>5</b></td><td>мной</td><td>тобо́й</td><td>им (ним)</td><td>ей (ней)</td><td>на́ми</td><td>ва́ми</td><td>и́ми (ни́ми)</td></tr>
                        <tr><td><b>6</b></td><td>обо мне</td><td>о тебе́</td><td>о нём</td><td>о ней</td><td>о нас</td><td>о вас</td><td>о них</td></tr>
                    </tbody>
                </table>
            </div>
            
""",
    '3. Động từ & Thể (НСВ/СВ)': """
            <div class="clean-card">
                <div class="clean-label"><span>Chia động từ Nhóm I &amp; Nhóm II · Biến âm · Thể НСВ / СВ</span></div>
                <table class="clean-table">
                    <thead><tr><th>Ngôi</th><th>Nhóm I (-ать, -ять, -еть · чита́ть)</th><th>Nhóm II (-ить · говори́ть)</th></tr></thead>
                    <tbody>
                        <tr><td><b>я</b></td><td>-у / -ю (чита́ю)</td><td>-у / -ю (говорю́)</td></tr>
                        <tr><td><b>ты</b></td><td>-ешь / -ёшь (чита́ешь)</td><td>-ишь (говори́шь)</td></tr>
                        <tr><td><b>он / она́ / оно́</b></td><td>-ет / -ёт (чита́ет)</td><td>-ит (говори́т)</td></tr>
                        <tr><td><b>мы</b></td><td>-ем / -ём (чита́ем)</td><td>-им (говори́м)</td></tr>
                        <tr><td><b>вы</b></td><td>-ете / -ёте (чита́ете)</td><td>-ите (говори́те)</td></tr>
                        <tr><td><b>они́</b></td><td>-ут / -ют (чита́ют)</td><td>-ат / -ят (говоря́т)</td></tr>
                    </tbody>
                </table>
                <div class="note-callout">
                    <b>Biến âm ở ngôi «я»:</b> д→ж (ви́жу), т→ч (плачу́), с→ш (пишу́), б/п/в/м→бл/пл/вл/мл (люблю́, гото́влю).<br/>
                    <b>НСВ</b> = quá trình, lặp lại (ка́ждый день, до́лго) · <b>СВ</b> = kết quả dứt điểm 1 lần (уже́, наконе́ц; không có thì hiện tại).
                </div>
            </div>
            
""",
    '4. Động từ chuyển động': """
            <div class="clean-card">
                <div class="clean-label"><span>Động từ chuyển động (1 chiều vs Đa chiều) &amp; Tiền tố</span></div>
                <table class="clean-table">
                    <thead><tr><th>Nghĩa</th><th>1 hướng / Đang đi</th><th>Khứ hồi / Thói quen</th><th>Tiền tố hay gặp</th></tr></thead>
                    <tbody>
                        <tr><td><b>Đi bộ</b></td><td>идти́ (иду́, идёшь)</td><td>ходи́ть (хожу́, хо́дишь)</td><td>при- (đến), у- (đi khỏi)</td></tr>
                        <tr><td><b>Đi xe / tàu</b></td><td>е́хать (е́ду, е́дешь)</td><td>е́здить (е́зжу, е́здишь)</td><td>в-/во- (vào), вы- (ra)</td></tr>
                        <tr><td><b>Mang (đi bộ)</b></td><td>нести́</td><td>носи́ть</td><td>под- (lại gần), от- (rời xa)</td></tr>
                        <tr><td><b>Chở (xe)</b></td><td>везти́</td><td>вози́ть</td><td>пере- (sang ngang), за- (ghé qua)</td></tr>
                        <tr><td><b>Bay</b></td><td>лете́ть</td><td>лета́ть</td><td>до- (tới đích), про- (đi qua)</td></tr>
                    </tbody>
                </table>
            </div>
            
""",
    '5. Giới từ & Thời gian': """
            <div class="clean-card">
                <div class="clean-label"><span>Giới từ địa điểm (В/НА · ИЗ/С · У/К/ОТ) &amp; Thời gian</span></div>
                <table class="clean-table">
                    <thead><tr><th>Где? (C6)</th><th>Куда́? (C4)</th><th>Отку́да? (C2)</th><th>Bắt buộc dùng «НА»</th></tr></thead>
                    <tbody>
                        <tr><td><b>в</b> + C6</td><td><b>в</b> + C4</td><td><b>из</b> + C2</td><td rowspan="3">на факульте́те, на ка́федре, на ку́рсе, на ле́кции, на экза́мене, на пра́ктике, на рабо́те, на по́чте, на вокза́ле, на заво́де</td></tr>
                        <tr><td><b>на</b> + C6</td><td><b>на</b> + C4</td><td><b>с</b> + C2</td></tr>
                        <tr><td><b>у</b> + C2</td><td><b>к</b> + C3</td><td><b>от</b> + C2</td></tr>
                    </tbody>
                </table>
                <div class="note-callout">
                    <b>Thời gian:</b> Thứ (<b>в</b> + C4: в сре́ду) · Tháng (<b>в</b> + C6: в ноябре́) · Ngày (Số thứ tự + Tháng đều <b>C2</b>: пе́рвого сентября́) · Bao lâu nữa (<b>че́рез</b> + C4) · Trước đây (C4 + <b>наза́д</b>).
                </div>
            </div>
            
""",
    '6. Số từ & Lượng từ': """
            <div class="clean-card">
                <div class="clean-label"><span>Quy tắc ghép Số đếm với Danh từ</span></div>
                <table class="clean-table">
                    <thead><tr><th>Số tận cùng</th><th>Cách của Danh từ</th><th>рубль</th><th>год</th><th>час</th></tr></thead>
                    <tbody>
                        <tr><td><b>1</b> (trừ 11)</td><td>Cách 1 số ít</td><td>оди́н рубль</td><td>оди́н год</td><td>оди́н час</td></tr>
                        <tr><td><b>2, 3, 4</b> (trừ 12–14)</td><td>Cách 2 số ít</td><td>два рубля́</td><td>три го́да</td><td>четы́ре часа́</td></tr>
                        <tr><td><b>5–20, 0, мно́го, ма́ло</b></td><td>Cách 2 số nhiều</td><td>пять рубле́й</td><td>пять <b>лет</b></td><td>пять часо́в</td></tr>
                    </tbody>
                </table>
            </div>
            
""",
    '7. Câu ghép & Từ nối': """
            <div class="clean-card">
                <div class="clean-label"><span>Cấu trúc câu ghép &amp; Từ nối học thuật</span></div>
                <table class="clean-table">
                    <thead><tr><th>Từ nối</th><th>Quy tắc</th><th>Ví dụ</th></tr></thead>
                    <tbody>
                        <tr><td><b>что́бы</b></td><td>Cùng chủ ngữ: nguyên thể · Khác chủ ngữ: <b>Quá khứ</b></td><td>Я хочу́, что́бы ты <b>пришёл</b>.</td></tr>
                        <tr><td><b>кото́рый</b></td><td>Giống &amp; số theo danh từ trước; Cách theo mệnh đề sau</td><td>Кни́га, <b>кото́рую</b> я чита́ю (C4).</td></tr>
                        <tr><td><b>благодаря́ / из-за</b></td><td>благодаря́ + C3 (nhờ vào) · из-за + C2 (tại vì)</td><td>Благодаря́ по́мощи · Из-за дождя́.</td></tr>
                        <tr><td><b>несмотря́ на</b></td><td>+ Cách 4 (mặc dù)</td><td>Несмотря́ на сло́жность зада́чи...</td></tr>
                    </tbody>
                </table>
            </div>
            
""",
}