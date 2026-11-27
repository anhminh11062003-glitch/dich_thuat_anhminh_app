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


DECK_MATH: List[Dict[str, str]] = [
    {"ru_accent": "Матема́тика", "pronunciation": "ma-chi-má-chi-ka", "vi": "Toán học", "en": "Mathematics", "example": "Вы́сшая матема́тика — ва́жный предме́т на пе́рвом ку́рсе."},
    {"ru_accent": "Уравне́ние", "pronunciation": "u-rav-nhê-ni-yê", "vi": "Phương trình", "en": "Equation", "example": "Ну́жно реши́ть квадра́тное уравне́ние."},
    {"ru_accent": "Фу́нкция", "pronunciation": "fúnk-txi-ya", "vi": "Hàm số", "en": "Function", "example": "Постро́йте гра́фик э́той фу́нкции."},
    {"ru_accent": "Произво́дная", "pronunciation": "pra-iz-vốt-na-ya", "vi": "Đạo hàm", "en": "Derivative", "example": "Найди́те пе́рвую произво́дную по вре́мени."},
    {"ru_accent": "Интегра́л", "pronunciation": "in-tê-grál", "vi": "Tích phân", "en": "Integral", "example": "Вы́числите определённый интегра́л от нуля́ до одного́."},
    {"ru_accent": "Преде́л", "pronunciation": "pri-đêl", "vi": "Giới hạn (lim)", "en": "Limit", "example": "Найдём преде́л фу́нкции при x стремя́щемся к нулю́."},
    {"ru_accent": "Дифференциа́льное уравне́ние", "pronunciation": "đi-fi-rên-txi-án-nơ-yê u-rav-nhê-ni-yê", "vi": "Phương trình vi phân", "en": "Differential equation", "example": "Движе́ние су́дна опи́сывается дифференциа́льным уравне́нием."},
    {"ru_accent": "Ма́трица", "pronunciation": "má-tri-txa", "vi": "Ma trận", "en": "Matrix", "example": "Найди́те определи́тель э́той ма́трицы."},
    {"ru_accent": "Ве́ктор", "pronunciation": "vêk-tơr", "vi": "Vectơ", "en": "Vector", "example": "Скаля́рное произведе́ние двух ве́кторов."},
    {"ru_accent": "Теоре́ма", "pronunciation": "tê-a-rê-ma", "vi": "Định lý", "en": "Theorem", "example": "Преподава́тель доказа́л теоре́му на доске́."},
    {"ru_accent": "Доказа́тельство", "pronunciation": "đa-ka-zá-chên-xtvơ", "vi": "Chứng minh (toán học)", "en": "Proof", "example": "Э́то доказа́тельство занима́ет три строки́."},
    {"ru_accent": "Координа́та", "pronunciation": "ka-ar-đi-ná-ta", "vi": "Tọa độ", "en": "Coordinate", "example": "Зада́йте координа́ты це́нтра тя́жести."},
    {"ru_accent": "Пло́щадь", "pronunciation": "plô-sơt", "vi": "Diện tích", "en": "Area", "example": "Пло́щадь ватерли́нии измеря́ется в квадра́тных ме́трах."},
    {"ru_accent": "Объём", "pronunciation": "ap-yôm", "vi": "Thể tích", "en": "Volume", "example": "Объём подво́дной ча́сти ко́рпуса."},
    {"ru_accent": "У́гол", "pronunciation": "ú-gơn", "vi": "Góc", "en": "Angle", "example": "У́гол кре́на не до́лжен превыша́ть норму."},
    {"ru_accent": "Ко́рень", "pronunciation": "kô-rên", "vi": "Căn bậc / Nghiệm", "en": "Root", "example": "Извлеки́те квадра́тный ко́рень из числа́."},
    {"ru_accent": "Сте́пень", "pronunciation": "xtê-pên", "vi": "Lũy thừa / Bậc", "en": "Power / Degree", "example": "Возведи́те число́ в тре́тью сте́пень."},
    {"ru_accent": "Логари́фм", "pronunciation": "la-ga-rífm", "vi": "Lô-ga-rít", "en": "Logarithm", "example": "Использу́йте натура́льный логари́фм."},
    {"ru_accent": "Дробь", "pronunciation": "đrôp", "vi": "Phân số", "en": "Fraction", "example": "Сократи́те числи́тель и знамена́тель дро́би."},
    {"ru_accent": "Вероя́тность", "pronunciation": "vi-ra-yát-nơxt", "vi": "Xác suất", "en": "Probability", "example": "Тео́рия вероя́тностей и математи́ческая стати́стика."},
    {"ru_accent": "Погре́шность", "pronunciation": "pa-grêt-nơxt", "vi": "Sai số", "en": "Error / Margin of error", "example": "Относи́тельная погре́шность расчёта ме́нее двух проце́нтов."},
    {"ru_accent": "Формула́ / Фо́рмула", "pronunciation": "fôr-mu-la", "vi": "Công thức", "en": "Formula", "example": "Подста́вьте значе́ния в фо́рмулу."},
    {"ru_accent": "Переме́нная", "pronunciation": "pi-ri-mên-na-ya", "vi": "Biến số", "en": "Variable", "example": "Заме́на переме́нной упроща́ет интегра́л."},
    {"ru_accent": "Конста́нта", "pronunciation": "kan-xtán-ta", "vi": "Hằng số", "en": "Constant", "example": "Ускоре́ние свобо́дного паде́ния — конста́нта."},
    {"ru_accent": "Гра́фик", "pronunciation": "grá-fik", "vi": "Đồ thị", "en": "Graph / Plot", "example": "По гра́фику ви́дно, как растёт сопротивле́ние."},
    {"ru_accent": "Крива́я", "pronunciation": "kri-vá-ya", "vi": "Đường cong", "en": "Curve", "example": "Крива́я осто́йчивости су́дна."},
    {"ru_accent": "Сече́ние", "pronunciation": "xi-chê-ni-yê", "vi": "Mặt cắt / Tiết diện", "en": "Cross-section", "example": "Попере́чное сече́ние ба́лки."},
    {"ru_accent": "Коэффицие́нт", "pronunciation": "ka-ê-fi-txi-ênt", "vi": "Hệ số", "en": "Coefficient", "example": "Коэффицие́нт по́лноты водоизмеще́ния."},
]

DECK_PHYSICS_MECHANICS: List[Dict[str, str]] = [
    {"ru_accent": "Фи́зика", "pronunciation": "fí-zi-ka", "vi": "Vật lý học", "en": "Physics", "example": "На ла́бе по фи́зике мы измеря́ли ускоре́ние."},
    {"ru_accent": "Меха́ника", "pronunciation": "mi-khá-ni-ka", "vi": "Cơ học", "en": "Mechanics", "example": "Теорети́ческая меха́ника — осно́ва инженерного расчёта."},
    {"ru_accent": "Си́ла", "pronunciation": "xí-la", "vi": "Lực", "en": "Force", "example": "Си́ла Архиме́да подде́рживает су́дно на воде́."},
    {"ru_accent": "Ско́рость", "pronunciation": "xkô-rơxt", "vi": "Vận tốc / Tốc độ", "en": "Velocity / Speed", "example": "Ско́рость хо́да су́дна — пятна́дцать узло́в."},
    {"ru_accent": "Ускоре́ние", "pronunciation": "u-xka-rê-ni-yê", "vi": "Gia tốc", "en": "Acceleration", "example": "Ускоре́ние равно́ произво́дной ско́рости."},
    {"ru_accent": "Ма́сса", "pronunciation": "má-xa", "vi": "Khối lượng", "en": "Mass", "example": "Ма́сса гру́за указа́на в то́ннах."},
    {"ru_accent": "Вес", "pronunciation": "vêx", "vi": "Trọng lượng", "en": "Weight", "example": "Вес вы́тесненной воды́ ра́вен ве́су су́дна."},
    {"ru_accent": "Пло́тность", "pronunciation": "plôt-nơxt", "vi": "Khối lượng riêng / Mật độ", "en": "Density", "example": "Пло́тность морско́й воды́ вы́ше, чем пре́сной."},
    {"ru_accent": "Давле́ние", "pronunciation": "đa-vlê-ni-yê", "vi": "Áp suất", "en": "Pressure", "example": "Гидростати́ческое давле́ние растёт с глубино́й."},
    {"ru_accent": "Эне́ргия", "pronunciation": "ê-nêr-gi-ya", "vi": "Năng lượng", "en": "Energy", "example": "Зако́н сохране́ния эне́ргии."},
    {"ru_accent": "Мо́щность", "pronunciation": "môt-nơxt", "vi": "Công suất", "en": "Power", "example": "Мо́щность гла́вного дви́гателя — десять мегава́тт."},
    {"ru_accent": "Моме́нт си́лы", "pronunciation": "ma-mênt xí-lư", "vi": "Mô-men lực", "en": "Torque / Moment of force", "example": "Восстана́вливающий моме́нт возвраща́ет су́дно в ро́вное положе́ние."},
    {"ru_accent": "Тре́ние", "pronunciation": "trê-ni-yê", "vi": "Ma sát", "en": "Friction", "example": "Сопротивле́ние тре́ния во́ды о ко́рпус."},
    {"ru_accent": "Напряже́ние", "pronunciation": "na-pri-zhê-ni-yê", "vi": "Ứng suất (cơ) / Điện áp (điện)", "en": "Stress / Voltage", "example": "Допусти́мое напряже́ние в листе́ обши́вки."},
    {"ru_accent": "Деформа́ция", "pronunciation": "đi-far-má-txi-ya", "vi": "Biến dạng", "en": "Deformation / Strain", "example": "Упру́гая и пласти́ческая деформа́ция мета́лла."},
    {"ru_accent": "Про́чность", "pronunciation": "prôt-nơxt", "vi": "Độ bền", "en": "Strength", "example": "Расчёт о́бщей про́чности ко́рпуса су́дна."},
    {"ru_accent": "Изги́б", "pronunciation": "iz-gíp", "vi": "Uốn (mô-men uốn)", "en": "Bending", "example": "На волне́ ко́рпус испытывает о́бщий изги́б."},
    {"ru_accent": "Круче́ние", "pronunciation": "kru-chê-ni-yê", "vi": "Xoắn", "en": "Torsion", "example": "Гребно́й вал рабо́тает на круче́ние."},
    {"ru_accent": "Колеба́ния / Вибра́ция", "pronunciation": "ka-li-bá-ni-ya / vi-brá-txi-ya", "vi": "Dao động / Rung động", "en": "Oscillation / Vibration", "example": "Ну́жно сни́зить вибра́цию ко́рпуса."},
    {"ru_accent": "Гидромеха́ника", "pronunciation": "gi-đrơ-mi-khá-ni-ka", "vi": "Cơ học chất lưu / Thủy cơ học", "en": "Fluid mechanics", "example": "Гидромеха́ника изуча́ет обтека́ние ко́рпуса водо́й."},
    {"ru_accent": "Вя́зкость", "pronunciation": "viáz-kơxt", "vi": "Độ nhớt", "en": "Viscosity", "example": "Кинемати́ческая вя́зкость воды́ зави́сит от температу́ры."},
    {"ru_accent": "Турбуле́нтность", "pronunciation": "tur-bu-lênt-nơxt", "vi": "Chảy rối (nhiễu loạn)", "en": "Turbulence", "example": "Турбуле́нтный пограни́чный слой у кормы́."},
    {"ru_accent": "Кавита́ция", "pronunciation": "ka-vi-tá-txi-ya", "vi": "Xâm thực (bọt khí chân vịt)", "en": "Cavitation", "example": "Кавита́ция разруша́ет ло́пасти гребно́го винта́."},
    {"ru_accent": "Термодина́мика", "pronunciation": "têr-ma-đi-ná-mi-ka", "vi": "Nhiệt động lực học", "en": "Thermodynamics", "example": "Пе́рвый зако́н термодина́мики."},
    {"ru_accent": "Теплообме́н", "pronunciation": "chi-pla-ap-mên", "vi": "Truyền nhiệt / Trao đổi nhiệt", "en": "Heat transfer", "example": "Расчёт теплообме́на в судово́м котле́."},
    {"ru_accent": "Электри́ческий ток", "pronunciation": "ê-lêk-trí-chix-ki tôk", "vi": "Dòng điện", "en": "Electric current", "example": "Си́ла электри́ческого то́ка измеря́ется в ампе́рах."},
    {"ru_accent": "Магни́тное по́ле", "pronunciation": "mag-nhít-nơ-yê pô-lê", "vi": "Từ trường", "en": "Magnetic field", "example": "Магни́тное по́ле Земли́ влия́ет на ко́мпас."},
    {"ru_accent": "Аку́стика", "pronunciation": "a-kúx-chi-ka", "vi": "Âm học", "en": "Acoustics", "example": "Подво́дная аку́стика важна́ для обнаруже́ния це́лей."},
]

DECK_CHEMISTRY_MATERIALS: List[Dict[str, str]] = [
    {"ru_accent": "Хи́мия", "pronunciation": "khí-mi-ya", "vi": "Hóa học", "en": "Chemistry", "example": "О́бщая хи́мия изуча́ется на пе́рвом ку́рсе."},
    {"ru_accent": "Материалове́дение", "pronunciation": "ma-chi-ri-a-la-vê-đi-ni-yê", "vi": "Khoa học vật liệu", "en": "Materials science", "example": "Материалове́дение помога́ет вы́брать сталь для су́дна."},
    {"ru_accent": "А́том", "pronunciation": "á-tơm", "vi": "Nguyên tử", "en": "Atom", "example": "Строе́ние а́тома желе́за."},
    {"ru_accent": "Моле́кула", "pronunciation": "ma-lê-ku-la", "vi": "Phân tử", "en": "Molecule", "example": "Моле́кула воды́ состои́т из водоро́да и кислоро́да."},
    {"ru_accent": "Химреа́кция / Реа́кция", "pronunciation": "ri-ák-txi-ya", "vi": "Phản ứng hóa học", "en": "Chemical reaction", "example": "Окисли́тельно-восстанови́тельная реа́кция."},
    {"ru_accent": "Кислота́", "pronunciation": "kix-la-tá", "vi": "Axit", "en": "Acid", "example": "Серная кислота́ — си́льный реаге́нт."},
    {"ru_accent": "Щёлочь / Основа́ние", "pronunciation": "siô-lơt / ax-na-vá-ni-yê", "vi": "Kiềm / Bazơ", "en": "Alkali / Base", "example": "Нейтрализа́ция кислоты́ щёлочью."},
    {"ru_accent": "Соль", "pronunciation": "xôn", "vi": "Muối", "en": "Salt", "example": "Солёность морско́й воды́ ускоря́ет корро́зию."},
    {"ru_accent": "Раство́р", "pronunciation": "rax-tvôr", "vi": "Dung dịch", "en": "Solution", "example": "Концентра́ция раство́ра."},
    {"ru_accent": "Окисле́ние", "pronunciation": "a-kix-lê-ni-yê", "vi": "Sự ô-xy hóa", "en": "Oxidation", "example": "Окисле́ние мета́лла на во́здухе."},
    {"ru_accent": "Корро́зия", "pronunciation": "ka-rô-zi-ya", "vi": "Sự ăn mòn kim loại", "en": "Corrosion", "example": "Защи́та ко́рпуса от морско́й корро́зии."},
    {"ru_accent": "Ржа́вчина", "pronunciation": "rơ-zháp-chi-na", "vi": "Gỉ sắt", "en": "Rust", "example": "Пе́ред покра́ской ну́жно очи́стить ржа́вчину."},
    {"ru_accent": "Сталь", "pronunciation": "xtan", "vi": "Thép", "en": "Steel", "example": "Судострои́тельная сталь повы́шенной про́чности."},
    {"ru_accent": "Сплав", "pronunciation": "xpláf", "vi": "Hợp kim", "en": "Alloy", "example": "Алюми́ниевый сплав для надстро́йки су́дна."},
    {"ru_accent": "Тита́н", "pronunciation": "chi-tán", "vi": "Ti-tan (hợp kim chống ăn mòn)", "en": "Titanium", "example": "Тита́н не ржаве́ет в морско́й воде́."},
    {"ru_accent": "Компози́т", "pronunciation": "kam-pa-zít", "vi": "Vật liệu composite", "en": "Composite material", "example": "Ко́рпус ка́тера сде́лан из компози́та."},
    {"ru_accent": "Сва́рка", "pronunciation": "xvár-ka", "vi": "Hàn kim loại", "en": "Welding", "example": "Электродугова́я сва́рка секций ко́рпуса."},
    {"ru_accent": "Сварно́й шов", "pronunciation": "xvar-nôi sốp", "vi": "Mối hàn", "en": "Weld seam", "example": "Ультразвуково́й контро́ль сварно́го шва."},
    {"ru_accent": "Термообрабо́тка", "pronunciation": "têr-ma-a-bra-bôt-ka", "vi": "Nhiệt luyện", "en": "Heat treatment", "example": "Термообрабо́тка повыша́ет твёрдость дета́ли."},
    {"ru_accent": "Твёрдость", "pronunciation": "tviôr-dơxt", "vi": "Độ cứng", "en": "Hardness", "example": "Измере́ние твёрдости ста́ли по Брине́ллю."},
    {"ru_accent": "Пласти́чность", "pronunciation": "plax-chít-nơxt", "vi": "Tính dẻo", "en": "Plasticity / Ductility", "example": "Хоро́шая пласти́чность предотвраща́ет тре́щины."},
    {"ru_accent": "Хру́пкость", "pronunciation": "khrúp-kơxt", "vi": "Tính giòn", "en": "Brittleness", "example": "При ни́зкой температу́ре растёт хру́пкость ста́ли."},
    {"ru_accent": "Уста́лость мета́лла", "pronunciation": "u-xtá-lơxt mi-tá-la", "vi": "Mỏi kim loại", "en": "Metal fatigue", "example": "Цикли́ческие нагру́зки вызыва́ют уста́лость мета́лла."},
    {"ru_accent": "Покры́тие / Кра́ска", "pronunciation": "pa-krư-chi-yê / kráz-ka", "vi": "Lớp phủ bảo vệ / Sơn tàu", "en": "Coating / Marine paint", "example": "Антикоррози́йное покры́тие подво́дной ча́сти."},
    {"ru_accent": "То́пливо", "pronunciation": "tô-pli-vơ", "vi": "Nhiên liệu", "en": "Fuel", "example": "Судово́е ди́зельное то́пливо."},
    {"ru_accent": "Сма́зка / Ма́сло", "pronunciation": "xmáz-ka / máx-lơ", "vi": "Dầu bôi trơn", "en": "Lubricant / Oil", "example": "Систе́ма сма́зки гла́вного дви́гателя."},
]

DECK_SMTU_ACADEMICS: List[Dict[str, str]] = [
    {"ru_accent": "Морско́й техни́ческий университе́т", "pronunciation": "mar-xkôi chi-khnhí-chix-ki u-ni-vêr-xi-chết", "vi": "Đại học Kỹ thuật Hàng hải (СПбГМТУ)", "en": "State Marine Technical University", "example": "Я учу́сь в Санкт-Петербу́ргском морско́м техни́ческом университе́те."},
    {"ru_accent": "Корабе́лка", "pronunciation": "ka-ra-bên-ka", "vi": "Tên thân mật của trường СПбГМТУ", "en": "Korabelka (SMTU nickname)", "example": "Корабе́лка — веду́щий вуз по судострое́нию в Росси́и."},
    {"ru_accent": "Факульте́т кораблестрое́ния и океаноте́хники", "pronunciation": "fa-kun-chết ka-ra-blê-xtra-yê-ni-ya i a-ki-a-na-têkh-ni-ki", "vi": "Khoa Đóng tàu & Kỹ thuật Đại dương (ФКиО)", "en": "Faculty of Shipbuilding & Ocean Engineering", "example": "ФКиО гото́вит инжене́ров-кораблестрои́телей."},
    {"ru_accent": "Факульте́т корабе́льной энерге́тики и автома́тики", "pronunciation": "fa-kun-chết ka-ra-bên-nơy ê-nêr-gê-chi-ki i áp-ta-má-chi-ki", "vi": "Khoa Năng lượng Tàu thủy & Tự động hóa (ФКЭиА)", "en": "Faculty of Marine Power & Automation", "example": "На ФКЭиА изуча́ют судовы́е дви́гатели и энергоустано́вки."},
    {"ru_accent": "Факульте́т морско́го приборострое́ния", "pronunciation": "fa-kun-chết mar-xkô-vơ pri-ba-ra-xtra-yê-ni-ya", "vi": "Khoa Thiết bị Hàng hải (ФМП)", "en": "Faculty of Marine Instrument Engineering", "example": "ФМП занима́ется подво́дной робототе́хникой и аку́стикой."},
    {"ru_accent": "Факульте́т цифровы́х промы́шленных техноло́гий", "pronunciation": "fa-kun-chết txư-fra-vưkh pra-mư-slên-nưkh chi-khna-lô-gi", "vi": "Khoa Công nghệ Công nghiệp Số (ФЦПТ)", "en": "Faculty of Digital Industrial Technologies", "example": "На ФЦПТ изуча́ют САПР и цифровы́е двойники́."},
    {"ru_accent": "Ка́федра", "pronunciation": "ká-fê-đra", "vi": "Bộ môn (trực thuộc khoa)", "en": "Academic department", "example": "Ка́федра тео́рии кора́бля и констру́кции ко́рпуса."},
    {"ru_accent": "Специа́льность", "pronunciation": "xpi-txi-án-nơxt", "vi": "Chuyên ngành đào tạo", "en": "Major / Specialty", "example": "Моя́ специа́льность — кораблестрое́ние."},
    {"ru_accent": "Бакалавриа́т / Магистрату́ра", "pronunciation": "ba-ka-la-vri-át / ma-gix-tra-tú-ra", "vi": "Hệ Cử nhân (4 năm) / Thạc sĩ (2 năm)", "en": "Bachelor's / Master's degree", "example": "По́сле бакалавриа́та я плани́рую в магистрату́ру."},
    {"ru_accent": "Специалите́т", "pronunciation": "xpi-txi-a-li-chết", "vi": "Hệ Kỹ sư chuyên sâu (5–5.5 năm)", "en": "Specialist degree", "example": "Обуче́ние на специалите́те дли́тся пять с полови́ной лет."},
    {"ru_accent": "Курсово́й прое́кт", "pronunciation": "kur-xa-vôi pra-yêkt", "vi": "Đồ án môn học", "en": "Course design project", "example": "Я сдаю́ курсово́й прое́кт по констру́кции ко́рпуса."},
    {"ru_accent": "Дипло́мная рабо́та / ВКР", "pronunciation": "đi-plôm-na-ya ra-bô-ta", "vi": "Khóa luận / Đồ án tốt nghiệp", "en": "Graduation thesis", "example": "Защи́та дипло́мной рабо́ты прохо́дит в ию́не."},
    {"ru_accent": "Нау́чный руководи́тель", "pronunciation": "na-út-nưy ru-ka-va-đí-chên", "vi": "Giảng viên hướng dẫn khoa học", "en": "Thesis advisor", "example": "Нау́чный руководи́тель прове́рил мои́ расчёты."},
    {"ru_accent": "Поясни́тельная запи́ска", "pronunciation": "pa-yax-nhí-chên-na-ya za-píx-ka", "vi": "Bản thuyết minh đồ án", "en": "Explanatory note / Report", "example": "Офо́рмите поясни́тельную запи́ску по ГО́СТу."},
    {"ru_accent": "Чертёж", "pronunciation": "chi-rơ-chiốt", "vi": "Bản vẽ kỹ thuật", "en": "Engineering drawing", "example": "Теорети́ческий чертёж ко́рпуса су́дна."},
    {"ru_accent": "Инжене́рная гра́фика", "pronunciation": "in-zhư-nhêr-na-ya grá-fi-ka", "vi": "Hình họa & Vẽ kỹ thuật", "en": "Engineering graphics", "example": "На пе́рвом ку́рсе мы че́ртим в AutoCAD и КО́МПАС-3D."},
    {"ru_accent": "Сопротивле́ние материа́лов", "pronunciation": "xa-pra-chi-vlê-ni-yê ma-chi-ri-á-lơf", "vi": "Môn Sức bền vật liệu", "en": "Strength of materials", "example": "Постро́йте эпю́ру изгиба́ющих моме́нтов по сопрома́ту."},
    {"ru_accent": "Тео́рия кора́бля", "pronunciation": "tê-ô-ri-ya ka-ra-bliá", "vi": "Môn Lý thuyết tàu", "en": "Ship theory / Naval architecture", "example": "Тео́рия кора́бля изуча́ет осто́йчивость и хо́дкость."},
    {"ru_accent": "Техноло́гия судострое́ния", "pronunciation": "chi-khna-lô-gi-ya xu-đa-xtra-yê-ni-ya", "vi": "Môn Công nghệ đóng tàu", "en": "Shipbuilding technology", "example": "Техноло́гия судострое́ния охва́тывает сбо́рку и сва́рку се́кций."},
    {"ru_accent": "Проекти́рование судо́в", "pronunciation": "pra-êk-chí-ra-va-ni-yê xu-đôf", "vi": "Môn Thiết kế tàu", "en": "Ship design", "example": "Вы́бор гла́вных разме́рений при проекти́ровании су́дна."},
    {"ru_accent": "Пра́ктика на верфи́", "pronunciation": "prák-chi-ka na vêr-fi", "vi": "Thực tập tại nhà máy đóng tàu", "en": "Shipyard internship", "example": "Ле́том студе́нты прохо́дят пра́ктику на Балти́йском заво́де."},
    {"ru_accent": "Судострои́тельный заво́д / Верфь", "pronunciation": "xu-đa-xtra-í-chên-nưy za-vôt / vêrf", "vi": "Nhà máy đóng tàu / Xưởng đóng tàu", "en": "Shipyard", "example": "На верфи́ стро́ят но́вый ато́мный ледоко́л."},
    {"ru_accent": "Реги́стр (РМРС)", "pronunciation": "ri-gíxtr", "vi": "Đăng kiểm Hàng hải Nga", "en": "Russian Maritime Register of Shipping", "example": "Констру́кция должна́ соотве́тствовать пра́вилам Реги́стра."},
    {"ru_accent": "ГОСТ / Станда́рт", "pronunciation": "gôxt / xtan-đárt", "vi": "Tiêu chuẩn quốc gia Nga (GOST)", "en": "GOST national standard", "example": "Все чертежи́ оформля́ются по ГО́СТу."},
    {"ru_accent": "Лаборато́рный стенд", "pronunciation": "la-ba-ra-tôr-nưy xtênt", "vi": "Bệ thử nghiệm phòng Lab", "en": "Laboratory test bench", "example": "Мы провели́ испыта́ния на лаборато́рном сте́нде."},
    {"ru_accent": "Защи́та прое́кта", "pronunciation": "za-sí-ta pra-yêk-ta", "vi": "Bảo vệ đồ án", "en": "Project defense", "example": "Защи́та прое́кта прошла́ на отли́чно!"},
]

DECK_SHIPBUILDING: List[Dict[str, str]] = [
    {"ru_accent": "Су́дно / Кора́бль", "pronunciation": "xút-nơ / ka-ráp", "vi": "Tàu dân sự / Tàu chiến (tàu lớn)", "en": "Vessel / Ship", "example": "Грузово́е су́дно вы́шло из по́рта."},
    {"ru_accent": "Ко́рпус су́дна", "pronunciation": "kôr-pux xút-na", "vi": "Thân tàu", "en": "Ship hull", "example": "Ко́рпус су́дна обеспечи́вает про́чность и гермети́чность."},
    {"ru_accent": "Нос / Корма́", "pronunciation": "nôx / kar-má", "vi": "Mũi tàu / Lái (đuôi) tàu", "en": "Bow / Stern", "example": "В носу́ су́дна расположе́н фо́рпик."},
    {"ru_accent": "Борт (пра́вый / ле́вый)", "pronunciation": "bôrt", "vi": "Mạn tàu (mạn phải / mạn trái)", "en": "Side (starboard / port)", "example": "Крен на пра́вый борт составля́ет два гра́дуса."},
    {"ru_accent": "Па́луба", "pronunciation": "pá-lu-ba", "vi": "Boong tàu", "en": "Deck", "example": "Ве́рхняя па́луба воспринима́ет о́бщий изги́б."},
    {"ru_accent": "Дни́ще / Двойно́е дно", "pronunciation": "đnhí-sê / đvai-nô-yê đnô", "vi": "Đáy tàu / Đáy đôi", "en": "Bottom / Double bottom", "example": "Двойно́е дно защища́ет су́дно при поса́дке на мель."},
    {"ru_accent": "Киль", "pronunciation": "kin", "vi": "Sống chính đáy tàu (Ki)", "en": "Keel", "example": "Закла́дка ки́ля — нача́ло постро́йки су́дна."},
    {"ru_accent": "Шпанго́ут", "pronunciation": "xpan-gô-ut", "vi": "Sườn tàu (khung ngang)", "en": "Frame / Rib", "example": "Шпа́ция — расстоя́ние ме́жду сосе́дними шпанго́утами."},
    {"ru_accent": "Стри́нгер / Би́мс", "pronunciation": "xtrín-gêr / bimx", "vi": "Sống dọc mạn / Xà ngang boong", "en": "Stringer / Deck beam", "example": "Би́мсы подде́рживают насти́л па́лубы."},
    {"ru_accent": "Перебо́рка", "pronunciation": "pi-ri-bôr-ka", "vi": "Vách ngăn kín nước", "en": "Bulkhead", "example": "Водонепроница́емые перебо́рки де́лят ко́рпус на отсе́ки."},
    {"ru_accent": "Обши́вка", "pronunciation": "ap-síp-ka", "vi": "Tôn bao thân tàu", "en": "Shell plating", "example": "Толщина́ нару́жной обши́вки в миллиме́трах."},
    {"ru_accent": "Надстро́йка", "pronunciation": "nat-xtrôi-ka", "vi": "Thượng tầng (cabin trên boong)", "en": "Superstructure", "example": "Жилы́е каю́ты нахо́дятся в надстро́йке."},
    {"ru_accent": "Трю́м", "pronunciation": "triúm", "vi": "Hầm hàng", "en": "Cargo hold", "example": "Грузово́й трюм закрыва́ется лю́ковыми кры́шками."},
    {"ru_accent": "Ватерли́ния", "pronunciation": "va-têr-lí-ni-ya", "vi": "Đường mớn nước (đường nước)", "en": "Waterline", "example": "Конструкти́вная ватерли́ния (КВЛ)."},
    {"ru_accent": "Оса́дка", "pronunciation": "a-xát-ka", "vi": "Mớn nước (chiều chìm của tàu)", "en": "Draft / Draught", "example": "Оса́дка су́дна в гру́зе — во́семь ме́тров."},
    {"ru_accent": "Водоизмеще́ние", "pronunciation": "va-đa-iz-mi-sê-ni-yê", "vi": "Lượng giãn nước", "en": "Displacement", "example": "По́лное водоизмеще́ние су́дна."},
    {"ru_accent": "Дедве́йт", "pronunciation": "đêt-vêyt", "vi": "Trọng tải toàn phần (DWT)", "en": "Deadweight", "example": "Дедве́йт та́нкера составля́ет сто ты́сяч тонн."},
    {"ru_accent": "Плаву́честь", "pronunciation": "pla-vú-chixt", "vi": "Tính nổi của tàu", "en": "Buoyancy", "example": "Запа́с плаву́чести определя́ется высото́й надво́дного бо́рта."},
    {"ru_accent": "Осто́йчивость", "pronunciation": "a-xtôi-chi-vơxt", "vi": "Tính ổn định của tàu", "en": "Stability", "example": "Нача́льная попере́чная осто́йчивость су́дна."},
    {"ru_accent": "Метацентри́ческая высота́", "pronunciation": "mi-ta-txên-trí-chix-ka-ya vư-xa-tá", "vi": "Chiều cao tâm nghiêng (GM)", "en": "Metacentric height", "example": "Положи́тельная метацентри́ческая высота́ гаранти́рует осто́йчивость."},
    {"ru_accent": "Непотопля́емость", "pronunciation": "nhi-pa-ta-pliá-yê-mơxt", "vi": "Tính không chìm", "en": "Unsinkability / Damage stability", "example": "Расчёт непотопля́емости при затопле́нии одного́ отсе́ка."},
    {"ru_accent": "Хо́дкость", "pronunciation": "khôt-kơxt", "vi": "Tính nhanh (tính hành thủy)", "en": "Propulsion performance", "example": "Хо́дкость изуча́ет сопротивле́ние воды́ и рабо́ту дви́жителя."},
    {"ru_accent": "Управля́емость", "pronunciation": "u-pra-vliá-yê-mơxt", "vi": "Tính ăn lái / Khả năng điều khiển", "en": "Maneuverability", "example": "Перо́ руля́ обеспечи́вает управля́емость су́дна."},
    {"ru_accent": "Ка́чка (бортова́я / килева́я)", "pronunciation": "kát-ka", "vi": "Sự lắc tàu (lắc ngang / lắc dọc)", "en": "Ship rolling / pitching", "example": "Успокои́тели ка́чки уменьша́ют бортову́ю ка́чку."},
    {"ru_accent": "Гребно́й винт", "pronunciation": "grêb-nôi vint", "vi": "Chân vịt tàu thủy", "en": "Propeller", "example": "Четырёхло́пастный гребно́й винт фикси́рованного ша́га."},
    {"ru_accent": "Руль / Рулево́е устро́йство", "pronunciation": "run / ru-lê-vô-yê u-xtrôi-xtvơ", "vi": "Bánh lái / Thiết bị lái", "en": "Rudder / Steering gear", "example": "Перекла́дка руля́ на три́дцать пять гра́дусов."},
    {"ru_accent": "Я́корное устро́йство", "pronunciation": "yá-kơr-nơ-yê u-xtrôi-xtvơ", "vi": "Thiết bị neo", "en": "Anchoring equipment", "example": "Я́корная цепь и брашпи́ль."},
    {"ru_accent": "О́пытовый бассе́йн", "pronunciation": "ô-pư-ta-vưy ba-xêyn", "vi": "Bể thử mô hình tàu thủy", "en": "Towing tank", "example": "Испыта́ние моде́ли су́дна в о́пытовом бассе́йне."},
]

DECK_MARINE_POWER_AUTO: List[Dict[str, str]] = [
    {"ru_accent": "Энергети́ческая устано́вка (СЭУ)", "pronunciation": "ê-nêr-gê-chí-chix-ka-ya u-xta-nốp-ka", "vi": "Hệ thống động lực tàu thủy", "en": "Ship power plant", "example": "Судова́я энергети́ческая устано́вка обеспечи́вает ход су́дна."},
    {"ru_accent": "Гла́вный дви́гатель", "pronunciation": "gláv-nưy đví-ga-chên", "vi": "Động cơ chính (máy chính)", "en": "Main engine", "example": "Малооборо́тный судово́й гла́вный дви́гатель."},
    {"ru_accent": "Ди́зельный дви́гатель", "pronunciation": "đí-zên-nưy đví-ga-chên", "vi": "Động cơ Diesel", "en": "Diesel engine", "example": "Четырёхта́ктный ди́зельный дви́гатель."},
    {"ru_accent": "Га́зовая турби́на", "pronunciation": "gá-za-va-ya tur-bí-na", "vi": "Tua-bin khí", "en": "Gas turbine", "example": "Га́зовая турби́на име́ет высо́кую уде́льную мо́щность."},
    {"ru_accent": "Парово́й котёл", "pronunciation": "pa-ra-vôi ka-chiôl", "vi": "Nồi hơi tàu thủy", "en": "Steam boiler", "example": "Утилизацио́нный парово́й котёл."},
    {"ru_accent": "Я́дерный реа́ктор", "pronunciation": "yá-đêr-nưy ri-ák-tơr", "vi": "Lò phản ứng hạt nhân (tàu phá băng)", "en": "Nuclear reactor", "example": "А́томный ледоко́л рабо́тает от я́дерного реа́ктора."},
    {"ru_accent": "Маши́нное отделе́ние", "pronunciation": "ma-sư-nơ-yê at-đi-lê-ni-yê", "vi": "Buồng máy", "en": "Engine room", "example": "Гла́вный дви́гатель устано́влен в маши́нном отделе́нии."},
    {"ru_accent": "Валопрово́д", "pronunciation": "va-la-pra-vôt", "vi": "Hệ trục chân vịt", "en": "Shafting / Propeller shaft", "example": "Валопрово́д передаёт крутя́щий моме́нт на винт."},
    {"ru_accent": "Реду́ктор", "pronunciation": "ri-đúk-tơr", "vi": "Hộp giảm tốc", "en": "Reduction gearbox", "example": "Реду́ктор снижа́ет частоту́ враще́ния ва́ла."},
    {"ru_accent": "Генера́тор", "pronunciation": "gi-ni-rá-tơr", "vi": "Máy phát điện", "en": "Generator", "example": "Дизель-генера́тор пита́ет судову́ю электросе́ть."},
    {"ru_accent": "Электродви́гатель", "pronunciation": "ê-lêk-tra-đví-ga-chên", "vi": "Động cơ điện", "en": "Electric motor", "example": "Гребно́й электродви́гатель на ледоко́ле."},
    {"ru_accent": "Насо́с", "pronunciation": "na-xôx", "vi": "Máy bơm", "en": "Pump", "example": "Центробе́жный балла́стный насо́с."},
    {"ru_accent": "Компре́ссор", "pronunciation": "kam-prê-xơr", "vi": "Máy nén khí", "en": "Compressor", "example": "Пусково́й во́здух подаётся от компре́ссора."},
    {"ru_accent": "Теплообме́нник", "pronunciation": "chi-pla-ap-mên-nhik", "vi": "Bộ trao đổi nhiệt", "en": "Heat exchanger", "example": "Пласти́нчатый теплообме́нник для охлажде́ния ма́сла."},
    {"ru_accent": "Кла́пан / Задви́жка", "pronunciation": "klá-pơn / za-đvízh-ka", "vi": "Van điều tiết / Van cổng", "en": "Valve / Gate valve", "example": "Предохрани́тельный кла́пан сбра́сывает ли́шнее давле́ние."},
    {"ru_accent": "Трубопрово́д", "pronunciation": "tru-ba-pra-vôt", "vi": "Hệ thống đường ống", "en": "Piping / Pipeline", "example": "Судово́й трубопрово́д пре́сной воды́."},
    {"ru_accent": "Автоматиза́ция", "pronunciation": "áp-ta-ma-chi-zá-txi-ya", "vi": "Tự động hóa", "en": "Automation", "example": "Автоматиза́ция маши́нного отделе́ния."},
    {"ru_accent": "Да́тчик", "pronunciation": "đát-chik", "vi": "Cảm biến", "en": "Sensor", "example": "Да́тчик температу́ры и давле́ния ма́сла."},
    {"ru_accent": "Контро́ллер (ПЛК)", "pronunciation": "kan-trô-lêr", "vi": "Bộ điều khiển lập trình (PLC)", "en": "Controller (PLC)", "example": "Программи́руемый логи́ческий контро́ллер."},
    {"ru_accent": "Систе́ма управле́ния", "pronunciation": "xi-xtê-ma u-pra-vlê-ni-ya", "vi": "Hệ thống điều khiển", "en": "Control system", "example": "Систе́ма автомати́ческого управле́ния ку́рсом."},
    {"ru_accent": "Обра́тная связь", "pronunciation": "a-brát-na-ya xviáz", "vi": "Hồi tiếp (điều khiển tự động)", "en": "Feedback", "example": "Контур регули́рования с отрица́тельной обра́тной свя́зью."},
    {"ru_accent": "Гидра́влика", "pronunciation": "gi-đrá-vli-ka", "vi": "Thủy lực", "en": "Hydraulics", "example": "Гидравли́ческий при́вод рулево́й маши́ны."},
    {"ru_accent": "КПД (Коэффицие́нт поле́зного де́йствия)", "pronunciation": "ka-pê-đê", "vi": "Hiệu suất", "en": "Efficiency", "example": "КПД совреме́нного ди́зеля достига́ет пяти́десяти проце́нтов."},
    {"ru_accent": "Выхлопны́е га́зы", "pronunciation": "vư-khla-pnư-yê gá-zư", "vi": "Khí xả động cơ", "en": "Exhaust gases", "example": "Очи́стка выхлопны́х га́зов по но́рмам IMO."},
    {"ru_accent": "Систе́ма охлажде́ния", "pronunciation": "xi-xtê-ma a-khla-zhđê-ni-ya", "vi": "Hệ thống làm mát", "en": "Cooling system", "example": "Двухко́нтурная систе́ма охлажде́ния дви́гателя."},
    {"ru_accent": "Авари́йный режи́м", "pronunciation": "a-va-ríy-nưy ri-zhưm", "vi": "Chế độ sự cố / Khẩn cấp", "en": "Emergency mode", "example": "При отка́зе включа́ется авари́йный генера́тор."},
]

DECK_OCEAN_TECH_NAV: List[Dict[str, str]] = [
    {"ru_accent": "Океаноте́хника", "pronunciation": "a-ki-a-na-têkh-ni-ka", "vi": "Kỹ thuật đại dương / Công trình biển", "en": "Ocean engineering", "example": "Океаноте́хника создаёт сооруже́ния для добы́чи на ше́льфе."},
    {"ru_accent": "Морска́я платфо́рма", "pronunciation": "mar-xká-ya plat-fôr-ma", "vi": "Giàn khoan / Công trình ngoài khơi", "en": "Offshore platform", "example": "Бурова́я морска́я платфо́рма в А́рктике."},
    {"ru_accent": "Ледоко́л", "pronunciation": "li-đa-kôl", "vi": "Tàu phá băng", "en": "Icebreaker", "example": "А́томный ледоко́л прокла́дывает путь во льда́х."},
    {"ru_accent": "Подво́дная ло́дка", "pronunciation": "pat-vôt-na-ya lôt-ka", "vi": "Tàu ngầm", "en": "Submarine", "example": "Про́чный ко́рпус подво́дной ло́дки выде́рживает большо́е давле́ние."},
    {"ru_accent": "Подво́дный аппара́т (НПА / АНПА)", "pronunciation": "pat-vôt-nưy a-pa-rát", "vi": "Thiết bị lặn không người lái (ROV/AUV)", "en": "Underwater vehicle (ROV/AUV)", "example": "Автоно́мный необита́емый подво́дный аппара́т обсле́дует дно."},
    {"ru_accent": "Гидроаку́стика", "pronunciation": "gi-đra-a-kúx-chi-ka", "vi": "Thủy âm học", "en": "Hydroacoustics", "example": "Гидроаку́стика — гла́вный спо́соб свя́зи под водо́й."},
    {"ru_accent": "Гидролока́тор / Сона́р", "pronunciation": "gi-đra-la-ká-tơr / xa-nár", "vi": "Máy định vị thủy âm (Sonar)", "en": "Sonar", "example": "Гидролока́тор стро́ит ка́рту релье́фа дна."},
    {"ru_accent": "Радиолока́тор (РЛС)", "pronunciation": "ra-đi-a-la-ká-tơr", "vi": "Ra-đa hàng hải", "en": "Marine radar", "example": "РЛС помога́ет су́дну идти́ в густо́м тума́не."},
    {"ru_accent": "Навига́ция", "pronunciation": "na-vi-gá-txi-ya", "vi": "Hàng hải / Dẫn đường", "en": "Navigation", "example": "Спу́тниковая навига́ция ГЛОНА́СС и GPS."},
    {"ru_accent": "Гироко́мпас", "pronunciation": "gi-ra-kôm-pơx", "vi": "La bàn con quay", "en": "Gyrocompass", "example": "Гироко́мпас ука́зывает и́стинный се́вер."},
    {"ru_accent": "Эхоло́т", "pronunciation": "ê-kha-lôt", "vi": "Máy đo sâu hồi âm", "en": "Echo sounder", "example": "Эхоло́т изме́рил глубину́ под ки́лем."},
    {"ru_accent": "Ходово́й мо́стик", "pronunciation": "kha-đa-vôi môx-chik", "vi": "Buồng lái / Cầu tàu", "en": "Navigation bridge", "example": "Капита́н упра́вляет су́дном с ходово́го мо́стика."},
    {"ru_accent": "Морска́я ми́ля / У́зел", "pronunciation": "mar-xká-ya mí-lia / ú-zên", "vi": "Hải lý (1852 m) / Hải lý giờ (knot)", "en": "Nautical mile / Knot", "example": "Оди́н у́зел ра́вен одно́й морско́й ми́ле в час."},
    {"ru_accent": "Волне́ние мо́ря", "pronunciation": "val-nhê-ni-yê mô-ria", "vi": "Sóng biển / Trạng thái biển", "en": "Sea state / Waves", "example": "Волне́ние мо́ря достига́ет пяти́ ба́ллов."},
    {"ru_accent": "Тече́ние", "pronunciation": "chi-chê-ni-yê", "vi": "Hải lưu / Dòng chảy", "en": "Ocean current", "example": "Си́льное подво́дное тече́ние."},
    {"ru_accent": "Шельф", "pronunciation": "sênf", "vi": "Thềm lục địa", "en": "Continental shelf", "example": "Освое́ние аркти́ческого ше́льфа."},
    {"ru_accent": "Конте́йнеровоз", "pronunciation": "kan-têy-nhi-ra-vôx", "vi": "Tàu chở container", "en": "Container ship", "example": "Современный конте́йнеровоз перево́зит ты́сячи конте́йнеров."},
    {"ru_accent": "Та́нкер / Газово́з", "pronunciation": "tán-kêr / ga-za-vôx", "vi": "Tàu chở dầu / Tàu chở khí hóa lỏng (LNG)", "en": "Tanker / LNG carrier", "example": "Аркти́ческий газово́з ледо́вого кла́сса."},
    {"ru_accent": "Сухогру́з / Ба́лкер", "pronunciation": "xu-kha-grúx / bál-kêr", "vi": "Tàu chở hàng khô / Tàu hàng rời", "en": "Dry cargo ship / Bulk carrier", "example": "Ба́лкер перево́зит зерно́ и уго́ль."},
    {"ru_accent": "Букси́р", "pronunciation": "buk-xír", "vi": "Tàu kéo / Tàu lai dắt", "en": "Tugboat", "example": "Букси́р помога́ет су́дну при шварто́вке в порту́."},
    {"ru_accent": "САПР (Систе́ма автоматизи́рованного проекти́рования)", "pronunciation": "xápr", "vi": "Hệ thống thiết kế CAD", "en": "CAD system", "example": "Инжене́ры рабо́тают в судострои́тельных САПР."},
    {"ru_accent": "Цифрово́й двойни́к", "pronunciation": "txư-fra-vôi đvai-nhík", "vi": "Bản sao số (Digital Twin)", "en": "Digital twin", "example": "Цифрово́й двойни́к помога́ет прогнози́ровать изно́с узло́в."},
    {"ru_accent": "Трёхме́рное модели́рование", "pronunciation": "triôkh-mêr-nơ-yê ma-đi-lí-ra-va-ni-yê", "vi": "Mô hình hóa 3D", "en": "3D modeling", "example": "Трёхме́рное модели́рование отсе́ка ко́рпуса."},
    {"ru_accent": "Мето́дика расчёта / МКЭ", "pronunciation": "mi-tô-đi-ka ra-siô-ta", "vi": "Phương pháp tính / Phần tử hữu hạn (FEM)", "en": "Calculation method / FEM", "example": "Расчёт про́чности ме́тодом коне́чных элеме́нтов (МКЭ)."},
    {"ru_accent": "Безопа́сность морепла́вания", "pronunciation": "bi-za-páx-nơxt ma-ri-plá-va-ni-ya", "vi": "An toàn hàng hải", "en": "Maritime safety", "example": "Междунаро́дная конве́нция СО́ЛАС по безопа́сности морепла́вания."},
    {"ru_accent": "Экипа́ж", "pronunciation": "ê-ki-pásh", "vi": "Thủy thủ đoàn", "en": "Ship crew", "example": "Чи́сленность экипа́жа — два́дцать челове́к."},
]

DECK_ASPECT_VERBS_NSV_SV: List[Dict[str, str]] = [
    # Nhóm 1: Động từ + Cách 4 (Кого? Что?)
    {"ru_accent": "ви́деть — уви́деть", "pronunciation": "ví-đêt — u-ví-đêt", "vi": "nhìn thấy (НСВ — СВ · + C4)", "en": "to see", "example": "Я уви́дел дру́га на ста́нции метро́."},
    {"ru_accent": "повторя́ть — повтори́ть", "pronunciation": "pơp-ta-riát — pơp-ta-rít", "vi": "nhắc lại / ôn lại (НСВ — СВ · + C4)", "en": "to repeat / review", "example": "Повтори́те, пожа́луйста, э́то пра́вило."},
    {"ru_accent": "изуча́ть — изучи́ть", "pronunciation": "i-zu-chát — i-zu-chít", "vi": "nghiên cứu / học chuyên sâu (НСВ — СВ · + C4)", "en": "to study thoroughly", "example": "Мы изуча́ем тео́рию кора́бля на тре́тьем ку́рсе."},
    {"ru_accent": "гото́вить — пригото́вить", "pronunciation": "ga-tô-vit — pri-ga-tô-vit", "vi": "chuẩn bị / nấu ăn (НСВ — СВ · + C4)", "en": "to prepare / cook", "example": "Я пригото́вил докла́д к семина́ру."},
    {"ru_accent": "люби́ть — полюби́ть", "pronunciation": "liu-bít — pa-liu-bít", "vi": "yêu thích / đem lòng yêu (НСВ — СВ · + C4)", "en": "to love / fall in love", "example": "Он сразу полюби́л Санкт-Петербу́рг."},
    {"ru_accent": "вспомина́ть — вспо́мнить", "pronunciation": "pơx-pa-mi-nát — pxpôm-nhit", "vi": "nhớ lại / hồi tưởng (НСВ — СВ · + C4)", "en": "to recall / remember", "example": "Я наконе́ц вспо́мнил э́ту фо́рмулу!"},
    {"ru_accent": "встреча́ть — встре́тить", "pronunciation": "pxtrê-chát — pxtrê-chit", "vi": "đón / gặp gỡ ai (НСВ — СВ · + C4)", "en": "to meet / pick up", "example": "Мы встре́тили но́вых студе́нтов в аэропорту́."},
    {"ru_accent": "поздравля́ть — поздра́вить", "pronunciation": "paz-đra-vliát — paz-đrá-vit", "vi": "chúc mừng (НСВ — СВ · + C4 + с C5)", "en": "to congratulate", "example": "Поздравля́ю вас с днём рожде́ния!"},
    {"ru_accent": "открыва́ть — откры́ть", "pronunciation": "at-krư-vát — at-krưt", "vi": "mở ra (НСВ — СВ · + C4)", "en": "to open", "example": "Откро́йте уче́бник на пя́той страни́це."},
    {"ru_accent": "закрыва́ть — закры́ть", "pronunciation": "za-krư-vát — za-krưt", "vi": "đóng lại / trả xong nợ môn (НСВ — СВ · + C4)", "en": "to close", "example": "Ну́жно закры́ть все хвосты́ до се́ссии."},
    {"ru_accent": "получа́ть — получи́ть", "pronunciation": "pa-lu-chát — pa-lu-chít", "vi": "nhận được (НСВ — СВ · + C4)", "en": "to receive / get", "example": "Я получи́л автома́т по фи́зике."},
    {"ru_accent": "приглаша́ть — пригласи́ть", "pronunciation": "pri-gla-sát — pri-gla-xít", "vi": "mời (НСВ — СВ · + C4)", "en": "to invite", "example": "Друг пригласи́л меня́ на ве́чер университе́та."},
    {"ru_accent": "исправля́ть — испра́вить", "pronunciation": "ix-pra-vliát — ix-prá-vit", "vi": "sửa lỗi (НСВ — СВ · + C4)", "en": "to correct / fix", "example": "Ну́жно испра́вить оши́бки в чертеже́."},
    {"ru_accent": "проси́ть — попроси́ть", "pronunciation": "pra-xít — pa-pra-xít", "vi": "nhờ vả / xin (НСВ — СВ · + C4)", "en": "to ask for / request", "example": "Я попроси́л преподава́теля объясни́ть ещё раз."},
    {"ru_accent": "реша́ть — реши́ть", "pronunciation": "ri-sát — ri-sít", "vi": "giải bài / quyết định (НСВ — СВ · + C4)", "en": "to solve / decide", "example": "Мы реши́ли все зада́чи по мата́ну."},
    {"ru_accent": "смотре́ть — посмотре́ть", "pronunciation": "xma-trết — pa-xma-trết", "vi": "xem / nhìn (НСВ — СВ · + C4)", "en": "to watch / look", "example": "Посмотри́ расписа́ние на са́йте СПбГМТУ."},
    {"ru_accent": "петь — спеть", "pronunciation": "pêt — xpêt", "vi": "hát (НСВ — СВ · + C4)", "en": "to sing", "example": "Дава́й споём ру́сскую пе́сню!"},
    {"ru_accent": "благодари́ть — поблагодари́ть", "pronunciation": "bla-ga-đa-rít — pa-bla-ga-đa-rít", "vi": "cảm ơn ai vì điều gì (НСВ — СВ · + C4 + за C4)", "en": "to thank", "example": "Мы поблагодари́ли учи́теля за по́мощь."},
    # Nhóm 2: Động từ + Cách 3 (Кому?) (+ Cách 4 / Cách 6 / Inf)
    {"ru_accent": "звони́ть — позвони́ть", "pronunciation": "zva-nhít — pa-zva-nhít", "vi": "gọi điện cho ai (НСВ — СВ · + C3)", "en": "to call", "example": "Позвони́ мне ве́чером по́сле па́ры."},
    {"ru_accent": "сообща́ть — сообщи́ть", "pronunciation": "xa-ap-sát — xa-ap-sít", "vi": "thông báo / báo cáo (НСВ — СВ · + C3 + о C6)", "en": "to inform / report", "example": "Ста́роста сообщи́ла гру́ппе о перено́се экза́мена."},
    {"ru_accent": "расска́зывать — рассказа́ть", "pronunciation": "rax-ká-zư-vơt — rax-ka-zát", "vi": "kể lại (НСВ — СВ · + C3 + о C6)", "en": "to tell / narrate", "example": "Она́ рассказа́ла мне о своём прое́кте."},
    {"ru_accent": "пока́зывать — показа́ть", "pronunciation": "pa-ká-zư-vơt — pa-ka-zát", "vi": "chỉ / cho xem (НСВ — СВ · + C3 + C4)", "en": "to show", "example": "Покажи́те, пожа́луйста, студе́нческий биле́т."},
    {"ru_accent": "дари́ть — подари́ть", "pronunciation": "đa-rít — pa-đa-rít", "vi": "tặng quà (НСВ — СВ · + C3 + C4)", "en": "to give a gift", "example": "Мы подари́ли дру́гу слова́рь."},
    {"ru_accent": "объясня́ть — объясни́ть", "pronunciation": "ab-yax-nhát — ab-yax-nhít", "vi": "giải thích (НСВ — СВ · + C3 + C4)", "en": "to explain", "example": "Преподава́тель поня́тно объясни́л те́му."},
    {"ru_accent": "передава́ть — переда́ть", "pronunciation": "pi-ri-đa-vát — pi-ri-đát", "vi": "chuyển / truyền lại (НСВ — СВ · + C3 + C4)", "en": "to pass / hand over", "example": "Переда́й, пожа́луйста, зачётку преподава́телю."},
    {"ru_accent": "посыла́ть — посла́ть", "pronunciation": "pa-xư-lát — pax-lát", "vi": "gửi đi (НСВ — СВ · + C3 + C4)", "en": "to send", "example": "Я посла́л нау́чному руководи́телю чертёж."},
    {"ru_accent": "присыла́ть — присла́ть", "pronunciation": "pri-xư-lát — pri-xlát", "vi": "gửi đến (НСВ — СВ · + C3 + C4)", "en": "to send over", "example": "Пришли́ мне, пожа́луйста, файл в Телегра́м."},
    {"ru_accent": "сове́товать — посове́товать", "pronunciation": "xa-vê-tơ-vơt — pa-xa-vê-tơ-vơt", "vi": "khuyên ai làm gì (НСВ — СВ · + C3 + инф.)", "en": "to advise", "example": "Сове́тую тебе́ нача́ть курса́ч зара́нее."},
    {"ru_accent": "разреша́ть — разреши́ть", "pronunciation": "raz-ri-sát — raz-ri-sít", "vi": "cho phép (НСВ — СВ · + C3 + инф.)", "en": "to allow / permit", "example": "Декана́т разреши́л пересда́ть экза́мен."},
    {"ru_accent": "обеща́ть — пообеща́ть", "pronunciation": "a-bi-sát — pa-a-bi-sát", "vi": "hứa (НСВ — СВ · + C3 + инф.)", "en": "to promise", "example": "Ко́ля пообеща́л мне прие́хать сего́дня."},
    {"ru_accent": "меша́ть — помеша́ть", "pronunciation": "mi-sát — pa-mi-sát", "vi": "làm phiền / cản trở (НСВ — СВ · + C3)", "en": "to disturb / hinder", "example": "Извини́те, я вам не меша́ю?"},
    {"ru_accent": "нра́виться — понра́виться", "pronunciation": "nrá-vi-txa — pan-rá-vi-txa", "vi": "thích (ai đó thấy thích · C3 + C1)", "en": "to like / appeal to", "example": "Мне о́чень понра́вилась э́та ле́кция."},
    # Nhóm 3: Động từ + Cách 5 (с кем? / кем? чем?)
    {"ru_accent": "догова́риваться — договори́ться", "pronunciation": "đa-ga-vá-ri-vơ-txa — đa-ga-va-rí-txa", "vi": "thỏa thuận / hẹn với ai (НСВ — СВ · + с C5)", "en": "to agree / arrange", "example": "Мы договори́лись встре́титься у метро́ в пять."},
    {"ru_accent": "встреча́ться — встре́титься", "pronunciation": "pxtrê-chá-txa — pxtrê-chi-txa", "vi": "gặp nhau với ai (НСВ — СВ · + с C5)", "en": "to meet up with", "example": "За́втра я встре́чусь с нау́чником."},
    {"ru_accent": "знако́миться — познако́миться", "pronunciation": "zna-kô-mi-txa — paz-na-kô-mi-txa", "vi": "làm quen với ai (НСВ — СВ · + с C5)", "en": "to get acquainted", "example": "Рад познако́миться с ва́ми!"},
    {"ru_accent": "сове́товаться — посове́товаться", "pronunciation": "xa-vê-tơ-vơ-txa — pa-xa-vê-tơ-vơ-txa", "vi": "hỏi ý kiến / bàn bạc với ai (НСВ — СВ · + с C5)", "en": "to consult with", "example": "На́до посове́товаться с преподава́телем."},
    {"ru_accent": "спо́рить — поспо́рить", "pronunciation": "xpô-rit — pax-pô-rit", "vi": "tranh luận với ai (НСВ — СВ · + с C5)", "en": "to argue / debate", "example": "Не сто́ит спо́рить с экзамена́тором."},
    {"ru_accent": "ссо́риться — поссо́риться", "pronunciation": "xô-ri-txa — pa-xô-ri-txa", "vi": "cãi nhau với ai (НСВ — СВ · + с C5)", "en": "to quarrel", "example": "Они́ поссо́рились, но бы́стро помири́лись."},
    {"ru_accent": "мири́ться — помири́ться", "pronunciation": "mi-rí-txa — pa-mi-rí-txa", "vi": "làm hòa với ai (НСВ — СВ · + с C5)", "en": "to make up / reconcile", "example": "Друзья́ помири́лись по́сле спо́ра."},
    {"ru_accent": "занима́ться — заня́ться", "pronunciation": "za-nhi-má-txa — za-nhá-txa", "vi": "học / nghiên cứu / tập luyện (НСВ — СВ · + C5)", "en": "to study / engage in", "example": "Он занима́ется судострое́нием и спо́ртом."},
    {"ru_accent": "станови́ться — стать", "pronunciation": "xta-na-ví-txa — xtat", "vi": "trở thành (НСВ — СВ · + C5)", "en": "to become", "example": "Я хочу́ стать инжене́ром-кораблестрои́телем."},
    {"ru_accent": "интересова́ться — заинтересова́ться", "pronunciation": "in-tê-ri-xa-vá-txa — za-in-tê-ri-xa-vá-txa", "vi": "quan tâm đến (НСВ — СВ · + C5)", "en": "to be interested in", "example": "Он интересу́ется подво́дной робототе́хникой."},
]


ALL_VOCAB_DECKS: Dict[str, List[Dict[str, str]]] = {
    **STARTER_VOCAB_DECKS,
    "5. Toán học đại cương (Математика)": DECK_MATH,
    "6. Vật lý & Cơ học kỹ thuật (Физика)": DECK_PHYSICS_MECHANICS,
    "7. Hóa học & Vật liệu (Химия и Материалы)": DECK_CHEMISTRY_MATERIALS,
    "8. Khoa, Bộ môn & Học thuật СПбГМТУ": DECK_SMTU_ACADEMICS,
    "9. Kết cấu & Lý thuyết tàu (Кораблестроение)": DECK_SHIPBUILDING,
    "10. Máy tàu, Năng lượng & Tự động hóa": DECK_MARINE_POWER_AUTO,
    "11. Kỹ thuật Đại dương, Robot ngầm & Hàng hải": DECK_OCEAN_TECH_NAV,
    "12. 42 Cặp động từ НСВ / СВ theo 6 cách": DECK_ASPECT_VERBS_NSV_SV,
}

VOCAB_DECK_CATEGORIES: Dict[str, List[str]] = {
    "Nhập môn A0–A1": [
        "1. Sinh tồn tuần đầu tại Nga",
        "2. Lớp học Dự bị (Подфак)",
        "3. Ký túc xá & Giấy tờ",
        "4. Động từ & Tính từ cốt lõi A1",
        "12. 42 Cặp động từ НСВ / СВ theo 6 cách",
    ],
    "Toán · Lý · Hóa": [
        "5. Toán học đại cương (Математика)",
        "6. Vật lý & Cơ học kỹ thuật (Физика)",
        "7. Hóa học & Vật liệu (Химия и Материалы)",
    ],
    "Chuyên ngành СПбГМТУ": [
        "8. Khoa, Bộ môn & Học thuật СПбГМТУ",
        "9. Kết cấu & Lý thuyết tàu (Кораблестроение)",
        "10. Máy tàu, Năng lượng & Tự động hóa",
        "11. Kỹ thuật Đại dương, Robot ngầm & Hàng hải",
    ],
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

            <div class="clean-card">
                <div class="clean-label"><span>Danh từ biến đổi số nhiều đặc biệt (Cách 1 &amp; Cách 2)</span><span>Hay thi nhất</span></div>
                <table class="clean-table">
                    <thead><tr><th>Cách 1 số ít</th><th>Cách 1 số nhiều</th><th>Cách 2 số nhiều</th><th>Nghĩa</th></tr></thead>
                    <tbody>
                        <tr><td>брат / сестра́</td><td>бра́тья / сёстры</td><td><b>бра́тьев / сестёр</b></td><td>anh em trai / chị em gái</td></tr>
                        <tr><td>друг / челове́к</td><td>друзья́ / лю́ди</td><td><b>друзе́й / люде́й</b></td><td>bạn bè / con người</td></tr>
                        <tr><td>ребёнок / сын</td><td>де́ти / сыновья́</td><td><b>дете́й / сынове́й</b></td><td>trẻ em / con trai</td></tr>
                        <tr><td>мать / дочь</td><td>ма́тери / до́чери</td><td><b>матере́й / дочере́й</b></td><td>mẹ / con gái</td></tr>
                        <tr><td>стул / лист / де́рево</td><td>сту́лья / ли́стья / дере́вья</td><td><b>сту́льев / ли́стьев / дере́вьев</b></td><td>ghế / lá / cây</td></tr>
                        <tr><td>письмо́ / окно́</td><td>пи́сьма / о́кна</td><td><b>пи́сем / о́кон</b></td><td>bức thư / cửa sổ</td></tr>
                    </tbody>
                </table>
                <div class="note-callout">
                    <b>Cấu trúc Có / Không có ở 3 thì:</b><br/>
                    • <b>Có:</b> У кого́ (C2) + <b>был(а/о/и) / есть / бу́дет</b> + C1 (<i>У меня́ есть слова́рь</i>).<br/>
                    • <b>Không có:</b> У кого́ (C2) + <b>не́ было / нет / не бу́дет</b> + <b>C2</b> (<i>У меня́ нет вре́мени; За́втра не бу́дет уро́ка</i>).<br/>
                    <b>Tính từ ngắn đuôi + Cách 5:</b> <i>дово́лен</i> (hài lòng), <i>бога́т</i> (giàu có), <i>изве́стен</i> (nổi tiếng), <i>бо́лен</i> (ốm) + <b>чем? (C5)</b> — VD: <i>Профе́ссор дово́лен рабо́той студе́нтов.</i>
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

            <div class="clean-card">
                <div class="clean-label"><span>Đại từ sở hữu (мой, твой, наш, ваш, свой) &amp; Chỉ định (э́тот)</span></div>
                <table class="clean-table">
                    <thead><tr><th>Cách</th><th>Đực / Trung (мой · э́тот)</th><th>Cái (моя́ · э́та)</th><th>Số nhiều (мои́ · э́ти)</th><th>Lưu ý</th></tr></thead>
                    <tbody>
                        <tr><td><b>1</b></td><td>мой / моё · э́тот / э́то</td><td>моя́ · э́та</td><td>мои́ · э́ти</td><td><b>его́, её, их</b> không đổi ở cả 6 cách</td></tr>
                        <tr><td><b>2</b></td><td>моего́ · э́того</td><td>мое́й · э́той</td><td>мои́х · э́тих</td><td><b>наш/ваш:</b> на́шего, на́шей, на́ших</td></tr>
                        <tr><td><b>3</b></td><td>моему́ · э́тому</td><td>мое́й · э́той</td><td>мои́м · э́тим</td><td><b>свой</b> chia hệt như <b>мой</b></td></tr>
                        <tr><td><b>4</b></td><td>Vật=C1 · Người=C2</td><td>мою́ · э́ту</td><td>Vật=C1 · Người=C2</td><td><i>Я чита́ю э́ту кни́гу / вижу э́того дру́га</i></td></tr>
                        <tr><td><b>5</b></td><td>мои́м · э́тим</td><td>мое́й · э́той</td><td>мои́ми · э́тими</td><td><i>с мои́м дру́гом · с э́той гру́ппой</i></td></tr>
                        <tr><td><b>6</b></td><td>моём · э́том</td><td>мое́й · э́той</td><td>мои́х · э́тих</td><td><i>в на́шем университе́те · об э́том</i></td></tr>
                    </tbody>
                </table>
                <div class="note-callout">
                    <b>Quy tắc thêm «н-» sau giới từ:</b> Khi ngôi thứ 3 (<i>он, она́, оно́, они́</i>) đứng ngay sau giới từ ở các cách 2–6, bắt buộc thêm <b>н-</b>: <i>у <b>него́</b>, к <b>ней</b>, с <b>ни́ми</b>, о <b>нём</b></i> (nhưng khi là sở hữu thì KHÔNG thêm: <i>у его́ дру́га</i>).
                </div>
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

            <div class="clean-card">
                <div class="clean-label"><span>So sánh 3 Thì của Thể Chưa hoàn thành (НСВ) &amp; Hoàn thành (СВ)</span><span>Cốt lõi động từ</span></div>
                <table class="clean-table">
                    <thead><tr><th>Thì</th><th>Thể НСВ (Quá trình · Lặp lại · Không nhấn kết quả)</th><th>Thể СВ (1 lần · Dứt điểm · Có kết quả)</th></tr></thead>
                    <tbody>
                        <tr><td><b>Quá khứ</b></td><td>чита́л(а/и) — <i>Вчера́ я до́лго чита́л текст.</i></td><td>прочита́л(а/и) — <i>Я уже́ прочита́л весь текст.</i></td></tr>
                        <tr><td><b>Hiện tại</b></td><td>чита́ю, чита́ешь... — <i>Я сейча́с чита́ю.</i></td><td><b>KHÔNG CÓ thì hiện tại!</b></td></tr>
                        <tr><td><b>Tương lai</b></td><td><b>бу́ду + nguyên thể НСВ</b> — <i>За́втра я бу́ду чита́ть рома́н.</i></td><td><b>Chia trực tiếp СВ</b> — <i>За́втра я прочита́ю рома́н.</i></td></tr>
                    </tbody>
                </table>
                <div class="note-callout">
                    <b>Cấu trúc rủ rê (Thức mệnh lệnh ngôi 1):</b> <b>Дава́й / Дава́йте + ngôi «мы» của động từ СВ</b>!<br/>
                    VD: <i>Дава́й пойдём в кино́!</i> (Chúng mình đi xem phim nhé!) · <i>Дава́йте споём пе́сню!</i> · <i>Дава́й пообе́даем вме́сте!</i><br/>
                    <b>Thời gian Cách 4 với НСВ vs СВ:</b> НСВ không giới từ (<i>Он чита́л текст 20 мину́т</i>) · СВ dùng <b>за</b> (hoàn thành trong bao lâu: <i>сде́лал за 30 мину́т</i>) hoặc <b>на</b> (trong hạn bao lâu: <i>взял кни́гу на неде́лю</i>).
                </div>
            </div>

            <div class="clean-card">
                <div class="clean-label"><span>Bảng tổng hợp Cặp động từ НСВ — СВ hay dùng nhất theo Cách chi phối</span><span>Ưu tiên ôn thi</span></div>
                <table class="clean-table">
                    <thead><tr><th>Nhóm Cách chi phối</th><th>Các cặp động từ НСВ — СВ thiết yếu</th></tr></thead>
                    <tbody>
                        <tr><td><b>+ Cách 4</b><br/>(Кого́? Что?)</td><td>
                            <b>ви́деть — уви́деть</b> (thấy) · <b>писа́ть — написа́ть</b> (viết) · <b>чита́ть — прочита́ть</b> (đọc) · <b>повторя́ть — повтори́ть</b> (nhắc lại) · <b>изуча́ть — изучи́ть</b> (nghiên cứu) · <b>понима́ть — поня́ть</b> (hiểu) · <b>покупа́ть — купи́ть</b> (mua) · <b>гото́вить — пригото́вить</b> (nấu/chuẩn bị) · <b>де́лать — сде́лать</b> (làm) · <b>вспомина́ть — вспо́мнить</b> (nhớ lại) · <b>встреча́ть — встре́тить</b> (gặp/đón) · <b>поздравля́ть — поздра́вить</b> (chúc mừng) · <b>открыва́ть — откры́ть</b> (mở) · <b>закрыва́ть — закры́ть</b> (đóng) · <b>получа́ть — получи́ть</b> (nhận) · <b>приглаша́ть — пригласи́ть</b> (mời) · <b>исправля́ть — испра́вить</b> (sửa lỗi) · <b>проси́ть — попроси́ть</b> (nhờ) · <b>спра́шивать — спроси́ть</b> (hỏi) · <b>реша́ть — реши́ть</b> (giải/quyết định) · <b>слу́шать — послу́шать</b> (nghe) · <b>смотре́ть — посмотре́ть</b> (xem) · <b>учи́ть — вы́учить</b> (học thuộc) · <b>петь — спеть</b> (hát) · <b>благодари́ть — поблагодари́ть</b> (cảm ơn)
                        </td></tr>
                        <tr><td><b>+ Cách 3</b><br/>(Кому́? + C4 / о C6 / инф.)</td><td>
                            <b>звони́ть — позвони́ть</b> (gọi) · <b>говори́ть — сказа́ть</b> (nói) · <b>сообща́ть — сообщи́ть</b> (báo tin) · <b>расска́зывать — рассказа́ть</b> (kể) · <b>пока́зывать — показа́ть</b> (cho xem) · <b>дава́ть — дать</b> (cho) · <b>дари́ть — подари́ть</b> (tặng) · <b>объясня́ть — объясни́ть</b> (giải thích) · <b>передава́ть — переда́ть</b> (chuyển) · <b>посыла́ть — посла́ть</b> (gửi đi) · <b>присыла́ть — присла́ть</b> (gửi đến) · <b>помога́ть — помо́чь</b> (giúp) · <b>сове́товать — посове́товать</b> (khuyên) · <b>разреша́ть — разреши́ть</b> (cho phép) · <b>обеща́ть — пообеща́ть</b> (hứa) · <b>меша́ть — помеша́ть</b> (làm phiền) · <b>нра́виться — понра́виться</b> (thích)
                        </td></tr>
                        <tr><td><b>+ Cách 5</b><br/>(с кем? / кем? чем?)</td><td>
                            <b>догова́риваться — договори́ться</b> (thỏa thuận) · <b>встреча́ться — встре́титься</b> (gặp nhau) · <b>знако́миться — познако́миться</b> (làm quen) · <b>сове́товаться — посове́товаться</b> (bàn bạc) · <b>спо́рить — поспо́рить</b> (tranh luận) · <b>ссо́риться — поссо́риться</b> (cãi nhau) · <b>мири́ться — помири́ться</b> (làm hòa) · <b>занима́ться — заня́ться</b> (học/tập) · <b>станови́ться — стать</b> (trở thành) · <b>интересова́ться — заинтересова́ться</b> (quan tâm) · <b>владе́ть</b> (nắm vững) · <b>управля́ть</b> (điều khiển)
                        </td></tr>
                    </tbody>
                </table>
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

            <div class="clean-card">
                <div class="clean-label"><span>Đầy đủ 14 cặp Động từ chuyển động &amp; 14 Tiền tố đổi thể (НСВ ↔ СВ)</span></div>
                <table class="clean-table">
                    <thead><tr><th>Nghĩa</th><th>Nhóm 1 (1 hướng)</th><th>Nhóm 2 (Đa hướng)</th><th>Tiền tố thông dụng</th><th>Ý nghĩa tiền tố</th></tr></thead>
                    <tbody>
                        <tr><td>Đi bộ / Đi xe</td><td>идти́ / е́хать</td><td>ходи́ть / е́здить</td><td><b>по- / при- / у-</b></td><td>bắt đầu đi / đến nơi / rời đi</td></tr>
                        <tr><td>Chạy / Bay</td><td>бежа́ть / лете́ть</td><td>бе́гать / лета́ть</td><td><b>в- (во-) / вы-</b></td><td>đi vào trong / đi ra ngoài</td></tr>
                        <tr><td>Bơi, đi tàu / Leo</td><td>плыть / лезть</td><td>пла́вать / ла́зать</td><td><b>под- / от-</b></td><td>lại gần / lùi ra xa</td></tr>
                        <tr><td>Bò / Lang thang</td><td>ползти́ / брести́</td><td>по́лзать / броди́ть</td><td><b>пере- / про-</b></td><td>băng qua / đi xuyên qua, đi lố</td></tr>
                        <tr><td>Dẫn dắt / Chở xe</td><td>вести́ / везти́</td><td>води́ть / вози́ть</td><td><b>за- / до-</b></td><td>ghé qua / đi tới tận đích</td></tr>
                        <tr><td>Mang tay / Xách</td><td>нести́ / тащи́ть</td><td>носи́ть / таска́ть</td><td><b>об- (обо-) / с-</b></td><td>đi vòng quanh / đi xuống, tụ họp</td></tr>
                        <tr><td>Đuổi theo / Lăn</td><td>гнать / кати́ть</td><td>гоня́ть / ката́ть</td><td><b>раз- (рас-) / на-</b></td><td>tản ra nhiều hướng / va chạm</td></tr>
                    </tbody>
                </table>
                <div class="note-callout">
                    <b>Quy tắc vàng tạo cặp thể СВ / НСВ cho Động từ chuyển động:</b><br/>
                    • <b>Nhóm 1 (1 chiều) + Tiền tố → Thể Hoàn thành (СВ)</b>: <i>прийти́, прие́хать, уйти́, вы́йти, зайти́</i>.<br/>
                    • <b>Nhóm 2 (đa chiều) + Tiền tố → Thể Chưa hoàn thành (НСВ)</b>: <i>приходи́ть, приезжа́ть, уходи́ть, выходи́ть, заходи́ть</i>.
                </div>
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