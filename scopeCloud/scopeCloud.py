import datetime
from flask import Flask, render_template, request, jsonify
from flask_mongoengine import MongoEngine
from flask_security import Security, MongoEngineUserDatastore, \
    UserMixin, RoleMixin, login_required, current_user, http_auth_required, auth_token_required
import os
import json
from datetime import datetime

# Create app
app = Flask(__name__)
port = int(os.getenv("PORT", 5000))
print "port: %d" % port
app.config['DEBUG'] = True
app.config['SECRET_KEY'] = 'super-secret'
app.config['WTF_CSRF_ENABLED'] = False
app.config['OVERRIDE_FLASK_SCHEME'] = 'https'


# localhost ===============================================================
# MongoDB Config

if 'VCAP_SERVICES' in os.environ:
    services = json.loads(os.getenv('VCAP_SERVICES'))
    mongo_env = services['mongodb'][0]['credentials']
    app.config['MONGODB_SETTINGS'] = {
        'username' : mongo_env['username'],
        'password' : mongo_env['password'],
        'host'     : mongo_env['uri'],
        'db'       : mongo_env['dbname']
    }
    #app.config['MONGODB_DB'] = mongo_env['dbname']
    #app.config['MONGODB_HOST'] = mongo_env['uri']
    #app.config['MONGODB_PORT'] = 27017
    #app.config['MONGODB_USERNAME'] = mongo_env['username']
    #app.config['MONGODB_PASSWORD'] = mongo_env['password']
else:
    app.config['MONGODB_DB'] = 'mydatabase'
    app.config['MONGODB_HOST'] = 'localhost'
    app.config['MONGODB_PORT'] = 27017

app.config['SECURITY_REGISTERABLE'] = True
app.config['SECURITY_SEND_REGISTER_EMAIL'] = False
app.config['SECURITY_PASSWORD_HASH']="bcrypt"
app.config['SECURITY_PASSWORD_SALT']="abc"

# Create database connection object
db = MongoEngine(app)

class Role(db.Document, RoleMixin):
    name = db.StringField(max_length=80, unique=True)
    description = db.StringField(max_length=255)

class User(db.Document, UserMixin):
    email = db.StringField(max_length=255)
    password = db.StringField(max_length=255)
    active = db.BooleanField(default=True)
    confirmed_at = db.DateTimeField()
    roles = db.ListField(db.ReferenceField(Role), default=[])


class Frame(db.Document):
    user_email = db.StringField(max_length=255)
    targetName = db.StringField(max_length=255)
    filterName = db.StringField(max_length=255)
    binningX = db.IntField(min_value=1,max_value=8)
    binningY = db.IntField(min_value=1,max_value=8)
    numOfFrames = db.IntField(min_value=1)
    expTime = db.FloatField(min_value=0.001)
    coord = db.PointField()
    equinox = db.FloatField(min_value=-273.15)
    created = db.DateTimeField()
    download_dir = db.StringField(max_length=255)
    fileName = db.StringField(max_length=255)
    fileExt = db.StringField(max_length=255)
    CCDTemp = db.FloatField(min_value=-273.15)
    CCDCamera = db.StringField(max_length=255)
    focalLength = db.FloatField(min_value=0)
    apertureDia = db.FloatField(min_value=0)
    frameType = db.StringField(max_length=255)

    #index definition
    meta = {
        'indexes' : [
            {
                'fields' : ['user_email', 'coord', 'equinox', 'created', 'apertureDia'],
                'unique' : True 
            }
           ]
        }

# Setup Flask-Security
user_datastore = MongoEngineUserDatastore(db, User, Role)
security = Security(app, user_datastore)


# Views
@app.route('/')
@login_required
def home():
    return render_template('overview.html', Frame=Frame, Now=datetime.utcnow())

@app.route('/allFrames', methods=['GET', 'POST'])
@login_required
def allFrames():
    if request.method == 'POST':
        filterDict = {'user_email': current_user.email}
        for item in request.form.iteritems():
            if item[1]:
                filterDict[item[0]] = item[1]
        objects = Frame.objects(**filterDict)
    else:
        objects = Frame.objects(user_email=current_user.email).order_by('-created')[:20]
        return render_template('allframes.html', objects=objects)

@app.route('/allFramesData', defaults={'date': None}, methods=['GET'])
@app.route('/allFramesData/<date>', methods=['GET'])
@login_required
def allFramesData(date):
    if date == None:
        objects = Frame.objects(user_email=current_user.email).order_by('-created')
    else:
        startDate = datetime.strptime(date,'%Y-%m-%d').replace(hour=0,minute=0,second=0)
        endDate = datetime.strptime(date,'%Y-%m-%d').replace(hour=23,minute=59,second=59)
        objects = Frame.objects(user_email=current_user.email, created__gte=startDate, created__lte=endDate).order_by('created')
    return objects.to_json(), 200

@app.route('/latestFramesData', methods=['GET'])
@login_required
def latestFramesData():
    objects = Frame.objects(user_email=current_user.email).order_by('-created')[:5]
    return objects.to_json(), 200


# apis
# curl -i -H "Content-Type: application/json" -X POST -d '{"targetName":"M31", "filterName":"L", "binning":1, "expTime":10.0, "status":"scheduled"}' http://klaus-Inspiron-1720:5000/api/v1.0/target

@app.route('/api/v1.0/add_frame', methods=['POST'])
@auth_token_required
def add_frame():
   # if not request.json or not 'target' in request.json:
   #     abort(400)
    currentTime = datetime.now()
    coord = [request.json['ra']*15 - 360 if request.json['ra']*15 > 180   else request.json['ra']*15 , request.json['dec']]
    print request.json
    try:
        f = Frame(user_email=current_user.email,targetName=request.json['targetName'],filterName=request.json['filterName'],binningX=request.json['binningX'],binningY=request.json['binningY'],numOfFrames=request.json['numOfFrames'],expTime=request.json['expTime'], created=request.json['dateObs'], download_dir=request.json['download_dir'], fileName=request.json['fileName'],  fileExt=request.json['fileExt'], coord=coord, equinox=request.json['equinox'], CCDTemp=request.json['CCDTemp'], CCDCamera=request.json['CCDCam'], focalLength=request.json['focalLen'], apertureDia=request.json['apertureDia'], frameType=request.json['frameType'] ).save()
        return jsonify({'frame': f}), 201
    except Exception as err:
        return "%s" % err, 409
    except:
        return 500

@app.route('/api/v1.0/add_frame2', methods=['POST'])
@http_auth_required
def add_frame2():
   # if not request.json or not 'target' in request.json:
   #     abort(400)
    currentTime = datetime.now()
    coord = [int(request.form['ra'])*15 - 360 if int(request.form['ra'])*15 > 180   else int(request.form['ra'])*15 , int(request.form['dec'])]
    f = Frame(user_email=current_user.email,targetName=request.form['targetName'],filterName=request.form['filterName'],binningX=request.form['binningX'],binningY=request.form['binningY'],numOfFrames=request.form['numOfFrames'],expTime=request.form['expTime'], created=currentTime, download_dir=request.form['download_dir'], fileName=request.form['fileName'], coord=coord).save()
    return jsonify({'frame': f}), 201


@app.route('/api/v1.0/get_dates', methods=['GET'])
#@auth_token_required
#@http_auth_required
def get_dates():
    # if not request.json or not 'target' in request.json:
    #     abort(400)

    # create aggregation pipeline to aggregate all frames of a day
    p_framesOfDay = [{ '$group':{
                         '_id': {
                                 'year'      : {'$year' : '$created' },
                                 'dayOfYear' : {'$dayOfYear' : '$created'}
                                },
                 'date'       : { '$first' : { '$dateToString': { 'format': '%Y-%m-%d', 'date': '$created' } } },
                 'totalFrames': { '$sum': '$numOfFrames' },
                }}]
    aggResult = list(Frame.objects(user_email=current_user.email).only('created','numOfFrames').order_by('-created').aggregate(*p_framesOfDay))

    # aggregate all frames of a year
    currentYear = None
    framesPerYear = {}
    for item in aggResult:
        if item[u'_id'][u'year'] in framesPerYear:
            framesPerYear[item[u'_id'][u'year']] = framesPerYear[item[u'_id'][u'year']] + item[u'totalFrames']
        else:
            framesPerYear[item[u'_id'][u'year']] = item[u'totalFrames']
        
    data = []
    for item in aggResult:
        
        data.append({'date' : item[u'date'], 'framesOfDay': item[u'totalFrames'], 'framesOfYear' : framesPerYear[item[u'_id'][u'year']]  })
    return jsonify(data), 201



if __name__ == '__main__':
    app.run(host='0.0.0.0',port=port)
