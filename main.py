import flask
from flask import Flask, render_template, redirect, url_for, request, abort

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, Text, Float
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, validators, URLField, DateField, FloatField
from wtforms.validators import DataRequired
import datetime as dt

app = Flask(__name__)
app.config['SECRET_KEY'] = 'abcdefghijklmnop'


class Base(DeclarativeBase):
    pass


app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database3.db'
db = SQLAlchemy(model_class=Base)
db.init_app(app)


class Item(db.Model):
    __tablename__ = "items"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    price: Mapped[float] = mapped_column(Float, nullable=True)
    average: Mapped[float] = mapped_column(Float, nullable=False)
    location: Mapped[str] = mapped_column(String(250), nullable=True)
    on_hand: Mapped[float] = mapped_column(Float, nullable=True)
    needed: Mapped[float] = mapped_column(Float, nullable=True)
    last_counted: Mapped[str] = mapped_column(String(250), nullable=True)
    unit: Mapped[str] = mapped_column(String(250), nullable=True)
    sort: Mapped[str] = mapped_column(String(250), nullable=True)
    group_id: Mapped[int] = mapped_column(Integer, db.ForeignKey("groups.id"))
    # Create reference to the User object. The "posts" refers to the posts property in the User class.
    group = relationship("Group", back_populates="items")


class Group(db.Model):
    __tablename__ = "groups"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    weeks: Mapped[float] = mapped_column(Float, nullable=False)
    items = relationship("Item", back_populates="group")


with app.app_context():
    db.create_all()


class EditForm(FlaskForm):
    name = StringField('Item Name',
                       [validators.DataRequired()], )

    location = StringField(label='Location', validators=[DataRequired(message="need a name")])
    average = FloatField(label='Weekly Average', validators=[DataRequired(message="need an average")])
    on_hand = FloatField(label='Amount on hand')
    price = FloatField(label='Price')
    group = StringField(label='Group')
    unit = StringField(label='Unit')
    submit = SubmitField('Save Changes')


class AddForm(FlaskForm):
    name = StringField('Item Name',
                       [validators.DataRequired()], )

    location = StringField(label='Location', validators=[DataRequired()])
    average = FloatField(label='Weekly Average', validators=[DataRequired()])
    on_hand = FloatField(label='Amount on hand')
    price = FloatField(label='Price')
    group = StringField(label='Group')
    unit = StringField(label='Unit')
    submit = SubmitField('Add Item')


def update(items):
    with app.app_context():
        for item in items:
            item.needed = (item.average * item.group.weeks) - float(item.on_hand)
    return


@app.route('/')
def home():
    #from testy import item
    with app.app_context():
        try:
            GROUP = request.args['GROUP']
        except:
            GROUP = 0
        print(GROUP)
        result = db.session.execute(db.select(Item).order_by(Item.sort))
        all_items = result.scalars().all()
        update(all_items)
        if GROUP != 0:
            selected_group = db.session.execute(db.select(Group).where(Group.name == GROUP)).scalar()
            print(selected_group.name)
            all_items = selected_group.items



        return render_template('index.html', items=all_items)


@app.route('/edit/<item_id>', methods=['GET', 'POST'])
def edit(item_id):
    #from testy import item
    with app.app_context():
        item = db.get_or_404(Item, item_id)
        print(item.group.name)
    form = EditForm(name=item.name, location=item.location, average=item.average, price=item.price,
                    on_hand=item.on_hand, group=item.group.name, unit=item.unit)
    if form.validate_on_submit():
        with app.app_context():
            item = db.get_or_404(Item, item_id)
            item.name = form.name.data
            item.average = form.average.data
            item.location = form.location.data
            item.price = form.price.data
            item.on_hand = form.on_hand.data
            item.group = db.session.execute(db.select(Group).where(Group.name == form.group.data)).scalar()
            item.unit = form.unit.data
            if form.location.data == 'delete':
                db.session.delete(item)
            try:
                db.session.commit()
            except:
                return ("edit failed. check group name spelled correctly")
        return redirect(url_for('home'))
    else:
        return render_template('edit2.html', item=item, form=form)


@app.route('/syrup_count')
def syrup_count():
    #from testy import item
    with app.app_context():
        group = db.session.execute(db.select(Group).where(Group.name == request.args['GROUP'])).scalar()
        return render_template('syrup_count.html', items=group.items, GROUP=request.args['GROUP'])





@app.route('/process', methods=['POST'])
def process():
    form = request.form
    GROUP = request.args['GROUP']
    # print(request.form)
    print(GROUP, "hello")

    #from testy import item
    with app.app_context():
        selected_group = db.session.execute(db.select(Group).where(Group.name == GROUP)).scalar()
        items = selected_group.items
        print(selected_group.name, "halla")
        # items = db.session.execute(db.select(Item).where(Item.group.name == GROUP)).scalars().all()
        for item in items:
            # print(item.name)
            item.on_hand = float(request.form.get(item.name))
            item.needed = (item.average * item.group.weeks) - float(item.on_hand)
            item.last_counted = dt.datetime.now().date()
        db.session.commit()
    return redirect(url_for('order', GROUP=request.args['GROUP']))


@app.route('/order/')
def order():
    #from testy import item

    with app.app_context():
        group = db.session.execute(db.select(Group).where(Group.name == request.args['GROUP'])).scalar()
        WEEKS = group.weeks

        print(group.name, "lujah")
        items = db.session.execute(
            db.select(Item).order_by(Item.sort)).scalars().all()

        # result = db.session.execute(db.select(Item).order_by(Item.sort))
        
        items2 = [item for item in items if item.group.name == request.args['GROUP']]
        for item in items2:
            item.needed = (item.average * item.group.weeks) - float(item.on_hand)
            if item.needed <= 0:
                item.needed = 0
            db.session.commit()
        filtered = [item for item in items2 if item.needed > 0]
        # for item in filtered:
        #     print(item.name, item.needed)
        return render_template('order.html', items=items2, GROUP=request.args['GROUP'], WEEKS = WEEKS)


@app.route('/add', methods=['GET', 'POST'])
def add():
    #from testy import item
    form = AddForm()
    for thing in form:
        print(thing)
    if form.validate_on_submit():
        with app.app_context():
            selected_group = db.session.execute(db.select(Group).where(Group.name == form.group.data)).scalar()
            new_item = Item(name=form.name.data, location=form.location.data, price=form.price.data,
                            on_hand=form.on_hand.data, average=form.average.data, group=selected_group,
                            unit=form.unit.data)
            db.session.add(new_item)
            db.session.commit()
        return redirect(url_for('home'))
    return render_template('edit2.html', form=form, item=0)


if __name__ == "__main__":
    app.run(debug=True, port=5003)
