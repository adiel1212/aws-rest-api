import os
import secrets
import time
import uuid

import boto3
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_PORT = os.environ.get("DB_PORT", "3306")
DB_NAME = os.environ.get("DB_NAME", "sicei")
DB_USER = os.environ.get("DB_USER", "admin")
DB_PASS = os.environ.get("DB_PASS", "password")

app.config["SQLALCHEMY_DATABASE_URI"] = (
    f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

AWS_REGION     = os.environ.get("AWS_REGION", "us-east-1")
S3_BUCKET      = os.environ.get("S3_BUCKET", "mi-bucket-sicei")
SNS_TOPIC_ARN  = os.environ.get("SNS_TOPIC_ARN", "")
DYNAMODB_TABLE = os.environ.get("DYNAMODB_TABLE", "sesiones-alumnos")

class Alumno(db.Model):
    __tablename__ = "alumnos"
    id            = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nombres       = db.Column(db.String(100), nullable=False)
    apellidos     = db.Column(db.String(100), nullable=False)
    matricula     = db.Column(db.String(50),  nullable=False)
    promedio      = db.Column(db.Float,        nullable=False)
    fotoPerfilUrl = db.Column(db.String(500),  nullable=True)
    password      = db.Column(db.String(200),  nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "nombres": self.nombres,
            "apellidos": self.apellidos,
            "matricula": self.matricula,
            "promedio": self.promedio,
            "fotoPerfilUrl": self.fotoPerfilUrl,
            "password": self.password,
        }

class Profesor(db.Model):
    __tablename__ = "profesores"
    id             = db.Column(db.Integer, primary_key=True, autoincrement=True)
    numeroEmpleado = db.Column(db.String(50),  nullable=False)
    nombres        = db.Column(db.String(100), nullable=False)
    apellidos      = db.Column(db.String(100), nullable=False)
    horasClase     = db.Column(db.Integer,     nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "numeroEmpleado": self.numeroEmpleado,
            "nombres": self.nombres,
            "apellidos": self.apellidos,
            "horasClase": self.horasClase,
        }

with app.app_context():
    db.create_all()

def validar_alumno(data):
    errores = []
    if not data.get("nombres") or not isinstance(data["nombres"], str) or data["nombres"].strip() == "":
        errores.append("nombres es requerido y debe ser texto")
    if not data.get("apellidos") or not isinstance(data["apellidos"], str) or data["apellidos"].strip() == "":
        errores.append("apellidos es requerido y debe ser texto")
    if not data.get("matricula") or not isinstance(data["matricula"], str) or data["matricula"].strip() == "":
        errores.append("matricula es requerida y debe ser texto")
    if "promedio" not in data:
        errores.append("promedio es requerido")
    else:
        try:
            p = float(data["promedio"])
            if p < 0 or p > 10:
                errores.append("promedio debe estar entre 0 y 10")
        except (ValueError, TypeError):
            errores.append("promedio debe ser un número")
    return errores

def validar_profesor(data):
    errores = []
    if not data.get("numeroEmpleado") or not isinstance(data["numeroEmpleado"], str) or data["numeroEmpleado"].strip() == "":
        errores.append("numeroEmpleado es requerido y debe ser texto")
    if not data.get("nombres") or not isinstance(data["nombres"], str) or data["nombres"].strip() == "":
        errores.append("nombres es requerido y debe ser texto")
    if not data.get("apellidos") or not isinstance(data["apellidos"], str) or data["apellidos"].strip() == "":
        errores.append("apellidos es requerido y debe ser texto")
    if "horasClase" not in data:
        errores.append("horasClase es requerido")
    else:
        try:
            h = int(data["horasClase"])
            if h < 0:
                errores.append("horasClase debe ser un número positivo")
        except (ValueError, TypeError):
            errores.append("horasClase debe ser un número entero")
    return errores

@app.route("/alumnos", methods=["GET"])
def get_alumnos():
    return jsonify([a.to_dict() for a in Alumno.query.all()]), 200

@app.route("/alumnos/<int:id>", methods=["GET"])
def get_alumno(id):
    a = Alumno.query.get(id)
    if a is None:
        return jsonify({"error": "Alumno no encontrado"}), 404
    return jsonify(a.to_dict()), 200

@app.route("/alumnos", methods=["POST"])
def create_alumno():
    try:
        data = request.get_json()
        if data is None:
            return jsonify({"error": "El cuerpo debe ser JSON válido"}), 400
        errores = validar_alumno(data)
        if errores:
            return jsonify({"errores": errores}), 400
        a = Alumno(nombres=data["nombres"].strip(), apellidos=data["apellidos"].strip(),
                   matricula=data["matricula"].strip(), promedio=float(data["promedio"]),
                   password=data.get("password"))
        db.session.add(a)
        db.session.commit()
        return jsonify(a.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@app.route("/alumnos/<int:id>", methods=["PUT"])
def update_alumno(id):
    try:
        a = Alumno.query.get(id)
        if a is None:
            return jsonify({"error": "Alumno no encontrado"}), 404
        data = request.get_json()
        if data is None:
            return jsonify({"error": "El cuerpo debe ser JSON válido"}), 400
        errores = validar_alumno(data)
        if errores:
            return jsonify({"errores": errores}), 400
        a.nombres = data["nombres"].strip()
        a.apellidos = data["apellidos"].strip()
        a.matricula = data["matricula"].strip()
        a.promedio = float(data["promedio"])
        if "password" in data:
            a.password = data["password"]
        db.session.commit()
        return jsonify(a.to_dict()), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@app.route("/alumnos/<int:id>", methods=["DELETE"])
def delete_alumno(id):
    try:
        a = Alumno.query.get(id)
        if a is None:
            return jsonify({"error": "Alumno no encontrado"}), 404
        db.session.delete(a)
        db.session.commit()
        return jsonify({"message": "Alumno eliminado"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@app.route("/alumnos/<int:id>/fotoPerfil", methods=["POST"])
def upload_foto(id):
    try:
        a = Alumno.query.get(id)
        if a is None:
            return jsonify({"error": "Alumno no encontrado"}), 404
        if "foto" not in request.files:
            return jsonify({"error": "Se requiere el campo foto"}), 400
        archivo = request.files["foto"]
        extension = archivo.filename.rsplit(".", 1)[-1].lower() if "." in archivo.filename else "jpg"
        nombre_archivo = f"alumnos/{id}/foto.{extension}"
        s3 = boto3.client("s3", region_name=AWS_REGION)
        s3.upload_fileobj(archivo, S3_BUCKET, nombre_archivo,
                          ExtraArgs={"ACL": "public-read", "ContentType": archivo.content_type})
        url = f"https://{S3_BUCKET}.s3.amazonaws.com/{nombre_archivo}"
        a.fotoPerfilUrl = url
        db.session.commit()
        return jsonify({"fotoPerfilUrl": url}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@app.route("/alumnos/<int:id>/email", methods=["POST"])
def send_email(id):
    try:
        a = Alumno.query.get(id)
        if a is None:
            return jsonify({"error": "Alumno no encontrado"}), 404
        mensaje = f"Nombre: {a.nombres} {a.apellidos}\nMatrícula: {a.matricula}\nPromedio: {a.promedio}"
        sns = boto3.client("sns", region_name=AWS_REGION)
        sns.publish(TopicArn=SNS_TOPIC_ARN, Message=mensaje,
                    Subject=f"Calificaciones de {a.nombres} {a.apellidos}")
        return jsonify({"message": "Correo enviado"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/alumnos/<int:id>/session/login", methods=["POST"])
def login(id):
    try:
        a = Alumno.query.get(id)
        if a is None:
            return jsonify({"error": "Alumno no encontrado"}), 404
        data = request.get_json()
        if data is None or "password" not in data:
            return jsonify({"error": "Se requiere password"}), 400
        if data["password"] != a.password:
            return jsonify({"error": "Contraseña incorrecta"}), 400
        session_string = secrets.token_hex(64)
        dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)
        tabla = dynamodb.Table(DYNAMODB_TABLE)
        tabla.put_item(Item={"id": str(uuid.uuid4()), "fecha": int(time.time()),
                             "alumnoId": id, "active": True, "sessionString": session_string})
        return jsonify({"sessionString": session_string}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/alumnos/<int:id>/session/verify", methods=["POST"])
def verify_session(id):
    try:
        data = request.get_json()
        if data is None or "sessionString" not in data:
            return jsonify({"error": "Se requiere sessionString"}), 400
        dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)
        tabla = dynamodb.Table(DYNAMODB_TABLE)
        respuesta = tabla.scan(
            FilterExpression=boto3.dynamodb.conditions.Attr("sessionString").eq(data["sessionString"])
            & boto3.dynamodb.conditions.Attr("alumnoId").eq(id))
        items = respuesta.get("Items", [])
        if not items or not items[0].get("active", False):
            return jsonify({"error": "Sesión inválida"}), 400
        return jsonify({"message": "Sesión válida"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/alumnos/<int:id>/session/logout", methods=["POST"])
def logout(id):
    try:
        data = request.get_json()
        if data is None or "sessionString" not in data:
            return jsonify({"error": "Se requiere sessionString"}), 400
        dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)
        tabla = dynamodb.Table(DYNAMODB_TABLE)
        respuesta = tabla.scan(
            FilterExpression=boto3.dynamodb.conditions.Attr("sessionString").eq(data["sessionString"])
            & boto3.dynamodb.conditions.Attr("alumnoId").eq(id))
        items = respuesta.get("Items", [])
        if not items:
            return jsonify({"error": "Sesión no encontrada"}), 400
        tabla.update_item(Key={"id": items[0]["id"]},
                          UpdateExpression="SET active = :val",
                          ExpressionAttributeValues={":val": False})
        return jsonify({"message": "Sesión cerrada"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/profesores", methods=["GET"])
def get_profesores():
    return jsonify([p.to_dict() for p in Profesor.query.all()]), 200

@app.route("/profesores/<int:id>", methods=["GET"])
def get_profesor(id):
    p = Profesor.query.get(id)
    if p is None:
        return jsonify({"error": "Profesor no encontrado"}), 404
    return jsonify(p.to_dict()), 200

@app.route("/profesores", methods=["POST"])
def create_profesor():
    try:
        data = request.get_json()
        if data is None:
            return jsonify({"error": "El cuerpo debe ser JSON válido"}), 400
        errores = validar_profesor(data)
        if errores:
            return jsonify({"errores": errores}), 400
        p = Profesor(numeroEmpleado=data["numeroEmpleado"].strip(), nombres=data["nombres"].strip(),
                     apellidos=data["apellidos"].strip(), horasClase=int(data["horasClase"]))
        db.session.add(p)
        db.session.commit()
        return jsonify(p.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@app.route("/profesores/<int:id>", methods=["PUT"])
def update_profesor(id):
    try:
        p = Profesor.query.get(id)
        if p is None:
            return jsonify({"error": "Profesor no encontrado"}), 404
        data = request.get_json()
        if data is None:
            return jsonify({"error": "El cuerpo debe ser JSON válido"}), 400
        errores = validar_profesor(data)
        if errores:
            return jsonify({"errores": errores}), 400
        p.numeroEmpleado = data["numeroEmpleado"].strip()
        p.nombres = data["nombres"].strip()
        p.apellidos = data["apellidos"].strip()
        p.horasClase = int(data["horasClase"])
        db.session.commit()
        return jsonify(p.to_dict()), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@app.route("/profesores/<int:id>", methods=["DELETE"])
def delete_profesor(id):
    try:
        p = Profesor.query.get(id)
        if p is None:
            return jsonify({"error": "Profesor no encontrado"}), 404
        db.session.delete(p)
        db.session.commit()
        return jsonify({"message": "Profesor eliminado"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
