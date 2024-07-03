# Import core libraries

import pickle
import typing
import varfile
import hashlib
import random


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


# Sugarcoated Functions

def hash_user(user_id: int) -> str:
    seed = random.randint(a=0, b=100000)
    return hashlib.md5(string=str(user_id+seed).encode()).hexdigest() + str(seed).zfill(6)


def verify_user(user_id: int, user_hash: str) -> bool:
    seed = int(user_hash[-6:])
    return user_hash == hashlib.md5(string=str(user_id+seed).encode()).hexdigest() + str(seed).zfill(6)
