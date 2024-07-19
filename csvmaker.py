import pandas
import sqlalchemy
from sqlalchemy import create_engine
# from testy2 import Item, Group
import os
x = os.path.abspath(os.getcwd())
print(x)
uri = 'sqlite:///instance/database3.db'
print(uri)


# df = pandas.read_sql_table('items', 'sqlite:///database3.db')
# print(df)



# SQLAlchemy connectable
engine = create_engine(f'sqlite:////{x}\instance\database3.db')
engine = create_engine(uri)


# table named 'contacts' will be returned as a dataframe.
df = pandas.read_sql_table('items', engine)
df.to_csv('out.csv', index = False)
print(df)
