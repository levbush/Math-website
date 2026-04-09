from collections import namedtuple
from enum import IntEnum, auto
from config import SUBJECTS


class SUBJECT:
	def __init__(self, name):
		self.name = name
	
	def __eq__(self, value):
		return isinstance(value, SUBJECT)


class AchievementType(IntEnum):
	solved = auto()
	correct_streak = auto()
      
	@staticmethod
	def solved_by_subject(subject):
		return SUBJECT(subject)
    
	ultimate = auto()
    


Achievement = namedtuple('Achievement', ('name', 'type', 'condition', 'condition_reference_point'))
ACHIEVEMENTS = [
    Achievement("5 solved tasks", AchievementType.solved, int.__ge__, 5),
    Achievement("10 solved tasks", AchievementType.solved, int.__ge__, 10),
    Achievement("50 solved tasks", AchievementType.solved, int.__ge__, 50),
    Achievement("100 solved tasks", AchievementType.solved, int.__ge__, 100),
    Achievement("1000 solved tasks", AchievementType.solved, int.__ge__, 1000),

    Achievement("2 correct trials in a row", AchievementType.correct_streak, int.__ge__, 2),
    Achievement("5 correct trials in a row", AchievementType.correct_streak, int.__ge__, 5),
    Achievement("10 correct trials in a row", AchievementType.correct_streak, int.__ge__, 10),
    Achievement("50 correct trials in a row", AchievementType.correct_streak, int.__ge__, 50),
    Achievement("100 correct trials in a row", AchievementType.correct_streak, int.__ge__, 100),
] + \
sum(
	[
		[
			Achievement(f"{i} solved tasks: {subject}", AchievementType.solved_by_subject(subject), int.__ge__, i) for i in (5, 10, 50, 100, 1000)
		] for subject in SUBJECTS
	]
	, start=[]
)
ACHIEVEMENTS.append(Achievement("Complete all achievements!", AchievementType.ultimate, int.__eq__, len(ACHIEVEMENTS)))

def _default_achievements() -> dict[str, bool]:
    return {achievement.name: False for achievement in ACHIEVEMENTS}