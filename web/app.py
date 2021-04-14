from flask import Flask, jsonify, request
from flask_restful import Api, Resource
from pymongo import MongoClient
import bcrypt
import spacy

app = Flask(__name__)
api = Api(app)
client = MongoClient('mongodb://db:27017')#here we are connected with client
db = client.SimilarityDB#create a new DB
users = db["Users"]#create a new collection of users

def UserExist(username):
    '''Check if user exists
    :param username:
    :return: True or False
    '''
    if users.find({"Username":username}).count() == 0:#count - mongo function which works similar as python module
        return False
    else:
        return True

def verifyPw(username, password):
    if not UserExist(username):
        return False

    hashed_pw = users.find({
        "Username":username
    })[0]["Password"]

    if bcrypt.hashpw(password.encode('utf8'),hashed_pw) == hashed_pw:
        return True
    else:
        return False


def countTokens(username):
    tokens_num = users.find({
        "Username":username
    })[0]["Tokens"]
    return tokens_num

class Register(Resource):# inherit from Resource class
    def post(self):
        postedData = request.get_json()#get the posted

        username = postedData["username"]
        password = postedData["password"]

        #check if username isnt exists already
        if UserExist(username):#consider using assert
            retJson = {
                "status":301,
                "message":"Invalid Username"
            }
            return jsonify(retJson)

        hashed_pw = bcrypt.hashpw(password.encode('utf8'), bcrypt.gensalt())

        users.insert({
            "Username": username,
            "Password": hashed_pw,
            "Tokens": 6
        })

        retJson = {
            "status":200,
            "msg":"You've successfully signed up to the API"
        }
        return jsonify(retJson)

class Detect(Resource):
    def post(self):
        postedData = request.get_json()

        username = postedData["username"]
        password = postedData["password"]
        text1 = postedData["text1"]
        text2 = postedData["text2"]

        if not UserExist(username):
            retJson = {
                "status":301,
                "message":"Invalid Username"
            }
            return jsonify(retJson)

        correct_pw = verifyPw(username, password)

        if not correct_pw:
            retJson = {
                "status": 302,
                "msg":"Invalid Password"
            }
            return jsonify(retJson)

        num_tokens = countTokens(username)

        if num_tokens <=0:
            retJson = {
                "status":303,
                "msg": "You are out of tokens, please refill."
            }
            return jsonify(retJson)

        print("Calculating the similarity..")

        nlp = spacy.load('en_core_web_sm-2.0.0')

        text1 = nlp(text1)
        text2 = nlp(text2)

        #ratio of text similarity <0,1>; close to 1 - similar, close to 0 - different
        ratio = text1.similarity(text2)

        retJson = {
            "status": 200,
            "similarity:": ratio,
            "msg": "Similarity score calculated successfully"
        }

        current_tokens = countTokens(username)
        users.update({
            "Username":username
        },{
            "$set":{
                "Tokens":current_tokens-1
            }
        })

        return jsonify(retJson)

class Refill(Resource):
    def post(self):
        postedData = request.get_json()

        username = postedData["username"]
        password = postedData["admin_pw"]
        refill_amount = postedData["refill"]

        if not UserExist(username):
            retJson = {
                "status":301,
                "message":"Invalid Username"
            }
            return jsonify(retJson)

        correct_pw = "sample123" #remember to avoid storing passwords in app. Use instead hashed password

        if not password == correct_pw:
            retJson = {
                "status":304,
                "msg":"Invalid admin password"
            }
            return jsonify(retJson)

        current_tokens = countTokens(username)
        users.update({
            "username":username
        },{
            "$set":{
                "Tokens":current_tokens + refill_amount
            }
        })

        retJson = {
            "status":200,
            "msg":"Refill succeed"
        }
        return jsonify(retJson)


api.add_resource(Register, '/register')
api.add_resource(Detect, '/detect')
api.add_resource(Refill, '/refill')

if __name__ == "__main__":
    app.run(host = '0.0.0.0')