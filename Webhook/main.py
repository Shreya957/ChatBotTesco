from os import getenv

from psycopg2 import OperationalError
from psycopg2.pool import SimpleConnectionPool

from flask import jsonify, json, request
import googleapiclient.discovery
from google.oauth2 import service_account
import os
import re


CONNECTION_NAME = getenv(
  'INSTANCE_CONNECTION_NAME',
  'tescoclubcard:us-central1:*****')
DB_USER = getenv('POSTGRES_USER', 'postgres')
DB_PASSWORD = getenv('POSTGRES_PASSWORD', '***')
DB_NAME = getenv('POSTGRES_DATABASE', 'tesco_clubcard')

pg_config = {
  'user': DB_USER,
  'password': DB_PASSWORD,
  'dbname': DB_NAME
}

# Connection pools reuse connections between invocations,
# and handle dropped or expired connections automatically.
pg_pool = None


#function to retreive google credential
def get_credentials():
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    GOOGLE_PRIVATE_KEY = "<Your private key>"
    GOOGLE_PRIVATE_KEY = GOOGLE_PRIVATE_KEY.replace('\\n', '\n')
    
    account_info = {
        "private_key": GOOGLE_PRIVATE_KEY,
        "client_email": "<Service_account>",
        "token_uri": "https://oauth2.googleapis.com/token",
    }    
    credentials = service_account.Credentials.from_service_account_info(account_info, scopes=scopes)
    return credentials

def get_service(service_name='sheets', api_version='v4'):
    credentials = get_credentials()
    service = googleapiclient.discovery.build(service_name, api_version, credentials=credentials)
    return service

# function for responses
def results():
#   build a request object
    req = request.get_json(force=True)

    # fetch action from json
    action = req.get('queryResult').get('action')
    intent = req.get('queryResult').get('intent').get('displayName')
    
#   result = service.spreadsheets().values().get(spreadsheetId=spreadsheet_id, range=range_name).execute()
#    values = get_spreadsheet(intent)  
#    return {'fulfillmentText': str(values[0]).replace("[","").replace("]","").replace("'","")}
#    return {'fulfillmentText': values}

# reteive the club points from account number
    if intent == 'Retrive_Club_Points - custom':
        values = postgres_get(request)
        r_value = 'Currently you have ' + values.replace("(","").replace(")","").replace(",","") + ' clubpoints.'
        if values.replace("(","").replace(")","").replace(",","") == 'None':
            return {'fulfillmentText': 'Seems Like , this account number does not exit! .. Please try again.'}            
        else:
            return {'fulfillmentText': r_value}
    if intent == 'Change_customer_info - custom':
        values = postgres_update(request)
        if values == 'None':
            return {'fulfillmentText': 'This acccount details do not match with any record. Please try again.'}
        else:
            return {'fulfillmentText': 'Your details have been verified. Please provide the phone number which needs to be updated.'}
        
    if intent == 'Change_customer_info - custom - custom':
        values = postgres_contact(request)
        return {'fulfillmentText': values }
    
    if intent == 'Clubcard_function' or intent == 'Customer_Care' or intent == 'Clubcard_value' or intent == 'Clubcard_expiry':
        values = get_spreadsheet(intent)
        return {'fulfillmentText': values } #str(values[0])}.replace("[","").replace("]","").replace("'","")}
    else:
        return {'fulfillmentText': ""}
        

#get the details from spreadsheet
def get_spreadsheet(intent):
    service = get_service()
    spreadsheet_id = "<spreadsheet_id>"
    if intent == 'Clubcard_function':
        range_name = "FAQ's!E2"
    elif intent == 'Customer_Care':
        range_name = "FAQ's!E7"
    elif intent == 'Clubcard_value':
        range_name = "FAQ's!E12"
    elif intent == 'Clubcard_expiry':
        range_name = "FAQ's!E17"
    else:
        range_name = ""

    result = service.spreadsheets().values().get(spreadsheetId=spreadsheet_id, range=range_name).execute()
    values = result.get('values')
    return values


def __connect(host):
    """
    Helper function to connect to Postgres
    """
    global pg_pool
    pg_config['host'] = host
    pg_pool = SimpleConnectionPool(1, 1, **pg_config)

#query the club point
def postgres_get(request):
    global pg_pool
    req = request.get_json(force=True)
    # Initialize the pool lazily, in case SQL access isn't needed for this
    # GCF instance. Doing so minimizes the number of active SQL connections,
    # which helps keep your GCF instances under SQL connection limits.
    if not pg_pool:
        try:
            __connect(f'/cloudsql/{CONNECTION_NAME}')
        except OperationalError:
            # If production settings fail, use local development ones
            __connect('localhost')

    # Remember to close SQL resources declared while running this function.
    # Keep any declared in global scope (e.g. pg_pool) for later reuse.
    try:
        with pg_pool.getconn() as conn:
            cursor = conn.cursor()
            account_number = req.get('queryResult').get('parameters').get('number')
            query_clubpoints = 'select clup_points from tesco_clubcard where acc_number= %s'
            cursor.execute(query_clubpoints, (account_number,))
            results = cursor.fetchone()
            pg_pool.putconn(conn)
            return str(results)
        
    except (Exception, psycopg2.DatabaseError) as error :
        conn.rollback()
        return error
    
#validate account number and DOB
def postgres_update(request):
    global pg_pool
    req = request.get_json(force=True)
    # Initialize the pool lazily, in case SQL access isn't needed for this
    # GCF instance. Doing so minimizes the number of active SQL connections,
    # which helps keep your GCF instances under SQL connection limits.
    if not pg_pool:
        try:
            __connect(f'/cloudsql/{CONNECTION_NAME}')
        except OperationalError:
            # If production settings fail, use local development ones
            __connect('localhost')

    # Remember to close SQL resources declared while running this function.
    # Keep any declared in global scope (e.g. pg_pool) for later reuse.
    try:
        with pg_pool.getconn() as conn:
            cursor = conn.cursor()
            account_number = req.get('queryResult').get('parameters').get('number')
            dob = req.get('queryResult').get('parameters').get('date')
            query_clubpoints = 'select * from tesco_clubcard where acc_number= %s and dob= %s'
            cursor.execute(query_clubpoints,(account_number,dob))
            results = cursor.fetchone()
            pg_pool.putconn(conn)
            return str(results)

    except (Exception, psycopg2.DatabaseError) as error :
        conn.rollback()
        return error

        
#update phone number
def postgres_contact(request):
    global pg_pool
    req = request.get_json(force=True)
    # Initialize the pool lazily, in case SQL access isn't needed for this
    # GCF instance. Doing so minimizes the number of active SQL connections,
    # which helps keep your GCF instances under SQL connection limits.
    if not pg_pool:
        try:
            __connect(f'/cloudsql/{CONNECTION_NAME}')
        except OperationalError:
            # If production settings fail, use local development ones
            __connect('localhost')

    # Remember to close SQL resources declared while running this function.
    # Keep any declared in global scope (e.g. pg_pool) for later reuse.
    try:
    	with pg_pool.getconn() as conn:
        	cursor = conn.cursor()
        	account_number = req.get('queryResult').get('outputContexts')[0].get('parameters').get('number')
       		dob = req.get('queryResult').get('outputContexts')[0].get('parameters').get('date')
        	phone_number = req.get('queryResult').get('parameters').get('phone-number')
        	query_clubpoints = 'UPDATE tesco_clubcard set phone_num = %s where acc_number= %s and dob= %s'
        	cursor.execute(query_clubpoints,(phone_number,account_number,dob))
        	conn.commit()
        	pg_pool.putconn(conn)
        	return 'Phone number has been updated'
    except (Exception, psycopg2.DatabaseError) as error :
        conn.rollback()
        return error

    
# create a route for webhook
def webhook(self):
    # return response
    return jsonify(results())
