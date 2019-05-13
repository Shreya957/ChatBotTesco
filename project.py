from flask import Flask, render_template
from flask import request, redirect, jsonify, url_for, flash


# import CRUD Operations from Lesson 1
from databaseSetup import Base, Category, Item, User
from sqlalchemy import create_engine
from sqlalchemy import Table
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker

from flask import session as login_session
import random
import string
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests


app = Flask(__name__)

CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Item Catalog"


# Create session and connect to DB
engine = create_engine('sqlite:///CatalogApplication.db?\
check_same_thread=False')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()


@app.route('/')
@app.route('/catalog')
def TheCatalogApp():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    categories = session.query(Category).all()
    items = session.query(Item).all()
    return render_template('categories3.html',
                           categories=categories, items=items, STATE=state)


# @app.route('/login')
# def showLogin():
#    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
#                    for x in xrange(32))
#    login_session['state'] = state
#    categories = session.query(Category).all()
#    items = session.query(Item).all()
#    return render_template('login.html', categories=categories,
#                        items = items, STATE = state)


@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data
    # print request.data
    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'

        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    # print access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])

    # If there was an error in the access token info, abort.
    print result
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    print stored_access_token
    print login_session.get('access_token')
    print stored_gplus_id
    print gplus_id
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user is already \
                                 Logged in.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    # check user present
    user_id = getUserID(data["email"])

    if user_id is None:
        user_id = createUser(login_session)

    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px; \
               -webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("Welcome %s" % login_session.get('username'))
    print "done!"
    return output


@app.route('/gdisconnect')
def gdisconnect():
    access_token = login_session.get('access_token')
    if access_token is None:
        print 'Access Token is None'
        response = make_response(json.dumps('Current user not connected.'),
                                 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    print 'In gdisconnect access token is %s', access_token
    print 'User name is: '
    print login_session['username']
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    print 'result is '
    print result
    if result['status'] == '200':
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        print response
        return redirect('/catalog')
    else:
        response = make_response(json.dumps('Failed to revoke token for \
                                 given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


@app.route('/catalog/JSON')
def catalogJSON():
    categorieslist = session.query(Category).all()
    return jsonify(CategoriesList=[r.serialize for r in categorieslist])


@app.route('/catalog/<int:categories_id>/JSON')
def categoryJSON(categories_id):
    categories = session.query(Category).filter_by(id=categories_id).one()
    items = session.query(Item).filter_by(cat_id=categories.id)
    return jsonify(CategoryItem=[i.serialize for i in items])


@app.route('/catalog/<int:categories_id>/<int:items_id>/JSON')
def itemJSON(categories_id, items_id):
    categories = session.query(Category).filter_by(id=categories_id).one()
    items = session.query(Item).filter_by(id=items_id).one()
    return jsonify(ItemDetails=[items.serialize])


def createUser(login_session):
    newUser = User(name=login_session['username'], email=login_session[
                   'email'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user


def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None


@app.route('/catalog/new', methods=['GET', 'POST'])
def AddNewItem():
    if login_session.get('username') is not None:
        if request.method == 'POST':
            print login_session.get('user_id')
            conn = engine.connect()
            select_cat_id = select([Category]).\
                where(Category.name == request.form['Category'])
            res = conn.execute(select_cat_id)
            for category_id in res:
                newItem = Item(name=request.form['itemname'],
                               description=request.form['description'],
                               cat_id=category_id.id,
                               user_id=login_session.get('user_id'))
                session.add(newItem)
                session.commit()
            conn.close()
            categories = session.query(Category).all()
            items = session.query(Item).\
                order_by(Item.creation_date.desc()).all()
            flash("New Item has been Added")
            return redirect('/catalog')
        else:
            categories = session.query(Category).all()
            return render_template('CreateNewItem.html', categories=categories)
    else:
        return redirect('/catalog')


@app.route('/catalog/<int:category_id>/ItemsList', methods=['GET', 'POST'])
def ListItems(category_id):
        if request.method == 'GET':
            categories = session.query(Category).all()
            items = session.query(Item).filter_by(cat_id=category_id)
            return render_template('categories3.html',
                                   categories=categories, items=items)

        else:
            return redirect('/catalog')


@app.route('/catalog/<int:item_id>/ItemDetails', methods=['GET', 'POST'])
def ItemDetails(item_id):
    if request.method == 'GET':
        items = session.query(Item).filter_by(id=item_id)
        return render_template('ItemDetails.html', items=items)
    else:
        return redirect('/catalog')


@app.route('/catalog/<int:item_id>/DeleteItem', methods=['GET', 'POST'])
def DeleteItem(item_id):
        items = session.query(Item).filter_by(id=item_id).one()
        print items.user_id
        print login_session.get('user_id')
        if request.method == 'GET':
            if items.user_id == login_session.get('user_id'):
                session.delete(items)
                session.commit()
                flash("Item has been deleted")
                return redirect('/catalog/%d/ItemsList' % items.cat_id)
            else:
                flash("You are unauthorised to Delete the Item!!")
                return redirect('/catalog')
        else:
            return "Its a POST"


@app.route('/catalog/<int:item_id>/UpdateItem', methods=['GET', 'POST'])
def UpdateItem(item_id):
    items = session.query(Item).filter_by(id=item_id).one()
    categories = session.query(Category).all()
    category_name = session.query(Category).filter_by(id=items.cat_id)

    if request.method == 'GET':
        return render_template('UpdateItem.html', items=items,
                               categories=categories,
                               category_name=category_name)
    else:
        if items.user_id == login_session.get('user_id'):
            categories = session.query(Category).\
                     filter_by(name=request.form['Category']).one()
            items = session.query(Item).filter_by(id=item_id).one()
            items.name = request.form['itemname']
            items.description = request.form['description']
            items.cat_id = categories.id
            session.add(items)
            session.commit()
            flash("An Item has been Updated")
            return redirect('/catalog/%d/ItemsList' % categories.id)

        else:
            flash("You are unauthorised to Update the Item!!")
            return redirect('/catalog')


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
