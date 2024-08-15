# Import core libraries

import pickle
import typing
import config
import os
import hashlib

from enum import Enum


# Define Database Schema

class Feedback(Enum):
    LIKE = 1
    DISLIKE = -1

    def __int__(self) -> int:
        return self.value


class PostType(typing.TypedDict):
    feedbacks: typing.Dict[str, Feedback]
    rating: int
    media: typing.Optional[str]


class DatabaseType(typing.TypedDict):
    posts: typing.Dict[int, PostType]
    timings: typing.Dict[str, int]
    autodelete: typing.List[int]


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
        db: DatabaseType = {"posts": {}, "timings": {}, "autodelete": []}
        save(db=db)
        return db


# Sugarcoated Functions

def hash(num: int) -> str:
    return hashlib.md5(string=str(num + config.SEED).encode()).hexdigest()

def add_post(db: DatabaseType, id: int, media: str = None) -> None:
    if id in db["posts"]:
        return

    db["posts"][id] = {"feedbacks": {}, "media": media, "rating": 0}


def remove_post(db: DatabaseType, id: int) -> None:
    if id not in db["posts"]:
        return
    
    if id in db["autodelete"]:
        del db["autodelete"][id]

    if db["posts"][id]["media"] is not None:
        os.remove(db["posts"][id]["media"])

    del db["posts"][id]
