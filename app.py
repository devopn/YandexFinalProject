from flask import Flask, request, jsonify
import os
from sqlalchemy import exc
import re
from data import db_session
from data.friends import Friends
from data.posts import Post
from data.users import User
from auth.register_manager import RegisterManager
from errors import *
from werkzeug.security import check_password_hash
import psycopg2
from sqlalchemy import desc
import datetime
import jwt
import uuid
app = Flask(__name__)
env = os.environ
JWT_TOKEN_TIME = datetime.timedelta(hours=24)



db_session.global_init()
sess = db_session.create_session()
sess.no_autoflush = False
rm = RegisterManager(sess)


def get_token_auth_header():
    auth = request.headers.get("Authorization", None)
    if not auth:
        raise AuthError("Authorization header is expected", 401)

    parts = auth.split()

    if parts[0].lower() != "bearer":
        raise AuthError("Authorization header must start with Bearer", 401)
    elif len(parts) == 1:
        raise AuthError("Token not found", 401)
    elif len(parts) > 2:
        raise AuthError("Invalid Authorization header", 401)
    token = parts[1]
    return token


def authorize():
    token = get_token_auth_header()
    try:
        payload = jwt.decode(token, os.environ["RANDOM_SECRET"], algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        raise AuthError("Token expired", 401)
    except jwt.InvalidTokenError:
        raise AuthError("Invalid token", 401)

    login, password = payload["sub"].split("~")  # login~hashed_password[64:]

    user: User = sess.query(User).filter(User.login == login).first()
    if not user:
        raise AuthError("Auth user not found", 401)
    if user.password[64:] != password:
        raise AuthError("Token exspired", 401)
    return user


def generate_jwt(user: User):
    payload = {
        "exp": datetime.datetime.utcnow() + JWT_TOKEN_TIME,
        "iat": datetime.datetime.utcnow(),
        "sub": f"{user.login}~{user.password[64:]}",
    }
    return jwt.encode(payload, os.environ["RANDOM_SECRET"], algorithm="HS256")


def get_sign_in_token(data: dict):
    login, password = data.get("login", None), data.get("password", None)
    if not login or not password:
        raise AuthError("No credentials", 401)

    user: User = sess.query(User).filter(User.login == login).first()
    if not user:
        raise AuthError("Incorrect login or password", 401)
    
    if not check_password_hash(user.password, password):
        raise AuthError("Incorrect login or password", 401)

    return generate_jwt(user)


def check_access(user1: User, user2: User):  # user1 can see user2
    if user2.isPublic:
        return True
    if user1.login == user2.login:
        return True
    if user1.login in [
        friend.user2
        for friend in sess.query(Friends).filter(Friends.user1 == user2.login).all()
    ]:
        return True  # If user1 is a friend of user2
    return False


def row2dict(row):
    d = {}
    for column in row.__table__.columns:
        d[column.name] = str(getattr(row, column.name))
    return d


@app.route("/api/ping", methods=["GET"])
def send():
    return jsonify({"status": "ok"}), 200

@app.route("/api/auth/register", methods=["POST"])
def register():
    data = request.json
    user = rm.register(data)
    return jsonify({"profile": user.get_profile()}), 201


@app.route("/api/auth/sign-in", methods=["POST"])
def sign_in():
    data = request.json
    token = get_sign_in_token(data)
    return jsonify({"token": token}), 200


@app.route("/api/me/profile", methods=["GET"])
def get_user_by_token():
    profile = authorize()
    return jsonify(profile.get_profile()), 200


@app.route("/api/me/profile", methods=["PATCH"])
def edit_profile():

    user = authorize()
    data = request.json
    rm.validate_data(data, user)
    user.update_profile(data)
    sess.commit()
    return jsonify(user.get_profile()), 200
 

@app.route("/api/me/profiles/<login>", methods=["GET"])
def get_user_by_token_by_login(login):

    user = authorize()
    profile = sess.query(User).filter(User.login == login).first()

    if not profile:
        return jsonify({"reason": "User not found "}), 404

    if check_access(user, profile):
        return jsonify(profile.get_profile()), 200
    else:
        return jsonify({"reason": "You dont have access"}), 403


@app.route("/api/me/updatePassword", methods=["POST"])
def update_password():

    user = authorize()
    data: dict = request.json

    old_password = data.get("oldPassword", None)
    new_password = data.get("newPassword", None)

    if user.update_password(old_password, new_password):
        sess.commit()
        return jsonify({"status": "ok"}), 200
    else:
        return jsonify({"reason": "Password does not changed"}), 400  # if error


@app.route("/api/friends/add", methods=["POST"])
def add_friend():

    user = authorize()
    data: dict = request.json

    friend = sess.query(User).filter(User.login == data.get("login", None)).first()
    if not friend:
        return jsonify({"reason": "User not found"}), 404
    if friend.isPublic == False:
        return jsonify({"reason": "User is not public"}), 403
    if friend and friend.login != user.login:
        user1 = user.login
        user2 = friend.login
        # print(user1, user2)

        if (
            sess.query(Friends)
            .filter(Friends.user1 == user1, Friends.user2 == user2)
            .first()
        ):
            return jsonify({"status": "ok"}), 200
        else:
            friends = Friends(user1=user1, user2=user2)
            sess.add(friends)
            sess.commit()
            return jsonify({"status": "ok"}), 200

    else:  # if user == friend
        return jsonify({"reason": "You cant add yourself"}), 400


@app.route("/api/friends/remove", methods=["POST"])
def remove_friend():

    user = authorize()
    data: dict = request.json

    friend = sess.query(User).filter(User.login == data.get("login", None)).first()
    if friend and friend.login != user.login:
        user1 = user.login
        user2 = friend.login
        a = (
            sess.query(Friends)
            .filter(Friends.user1 == user1, Friends.user2 == user2)
            .first()
        )
        if a:
            sess.delete(a)
            sess.commit()
        return jsonify({"status": "ok"}), 200

    else:
        return jsonify({"reason": "User not found"}), 404


@app.route("/api/friends", methods=["GET"])
def list_friends():
    user = authorize()
    offset = int(request.args.get("offset", 0))
    limit = int(request.args.get("limit", 5))

    if offset < 0 or limit < 0:
        return jsonify({"reason": "Invalid parameters"}), 400

    friends = (
        sess.query(Friends)
        .filter(Friends.user1 == user.login)
        .order_by(Friends.createdAt.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return (
        jsonify(
            [{"login": friend.user2, "addedAt": friend.createdAt.isoformat()} for friend in friends]
        ),
        200,
    )


@app.route("/api/posts/new", methods=["POST"])
def create_post():

    user = authorize()
    data: dict = request.json

    content = data.get("content", "")
    tags = data.get("tags", [])

    post = Post()
    post.id = str(uuid.uuid4())
    post.content = str(content)
    post.author = user.login
    if isinstance(tags, list):
        post.tags = [str(tag) for tag in tags]
    else:
        return jsonify({"reason": "Invalid tags. Tags must be an array"}), 400
    sess.add(post)
    sess.commit()

    return jsonify(post.get_post()), 200


@app.route("/api/posts/<postId>", methods=["GET"])
def get_post_by_id(postId):

    user = authorize()
    post = sess.query(Post).filter(Post.id == postId).first()

    if not post:
        return jsonify({"reason": "Post not found"}), 404

    owner = sess.query(User).filter(User.login == post.author).first()

    if check_access(user, owner) == False:
        return jsonify({"reason": "You dont have access"}), 403
    else:
        return jsonify(post.get_post()), 200


@app.route("/api/posts/feed/<pre_login>", methods=["GET"])
def get_post_by_login(pre_login):

    user = authorize()
    if pre_login == "my":
        login = user.login
    else:
        login = pre_login
        profile = sess.query(User).filter(User.login == login).first()

        if not profile:
            return jsonify({"reason": "Profile not found"}), 404

        if not check_access(user, profile):
            return jsonify({"reason": "You dont have access"}), 403
    try:
        offset = int(request.args.get("offset", 0))
        limit = int(request.args.get("limit", 5))
    except ValueError:
        return jsonify({"reason": "Invalid parameters"}), 400
    if offset < 0 or limit < 0:
        return jsonify({"reason": "Invalid parameters"}), 400
    posts = (
        sess.query(Post)
        .filter(Post.author == login)
        .order_by(Post.createdAt.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return jsonify([post.get_post() if post else None for post in posts]), 200


@app.route("/api/posts/<postId>/like", methods=["POST"])
def like_post_by_id(postId):

    user = authorize()
    post = sess.query(Post).filter(Post.id == postId).first()

    if not post:
        return jsonify({"reason": "Post not found"}), 404
    owner = sess.query(User).filter(User.login == post.author).first()
    if user.login in post.likersLogins:
        return jsonify(post.get_post()), 200
    else:
        if not check_access(user, owner):
            return jsonify({"reason": "You dont have access"}), 403

        if user.login in post.dislikersLogins:
            dis_res = list(post.dislikersLogins)
            dis_res.remove(user.login)
            post.dislikersLogins = dis_res
            post.dislikesCount -= 1

        like_res = list(post.likersLogins)
        like_res.append(user.login)
        post.likersLogins = like_res
        post.likesCount += 1
        sess.commit()
        return jsonify(post.get_post()), 200


@app.route("/api/posts/<postId>/dislike", methods=["POST"])
def dislike_post_by_id(postId):

    user = authorize()
    post = sess.query(Post).filter(Post.id == postId).first()

    if not post:
        return jsonify({"reason": "Post not found"}), 404

    owner = sess.query(User).filter(User.login == post.author).first()

    if user.login in post.dislikersLogins:
        return jsonify(post.get_post()), 200
    else:
        if not check_access(user, owner):
            return jsonify({"reason": "You dont have access"}), 403
        if user.login in post.likersLogins:
            like_res = list(post.likersLogins)
            like_res.remove(user.login)
            post.likersLogins = like_res
            post.likesCount -= 1

        dislike_res = list(post.dislikersLogins)
        dislike_res.append(user.login)
        post.dislikersLogins = dislike_res
        post.dislikesCount += 1
        sess.commit()
        return jsonify(post.get_post()), 200


# Error handlers
@app.errorhandler(AuthError)
def handle_auth_error(error: AuthError):
    return jsonify({"reason": error.error}), error.status_code


@app.errorhandler(PasswordError)
def handle_password_error(error: PasswordError):
    return jsonify({"reason": error.error}), error.status_code


@app.errorhandler(RegisterError)
def handle_register_error(error: RegisterError):
    return jsonify({"reason": error.error}), error.status_code


@app.errorhandler(psycopg2.errors.UniqueViolation)  # just in case
def handle_unique_violation(error):
    return jsonify({"reason": "userdata already used"}), 409


@app.errorhandler(exc.InvalidRequestError)
def handle_invalid_request_error(error):
    sess.rollback()
    return jsonify({"reason": "Invalid request"}), 400


@app.errorhandler(415)
def handle_415(error):
    return jsonify({"reason": "Unsupported media type"}), 415


@app.errorhandler(400)
def handle_400(error):
    return jsonify({"reason": "Bad request"}), 400

@app.errorhandler(500)
def handle(error):
    return jsonify({"reason": "Ooops... Something went wrong, sorry!"}), 500


if __name__ == "__main__":
    host, port = env["SERVER_ADDRESS"].split(":")
    app.run(host=host, port=port)
