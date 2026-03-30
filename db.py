from sqlalchemy import create_engine, Column, String, Integer, JSON
from sqlalchemy.orm import declarative_base, Session
from werkzeug.security import generate_password_hash, check_password_hash
from config import DB_PATH, SUBJECTS

engine = create_engine(f'sqlite:///{DB_PATH}', echo=False)

Base = declarative_base()


class User(Base):
    __tablename__ = 'users'

    uid = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, nullable=False)
    password_hash = Column(String, nullable=False)
    solved = Column(JSON, nullable=False, default=list)
    stats = Column(JSON, nullable=False, default=dict)


def init_db():
    Base.metadata.create_all(engine)


def _default_stats():
    return {key: 0 for key in SUBJECTS + [str(d) for d in range(1, 11)]}


def register_user(username: str, password: str) -> bool:
    with Session(engine) as s:
        if s.get(User, username):
            return False
        s.add(User(
            username=username,
            password_hash=generate_password_hash(password),
            solved=[],
            stats=_default_stats(),
        ))
        s.commit()
        return True


def check_user(username: str, password: str) -> bool:
    with Session(engine) as s:
        user = s.get(User, username)
        if not user:
            return False
        return check_password_hash(user.password_hash, password)


def get_solved(username: str) -> set:
    with Session(engine) as s:
        user = s.get(User, username)
        if not user:
            return set()
        return set(user.solved)


def get_stats(username: str) -> dict:
    with Session(engine) as s:
        user = s.get(User, username)
        if not user:
            return _default_stats()
        return user.stats


def mark_solved(username: str, problem_id: str, subject: str, difficulty: int):
    with Session(engine) as s:
        user = s.get(User, username)
        if not user:
            return
        solved = list(user.solved)
        if problem_id not in solved:
            solved.append(problem_id)
        stats = dict(user.stats)
        stats[subject] = stats.get(subject, 0) + 1
        stats[str(difficulty)] = stats.get(str(difficulty), 0) + 1
        user.solved = solved
        user.stats = stats
        s.commit()
