# Import core libraries

import pickle
import typing
import varfile


# Define Database Type

class Database(typing.TypedDict):
    banned_users: typing.Set[int]
    msg_list: typing.List[int]
    user_timings: typing.Dict[int, int]
    images: typing.Dict[int, str]


# Database Core Functions

def save(db: Database, name: str = varfile.DATABASE_FILE) -> None:
    with open(file=name, mode="wb") as f:
        pickle.dump(obj=db, file=f)


def load(name: str = varfile.DATABASE_FILE) -> Database:
    try:
        with open(file=name, mode="rb") as f:
            return pickle.load(file=f)
        
    except FileNotFoundError:
        db: Database = {
            "banned_users": set(),
            "msg_list": [],
            "user_timings": {},
            "images": {}
        }

        save(db=db)
        
        return db


# Decorator Functions

def sync(func: typing.Callable) -> typing.Callable:
    def wrapper(*args, **kwargs) -> None:
        db: Database = load()
        result = func(db=db, *args, **kwargs) if "db" in func.__code__.co_varnames and "db" not in kwargs else func(*args, **kwargs)
        save(db=result)

    return wrapper


def syncn(func: typing.Callable) -> typing.Callable:
    def wrapper(*args, **kwargs) -> typing.Any:
        db: Database = load()
        result = func(db=db, *args, **kwargs) if "db" in func.__code__.co_varnames and "db" not in kwargs else func(*args, **kwargs)
        return result

    return wrapper
