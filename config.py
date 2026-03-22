import dotenv, os
from dataclasses import dataclass, field


dotenv.load_dotenv()

TOKEN = os.getenv('BOT_TOKEN')

# db related constants
DB_PATH = 'bot.db'


@dataclass
class Data:
    solved: set = field(default_factory=set)
    stats: dict = field(
        default_factory=lambda: {
            'Algebra': 0,
            'Arithmetic': 0,
            'Calculus': 0,
            'Combinatorics': 0,
            'Geometry': 0,
            'Linear Algebra': 0,
            'Logic & Discrete Math': 0,
            'Multidisciplinary': 0,
            'Number Theory': 0,
            'Other': 0,
            'Pre-Algebra': 0,
            'Probability & Statistics': 0,
            'Trigonometry': 0,
            '1': 0,
            '2': 0,
            '3': 0,
            '4': 0,
            '5': 0,
            '6': 0,
            '7': 0,
            '8': 0,
            '9': 0,
            '10': 0,
        }
    )


DEFAULT_DATA = Data()

# Dataset related constants
SUBJECTS = [
    'Arithmetic',
    'Algebra',
    'Pre-Algebra',
    'Geometry',
    'Probability & Statistics',
    'Combinatorics',
    'Number Theory',
    'Logic & Discrete Math',
    'Linear Algebra',
    'Trigonometry',
    'Calculus',
    'Other'
]

repo_id = "levbush/math_tasks_split"
repo_type = "dataset"

FILE_LENGTH = 1000
