import os
from os.path import realpath, dirname
from flask_restful import Resource, reqparse
from . import api
from expr import expr_manager
from database.models import Announcement, Hackathon, Register, Template
from user.login import *
from flask import g, request
from log import log
from database import db_adapter
from decorators import token_required
from user.user_functions import get_user_experiment, get_user_hackathon
from health import report_health
from remote.guacamole import GuacamoleInfo


class RegisterListResource(Resource):
    # =======================================================return data start
    # [{"register_name":"zhang", "online":"1","submitted":"0"..."description":" "}]
    # =======================================================return data end
    @token_required
    def get(self):
        json_ret = map(lambda u: u.json(), user_manager.get_all_registration())
        return json_ret


class UserExperimentResource(Resource):
    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument('id', type=int, location='args')
        args = parser.parse_args()
        if args['id'] is None:
            return json.dumps({"error": "Bad request"}), 400
        cs = expr_manager.get_expr_status(args['id'])
        if cs is not None:
            return cs
        else:
            return "Not Found", 404

    @token_required
    def post(self):
        args = request.get_json()
        if "cid" not in args or "hackathon" not in args:
            return "invalid parameter", 400
        cid = args["cid"]
        hackathon = args["hackathon"]
        try:
            return expr_manager.start_expr(hackathon, cid)
        except Exception as err:
            log.error(err)
            return "fail to start due to '%s'" % err, 500

    @token_required
    def delete(self):
        parser = reqparse.RequestParser()
        parser.add_argument('id', type=int, location='args')
        args = parser.parse_args()
        if args['id'] is None:
            return {"error": "Bad request"}, 400

        return expr_manager.stop_expr(args["id"])

    @token_required
    def put(self):
        args = request.get_json()
        if args['id'] is None:
            return json.dumps({"error": "Bad request"}), 400
        return expr_manager.heart_beat(args["id"])


class BulletinResource(Resource):
    def get(self):
        return db_adapter.find_first_object(Announcement, enabled=1).json()

    # todo bulletin post
    @token_required
    def post(self):
        pass


class LoginResource(Resource):
    def post(self):
        body = request.get_json()
        provider = body["provider"]
        return login_providers[provider].login(body)

    @token_required
    def delete(self):
        return login_providers.values()[0].logout(g.user)


class HealthResource(Resource):
    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument('q', type=str, location='args')
        args = parser.parse_args()
        return report_health(args['q'])


class HackathonResource(Resource):
    # hid is hackathon id
    @token_required
    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument('hid', type=int, location='args')
        args = parser.parse_args()
        if args['hid'] is None:
            return {"error": "Bad request"}, 400
        return db_adapter.find_first_object(Hackathon, id=args['hid']).json()

    # todo post
    @token_required
    def post(self):
        pass


class HackathonListResource(Resource):
    def get(self):
        parse = reqparse.RequestParser()
        parse.add_argument('name',type=str, location='args')
        args = parse.parse_args()
        if args['name'] is not None:
            return db_adapter.find_first_object(Hackathon, name=args['name']).json()
        return map(lambda u: u.json(), db_adapter.find_all_objects(Hackathon))

class HackathonStatResource(Resource):
    # hid is hackathon id
    def get(self):
        parse = reqparse.RequestParser()
        parse.add_argument('hid', type=int, location='args')
        args = parse.parse_args()
        if args['hid'] is None:
            return {"error": "Bad request"}, 400
        total_num = db_adapter.count(Register, id=args['hid'])
        enabled_num = db_adapter.count(Register, id=args['hid'], enabled=1)
        disabled_num = db_adapter.count(Register, id=args['hid'], enabled=0)
        return {'hid': args['hid'], 'total': total_num, 'online': enabled_num, 'offline': disabled_num}


class UserHackathonResource(Resource):
    # uid is user id
    @token_required
    def get(self):
        parse = reqparse.RequestParser()
        parse.add_argument('uid', type=int, location='args')
        args = parse.parse_args()
        if args['uid'] is None:
            return {"error": "Bad request"}, 400
        return get_user_hackathon(args['uid'])

    # todo user hackathon post
    @token_required
    def post(self):
        pass

    # todo delete user hackathon
    @token_required
    def delete(self):
        pass


class HackathonTemplateResource(Resource):
    # hid is hackathon id
    def get(self):
        parse = reqparse.RequestParser()
        parse.add_argument('hid', type=int, location='args')
        args = parse.parse_args()
        if args['hid'] is None:
            return {"error": "Bad request"}, 400
        return map(lambda u: u.json(), db_adapter.find_all_objects(Template, hackathon_id=args['hid']))


class UserExperimentListResource(Resource):
    # uid is user id
    @token_required
    def get(self):
        parse = reqparse.RequestParser()
        parse.add_argument('uid', type=int, location='args')
        args = parse.parse_args()
        if args['uid'] is None:
            return {"error": "Bad request"}, 400
        return get_user_experiment(args['uid'])


class GuacamoleResource(Resource):
    @token_required
    def get(self):
        return GuacamoleInfo().getConnectInfo()


class UserResource(Resource):
    def get(self):
        parse = reqparse.RequestParser()
        parse.add_argument('uid', type=int, location='args')
        args = parse.parse_args()
        if args['uid'] is None:
            return {"error": "Bad request"}, 400
        return user_manager.get_user_by_id(args['uid'])


api.add_resource(UserExperimentResource, "/api/user/experiment")
api.add_resource(RegisterListResource, "/api/register/list")
api.add_resource(BulletinResource, "/api/bulletin")
api.add_resource(LoginResource, "/api/user/login")
api.add_resource(HackathonResource, "/api/hackathon")
api.add_resource(HackathonListResource, "/api/hackathon/list")
api.add_resource(HackathonTemplateResource, "/api/hackathon/template")
api.add_resource(HackathonStatResource, "/api/hackathon/stat")
api.add_resource(HealthResource, "/", "/health")
api.add_resource(UserHackathonResource, "/api/user/hackathon")
api.add_resource(UserExperimentListResource, "/api/user/experiment/list")
api.add_resource(GuacamoleResource, "/api/guacamoleconfig")
api.add_resource(UserResource, "/api/user")
