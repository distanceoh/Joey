import pandas
import pprint as p
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Text, Float, DATE
import csv

app = Flask(__name__)
app.config['SECRET_KEY'] = 'abcdefghijklmnop'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database2.db'


class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)
db.init_app(app)


class Item(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    average: Mapped[float] = mapped_column(Float, nullable=False)
    location: Mapped[str] = mapped_column(String(250), nullable=False)
    on_hand: Mapped[float] = mapped_column(Float, nullable=True)
    needed: Mapped[float] = mapped_column(Float, nullable=True)
    last_counted: Mapped[str] = mapped_column(String(250), nullable = True)


with app.app_context():
    db.create_all()


def create_records(name, price, location, average, on_hand):
    with app.app_context():
        old_book = db.session.execute(db.select(Item).where(Item.name == name)).scalar()
        new_book = Item(name=name, price=price, location=location, average=average, on_hand=on_hand)
        if not old_book:
            db.session.add(new_book)
        else:
            old_book.price = price
            old_book.location = location
            old_book.average = average
        db.session.commit()


if __name__ == '__main__':
    data = pandas.read_csv("static/data/testdata2.csv")
    data = data.to_dict(orient='records')
    p.pprint(data)
    for row in data:
        create_records(name=row['Name'], price=row['price'], location=row['location'], average=row['average'],
                       on_hand=row['on_hand'])
