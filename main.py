from flask import Flask, render_template, abort
import json
from collections import defaultdict
import os

app = Flask(__name__)

# Конфигурация для GitHub Pages
# Устанавливаем APPLICATION_ROOT для работы с подпапкой
app.config['APPLICATION_ROOT'] = '/ITMOHistoryFeedback'

DATA_PATH = 'data/fidbek po istorii.json'

# _точные_ формулировки вопросов из вашего JSON
SUBJECT_Q  = 'Какой предмет у тебя был?'
LECTURER_Q = 'Кто  у тебя был лектором?'  # две пробелы после "Кто"
ID_Q        = 'ID'
LECTURE_COMPLEXITY_Q = 'Оцени степень сложности лекций'
LECTURE_INTEREST_Q  = ' Оцени степень интересности лекций'  # обратите внимание на ведущий пробел
PRACTICE_COMPLEXITY_Q = 'Оцени степень сложности практик'
PRACTICE_INTEREST_Q = 'Оцени степень интересности практик'
LECTURER_FEEDBACK_Q = 'Что можешь рассказать о лекциях, преподавателе, что делали ? Тут можно расписать что угодно, всё что ты считаешь важным. Эта информация будет передана следующим поколениям.'
PRACTICE_FEEDBACK_Q = 'Что можешь рассказать о практиках, преподавателе, чем занимались? Тут можно расписать что угодно, всё что ты считаешь важным. Эта информация будет передана следующим поколениям.'
PRACTITIONER_Q = 'Кто у тебя был практиком?'

SCORE_MIN = 1.0
SCORE_MAX = 10.0

DEFAULT_LECTURERS = {
    'Реформы и реформаторы в истории России':                      'Вычеров Дмитрий Александрович',
    'Россия в истории современных международных отношений':'Богомазов Николай Иванович',
    'История России и мира в ХХ веке':                       'Пригодич Никита Дмитриевич',
    'Социальная история России':                      'Мунжукова Светлана Игоревна',
    'История русской культуры в контексте мировой культуры':     'Жиркова Галина Петровна',
    'История российской науки и техники':      'Васильев Андрей Владимирович, Белоусов Александр Сергеевич',
}

# Краткие названия предметов - здесь можете настроить как нужно
SUBJECT_SHORT_NAMES = {
    'Реформы и реформаторы в истории России': 'Реформы и реформаторы',
    'Россия в истории современных международных отношений': 'Международные отношения',
    'История России и мира в ХХ веке': 'ХХ век',
    'Социальная история России': 'Социальная история',
    'История русской культуры в контексте мировой культуры': 'Российская культуры',
    'История российской науки и техники': 'Наука и техника',
}

ALIAS_FIELDS = {
    SUBJECT_Q:  'subject',
    LECTURER_Q: 'lecturer',
    ID_Q:       'id',
}

def load_raw():
    with open(DATA_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

def parse_responses(raw):
    parsed = []
    for entry in raw:
        temp = defaultdict(list)
        for question, answer in entry:
            temp[question].append(answer)

        # 1. Собираем ответы (самый длинный, если их несколько)
        record = {}
        for q, vals in temp.items():
            record[q] = vals[0] if len(vals) == 1 else max(vals, key=lambda s: len(s or ''))

        # 2. Если по вопросу о лекторе только '—', подменяем сразу в этом ключе
        subj = record.get(SUBJECT_Q, '')
        if record.get(LECTURER_Q, '—') in ('', '—') and subj in DEFAULT_LECTURERS:
            record[LECTURER_Q] = DEFAULT_LECTURERS[subj]

        # 3. Дублируем в короткие alias-поля
        for long_key, short_key in ALIAS_FIELDS.items():
            record[short_key] = record.get(long_key, '—')

        parsed.append(record)
    return parsed



def aggregate_by(question_text):
    groups = defaultdict(list)
    for r in RESPONSES:
        # если вопрос вдруг отсутствует — попадёт в группу '—'
        key = r.get(question_text, '—')
        groups[key].append(r)
    return groups

# загрузка и парсинг
RAW = load_raw()
RESPONSES = parse_responses(RAW)

def group_by(field):
    groups = defaultdict(list)
    for r in RESPONSES:
        # На всякий случай: если поля нет или None, попадёт в группу '—'
        key = r.get(field) or '—'
        groups[key].append(r)
    return groups


# агрегируем
LECTURERS = group_by('lecturer')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/reviews')
def reviews():
    # Собираем все отзывы с дополнительной информацией
    all_reviews = []
    
    for lecturer_name, responses in LECTURERS.items():
        for resp in responses:
            # Данные о лекциях
            lecture_complexity = resp.get(LECTURE_COMPLEXITY_Q, '—')
            lecture_interest = resp.get(LECTURE_INTEREST_Q, '—')
            lecture_feedback = resp.get(LECTURER_FEEDBACK_Q, '—')
            
            # Данные о практиках
            practice_complexity = resp.get(PRACTICE_COMPLEXITY_Q, '—')
            practice_interest = resp.get(PRACTICE_INTEREST_Q, '—')
            practice_feedback = resp.get(PRACTICE_FEEDBACK_Q, '—')
            practitioner = resp.get(PRACTITIONER_Q, '—')
            
            # Если практик не указан, используем имя лектора
            if not practitioner or practitioner == '—' or practitioner.strip() == '':
                practitioner = lecturer_name
            
            all_reviews.append({
                'id': resp.get('id', '—'),
                'lecturer': lecturer_name,
                'practitioner': practitioner,
                'subject': resp.get('subject', '—'),
                'lectures': {
                    'complexity': lecture_complexity,
                    'interest': lecture_interest,
                    'feedback': lecture_feedback
                },
                'practices': {
                    'complexity': practice_complexity,
                    'interest': practice_interest,
                    'feedback': practice_feedback
                }
            })
    
    # Группируем отзывы по предметам для отображения
    reviews_by_subject = defaultdict(list)
    for review in all_reviews:
        subject = review['subject']
        reviews_by_subject[subject].append(review)
    
    # Сортируем отзывы внутри каждого предмета по ID
    for subject in reviews_by_subject:
        reviews_by_subject[subject].sort(key=lambda x: int(x['id']) if x['id'].isdigit() else 0)
    
    # Собираем уникальных лекторов и их практиков для фильтров
    lecturers_with_practitioners = {}
    for review in all_reviews:
        lecturer = review['lecturer']
        practitioner = review['practitioner']
        
        if lecturer not in lecturers_with_practitioners:
            lecturers_with_practitioners[lecturer] = set()
        lecturers_with_practitioners[lecturer].add(practitioner)
    
    # Преобразуем в удобный формат для шаблона
    filter_data = []
    for lecturer, practitioners in sorted(lecturers_with_practitioners.items()):
        filter_data.append({
            'lecturer': lecturer,
            'practitioners': sorted(practitioners)
        })
    
    # Собираем статистику по преподавателям (лекторам и практикам)
    teacher_stats = {}
    
    # Статистика по лекторам (по лекциям)
    for lecturer_name, responses in LECTURERS.items():
        complexity_total, complexity_cnt = 0.0, 0
        interest_total, interest_cnt = 0.0, 0
        
        for r in responses:
            # Сложность лекций
            raw_complexity = r.get(LECTURE_COMPLEXITY_Q)
            try:
                num = float(raw_complexity)
                complexity_total += num
                complexity_cnt += 1
            except (TypeError, ValueError):
                pass
                
            # Интерес лекций
            raw_interest = r.get(LECTURE_INTEREST_Q)
            try:
                num = float(raw_interest)
                interest_total += num
                interest_cnt += 1
            except (TypeError, ValueError):
                pass
        
        complexity_avg = round(complexity_total / complexity_cnt, 1) if complexity_cnt else None
        interest_avg = round(interest_total / interest_cnt, 1) if interest_cnt else None
        
        teacher_stats[lecturer_name] = {
            'complexity': complexity_avg,
            'interest': interest_avg,
            'type': 'lecturer'
        }
    
    # Статистика по практикам (по практикам)
    practitioner_stats = {}
    for review in all_reviews:
        practitioner = review['practitioner']
        
        if practitioner not in practitioner_stats:
            practitioner_stats[practitioner] = {
                'complexity_total': 0.0,
                'complexity_cnt': 0,
                'interest_total': 0.0,
                'interest_cnt': 0
            }
        
        # Сложность практик
        if review['practices']['complexity'] != '—':
            try:
                num = float(review['practices']['complexity'])
                practitioner_stats[practitioner]['complexity_total'] += num
                practitioner_stats[practitioner]['complexity_cnt'] += 1
            except (TypeError, ValueError):
                pass
        
        # Интерес практик
        if review['practices']['interest'] != '—':
            try:
                num = float(review['practices']['interest'])
                practitioner_stats[practitioner]['interest_total'] += num
                practitioner_stats[practitioner]['interest_cnt'] += 1
            except (TypeError, ValueError):
                pass
    
    # Вычисляем средние для практиков
    for practitioner, stats in practitioner_stats.items():
        complexity_avg = round(stats['complexity_total'] / stats['complexity_cnt'], 1) if stats['complexity_cnt'] else None
        interest_avg = round(stats['interest_total'] / stats['interest_cnt'], 1) if stats['interest_cnt'] else None
        
        # Если практик не является лектором, добавляем его в teacher_stats
        if practitioner not in teacher_stats:
            teacher_stats[practitioner] = {
                'complexity': complexity_avg,
                'interest': interest_avg,
                'type': 'practitioner'
            }
        else:
            # Если практик также является лектором, добавляем статистику по практикам
            teacher_stats[practitioner]['practice_complexity'] = complexity_avg
            teacher_stats[practitioner]['practice_interest'] = interest_avg
    
    # Статистика по практикам
    practitioners_data = defaultdict(list)
    for review in all_reviews:
        practitioner = review['practitioner']
        if practitioner != review['lecturer']:  # Только если практик отличается от лектора
            practitioners_data[practitioner].append(review)
    
    for practitioner_name, reviews in practitioners_data.items():
        complexity_total, complexity_cnt = 0.0, 0
        interest_total, interest_cnt = 0.0, 0
        
        for review in reviews:
            # Сложность практик
            try:
                if review['practices']['complexity'] != '—':
                    num = float(review['practices']['complexity'])
                    complexity_total += num
                    complexity_cnt += 1
            except (TypeError, ValueError):
                pass
                
            # Интерес практик
            try:
                if review['practices']['interest'] != '—':
                    num = float(review['practices']['interest'])
                    interest_total += num
                    interest_cnt += 1
            except (TypeError, ValueError):
                pass
        
        complexity_avg = round(complexity_total / complexity_cnt, 1) if complexity_cnt else None
        interest_avg = round(interest_total / interest_cnt, 1) if interest_cnt else None
        
        if practitioner_name not in teacher_stats:
            teacher_stats[practitioner_name] = {
                'complexity': complexity_avg,
                'interest': interest_avg,
                'type': 'practitioner'
            }
    
    # Группируем преподавателей по предметам для фильтров
    subjects_with_teachers = {}
    for review in all_reviews:
        subject = review['subject']
        lecturer = review['lecturer']
        
        if subject not in subjects_with_teachers:
            subjects_with_teachers[subject] = {}
        
        if lecturer not in subjects_with_teachers[subject]:
            # Находим всех практиков для этого лектора
            practitioners = set()
            for r in all_reviews:
                if r['lecturer'] == lecturer:
                    practitioners.add(r['practitioner'])
            
            subjects_with_teachers[subject][lecturer] = {
                'practitioners': sorted(practitioners),
                'stats': teacher_stats.get(lecturer, {})
            }
    
    return render_template('reviews.html', 
                         reviews_by_subject=dict(reviews_by_subject),
                         filter_data=filter_data,
                         teacher_stats=teacher_stats,
                         subjects_with_teachers=subjects_with_teachers)



def invert_score(val: float) -> float:
    return SCORE_MAX + SCORE_MIN - val

@app.route('/lecturers')
def lecturers():
    stats = []
    for name, responses in LECTURERS.items():
        # Считаем сложность лекций (инвертируем)
        complexity_total, complexity_cnt = 0.0, 0
        # Считаем интерес лекций (не инвертируем)
        interest_total, interest_cnt = 0.0, 0
        
        # Собираем предметы лектора
        subjects = set()
        
        for r in responses:
            subject = r.get('subject', '')
            if subject and subject != '—':
                subjects.add(subject)
                
            # Сложность лекций
            raw_complexity = r.get(LECTURE_COMPLEXITY_Q)
            try:
                num = float(raw_complexity)
                complexity_total += num  # НЕ инвертируем для сложности
                complexity_cnt += 1
            except (TypeError, ValueError):
                pass
                
            # Интерес лекций
            raw_interest = r.get(LECTURE_INTEREST_Q)
            try:
                num = float(raw_interest)
                interest_total += num  # не инвертируем для интереса
                interest_cnt += 1
            except (TypeError, ValueError):
                pass
        
        complexity_avg = round(complexity_total / complexity_cnt, 2) if complexity_cnt else None
        interest_avg = round(interest_total / interest_cnt, 2) if interest_cnt else None
        
        # Создаем краткие названия предметов используя словарь
        subject_shorts = []
        for s in sorted(subjects)[:2]:  # берем максимум 2 предмета
            short_name = SUBJECT_SHORT_NAMES.get(s, s)  # используем краткое название или оригинал
            subject_shorts.append(short_name)
        
        subject_short = ', '.join(subject_shorts)
        if len(subjects) > 2:
            subject_short += '...'
        
        stats.append({
            'name': name, 
            'complexity_avg': complexity_avg,
            'interest_avg': interest_avg,
            'reviews': len(responses),
            'subjects': subject_short
        })
    
    return render_template('lecturers.html', lecturers=stats)


@app.route('/lecturers/<name>')
def lecturer_detail(name):
    if name not in LECTURERS:
        abort(404)
    responses = LECTURERS[name]
    
    # Собираем уникальных практиков для фильтра
    practitioners = set()
    for r in responses:
        practitioner = r.get(PRACTITIONER_Q, '').strip()
        if practitioner and practitioner != '—' and practitioner != '':
            practitioners.add(practitioner)
    
    # Подготавливаем структурированные данные для отображения
    structured_responses = []
    for r in responses:
        # Данные о лекциях
        lecture_complexity = r.get(LECTURE_COMPLEXITY_Q, '—')
        lecture_interest = r.get(LECTURE_INTEREST_Q, '—')
        lecture_feedback = r.get(LECTURER_FEEDBACK_Q, '—')
        
        # Данные о практиках
        practice_complexity = r.get(PRACTICE_COMPLEXITY_Q, '—')
        practice_interest = r.get(PRACTICE_INTEREST_Q, '—')
        practice_feedback = r.get(PRACTICE_FEEDBACK_Q, '—')
        practitioner = r.get(PRACTITIONER_Q, '—')
        # Если практик не указан, используем имя лектора
        if not practitioner or practitioner == '—' or practitioner.strip() == '':
            practitioner = name
        
        structured_responses.append({
            'id': r.get('id', '—'),
            'practitioner': practitioner,
            'lectures': {
                'complexity': lecture_complexity,
                'interest': lecture_interest,
                'feedback': lecture_feedback
            },
            'practices': {
                'complexity': practice_complexity,
                'interest': practice_interest,
                'feedback': practice_feedback
            }
        })
    
    return render_template('lecturer_detail.html',
                           name=name,
                           responses=structured_responses,
                           practitioners=sorted(practitioners))

if __name__ == '__main__':
    # Для разработки
    app.run(debug=True)
