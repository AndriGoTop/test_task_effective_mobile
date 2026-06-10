import os
import secrets
from dotenv import load_dotenv, dotenv_values, set_key

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_PATH = os.path.join(BASE_DIR, '.env')
if os.path.exists(ENV_PATH):
    load_dotenv(ENV_PATH)

if 'SECRET_KEY' not in dotenv_values(ENV_PATH).keys():
    set_key(ENV_PATH, 'SECRET_KEY', secrets.token_hex(32))

DB_PARAMETERS = {
    'user': os.getenv('POSTGRES_USER', 'postgres'),
    'password': os.getenv('POSTGRES_PASSWORD', 'password'),
    'host': os.getenv('POSTGRES_HOST', 'localhost'),
    'port': os.getenv('POSTGRES_PORT', '5432'),
    'db_name': os.getenv('POSTGRES_DB', 'auth_em'),
}

DB_PATH = f"postgresql://{DB_PARAMETERS['user']}:{DB_PARAMETERS['password']}@{DB_PARAMETERS['host']}:{DB_PARAMETERS['port']}/{DB_PARAMETERS['db_name']}"


