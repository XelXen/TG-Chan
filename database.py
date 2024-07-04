# Import core libraries

import pickle
import typing
import config
import hashlib
import random


# Define Database Type


class DatabaseType(typing.TypedDict):
    like_ratio: typing.Dict[int, int]
    user_timings: typing.Dict[int, int]
    autodelete: typing.Set[int]


# Database Core Functions


def save(db: DatabaseType, name: str = config.DATABASE_FILE) -> None:
    with open(file=name, mode="wb") as f:
        pickle.dump(obj=db, file=f)


def load(name: str = config.DATABASE_FILE) -> DatabaseType:
    try:
        with open(file=name, mode="rb") as f:
            db: DatabaseType = pickle.load(file=f)
            return db

    except FileNotFoundError:
        db: DatabaseType = {
            "like_ratio": dict(),
            "user_timings": dict(),
            "autodelete": set(),
        }

        save(db=db)

        return db


# Define Database class


class DatabaseSession:
    def __init__(self) -> None:
        self.db = load()

    def __getitem__(self, key) -> typing.Any:
        return self.db[key] if key in self.db else None

    def __setitem__(self, key, value) -> None:
        self.db[key] = value
        save(db=self.db)

    def __delitem__(self, key) -> None:
        del self.db[key]
        save(db=self.db)

    def __contains__(self, key) -> bool:
        return key in self.db

    def __iter__(self) -> typing.Iterator:
        return iter(self.db)

    def reload(self) -> None:
        self.db = load()


# Decorator Functions


def sync(func: typing.Callable) -> typing.Callable:
    def wrapper(*args, **kwargs) -> None:
        db: DatabaseType = load()
        result = (
            func(db=db, *args, **kwargs)
            if "db" in func.__code__.co_varnames and "db" not in kwargs
            else func(*args, **kwargs)
        )
        save(db=result)

    return wrapper


def syncn(func: typing.Callable) -> typing.Callable:
    def wrapper(*args, **kwargs) -> typing.Any:
        db: DatabaseType = load()
        result = (
            func(db=db, *args, **kwargs)
            if "db" in func.__code__.co_varnames and "db" not in kwargs
            else func(*args, **kwargs)
        )
        return result

    return wrapper


# Sugarcoated Functions


def hash_user(user_id: int) -> str:
    seed = random.randint(a=0, b=100000)
    return hashlib.md5(string=str(user_id + seed).encode()).hexdigest() + str(
        seed
    ).zfill(6)


def verify_user(user_id: int, user_hash: str) -> bool:
    seed = int(user_hash[-6:])
    return user_hash == hashlib.md5(
        string=str(user_id + seed).encode()
    ).hexdigest() + str(seed).zfill(6)
