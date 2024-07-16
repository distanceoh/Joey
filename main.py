import flask
from flask import Flask, render_template, redirect, url_for, request

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Text, Float
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, validators, URLField, DateField, FloatField
from wtforms.validators import DataRequired
import datetime as dt

# WEEKS = 2
app = Flask(__name__)
app.config['SECRET_KEY'] = 'abcdefghijklmnop'


class Base(DeclarativeBase):
    pass


app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database2.db'
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
    last_counted: Mapped[str] = mapped_column(String(250), nullable=True)
    group: Mapped[str] = mapped_column(String(250), nullable=True)
    unit : Mapped[str] = mapped_column(String(250), nullable = True)

with app.app_context():
    db.create_all()


class EditForm(FlaskForm):
    name = StringField('Item Name',
                       [validators.DataRequired()], )

    location = StringField(label='Location', validators=[DataRequired(message="need a name")])
    average = FloatField(label='Weekly Average', validators=[DataRequired(message = "need an average")])
    on_hand = FloatField(label='Amount on hand')
    price = FloatField(label='Price')
    group = StringField(label = 'Group')
    unit = StringField(label = 'Unit')
    submit = SubmitField('Save Changes')



class AddForm(FlaskForm):
    name = StringField('Item Name',
                       [validators.DataRequired()], )

    location = StringField(label='Location', validators=[DataRequired()])
    average = FloatField(label='Weekly Average', validators=[DataRequired()])
    on_hand = FloatField(label='Amount on hand')
    price = FloatField(label='Price')
    group = StringField(label='Group')
    unit = StringField(label = 'Unit')
    submit = SubmitField('Add Item')


def update(items):
    with app.app_context():
        for item in items:
            if item.group == 'Flavor':
                WEEKS = 2
            else:
                WEEKS = 1
            item.needed = (item.average * WEEKS) - float(item.on_hand)
    return


@app.route('/')
def home():
    #from testy import item
    with app.app_context():
        result = db.session.execute(db.select(Item).order_by(Item.name))
        all_books = result.scalars().all()
        update(all_books)

    return render_template('index.html', items=all_books)


@app.route('/edit/<item_id>', methods=['GET', 'POST'])
def edit(item_id):
    #from testy import item
    with app.app_context():
        item = db.get_or_404(Item, item_id)
    form = EditForm(name=item.name, location=item.location, average=item.average, price=item.price,
                    on_hand=item.on_hand, group = item.group, unit = item.unit)
    if form.validate_on_submit():
        with app.app_context():
            item = db.get_or_404(Item, item_id)
            item.name = form.name.data
            item.average = form.average.data
            item.location = form.location.data
            item.price = form.price.data
            item.on_hand = form.on_hand.data
            item.group = form.group.data
            item.unit = form.unit.data
            if form.location.data == 'delete':
                db.session.delete(item)
            db.session.commit()
        return redirect(url_for('home'))
    else:
        print('negative')
        return render_template('edit2.html', item=item, form=form)


@app.route('/syrup_count')
def syrup_count():
    #from testy import item
    with app.app_context():
        items = db.session.execute(
            db.select(Item).order_by(Item.name).where(Item.location == 'Webstaurant')).scalars().all()
        filtered = [item for item in items if item.group=='Flavor']
    return render_template('syrup_count.html', items=filtered, GROUP = 'Flavor', WEEKS = request.args['WEEKS'])

@app.route('/dry_count')
def dry_count():
    with app.app_context():
        items = db.session.execute(
            db.select(Item).order_by(Item.name).where(Item.location == 'Webstaurant')).scalars().all()
        filtered = [item for item in items if item.group=='Dry']
    return render_template('syrup_count.html', items=filtered, GROUP = 'Dry', WEEKS = request.args['WEEKS'])

@app.route('/sysco')
def sysco():
    with app.app_context():
        items = db.session.execute(
            db.select(Item).order_by(Item.name).where(Item.location == 'Sysco')).scalars().all()
        filtered = [item for item in items if item.group=='Sysco']
    return render_template('syrup_count.html', items=filtered, GROUP = 'Sysco', WEEKS = request.args['WEEKS'])



@app.route('/process', methods=['POST'])
def process():
    form = request.form
    GROUP = request.args['GROUP']
    if GROUP == 'Flavor':
        WEEKS = 2
    else:
        WEEKS = 1
    # print(request.form)
    #from testy import item
    with app.app_context():
        items = db.session.execute(db.select(Item).where(Item.group==GROUP)).scalars().all()
        for item in items:
            item.on_hand = float(request.form.get(item.name))
            item.needed = (item.average * WEEKS) - float(item.on_hand)
            item.last_counted = dt.datetime.now().date()
        db.session.commit()
    return redirect(url_for('order', GROUP = GROUP, WEEKS = WEEKS))


@app.route('/order/')
def order():
    #from testy import item

    with app.app_context():
        items = db.session.execute(
            db.select(Item).order_by(Item.name)).scalars().all()
        items2 = [item for item in items if item.group==request.args['GROUP']]
        for item in items2:
            item.needed = (item.average * int(request.args['WEEKS'])) - float(item.on_hand)
            if item.needed <= 0:
                    item.needed = 0
            db.session.commit()
        filtered = [item for item in items2 if item.needed > 0]
        # for item in filtered:
        #     print(item.name, item.needed)
    return render_template('order.html', items=items2, WEEKS=request.args['WEEKS'], GROUP = request.args['GROUP'])


@app.route('/add', methods=['GET', 'POST'])
def add():
    #from testy import item
    form = AddForm()
    for thing in form:
        print(thing)
    if form.validate_on_submit():
        with app.app_context():
            new_item = Item(name=form.name.data, location=form.location.data, price=form.price.data,
                            on_hand=form.on_hand.data, average=form.average.data, group = form.group.data, unit = form.unit.data)
            db.session.add(new_item)
            db.session.commit()
        return redirect(url_for('home'))
    return render_template('edit2.html', form=form, item=0)


if __name__ == "__main__":
    app.run(debug=True, port=5003)
