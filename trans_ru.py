from logic.achievements import ACHIEVEMENTS

SUBJECTS_RU = {
    'Arithmetic': 'Арифметика',
    'Algebra': 'Алгебра',
    'Pre-Algebra': 'Начальная алгебра',
    'Geometry': 'Геометрия',
    'Probability & Statistics': 'Вероятность и статистика',
    'Combinatorics': 'Комбинаторика',
    'Number Theory': 'Теория чисел',
    'Logic & Discrete Math': 'Логика и дискретная математика',
    'Linear Algebra': 'Линейная алгебра',
    'Trigonometry': 'Тригонометрия',
    'Calculus': 'Математический анализ',
    'Other': 'Другое'
}

ACHIEVEMENTS_RU = [
    "5 решённых задач",
    "10 решённых задач",
    '50 решённых задач',
    '100 решённых задач',
    '1000 решённых задач',

    '2 правильные попытки подряд',
    '5 правильных попыток подряд',
    '10 правильных попыток подряд',
    '50 правильных попыток подряд',
    '100 правильных попыток подряд',
] + \
sum(
	[
		[
			f"{i} решённых задач: {subject}" for i in (5, 10, 50, 100, 1000)
		] for subject in SUBJECTS_RU.values()
	]
	, start=[]
)
ACHIEVEMENTS_RU.append("Выполнить все достижения!")

ACHIEVEMENTS_RU = dict(zip([ac.name for ac in ACHIEVEMENTS], ACHIEVEMENTS_RU))