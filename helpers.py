import bcrypt
from models import Recipe
from database import SessionLocal, engine
from datetime import datetime

def get_all_recipes():
    session = SessionLocal()
    recipes = session.query(Recipe).all()
    session.close()
    return recipes

def get_bookmarked_recipes():
    query = "SELECT * FROM recipes WHERE bookmarked_at IS NOT NULL"
    with engine.connect() as conn:
        result = conn.execute(query)
        return [dict(row) for row in result]
    
def generate_hash(password):
    password = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password, salt)
    return hashed.decode('utf-8')

def check_hash(password, hashed):
    password = password.encode('utf-8')
    return bcrypt.checkpw(password, hashed.encode('utf-8'))

last_updated_day = None

def is_new_day():
    global last_updated_day
    current_day = datetime.now().date()
    if last_updated_day != current_day:
        last_updated_day = current_day
        return True
    return False



    