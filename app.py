from flask import Flask, jsonify, request

app = Flask(__name__)

# ── Almacenamiento en memoria ──────────────────────────────────────────────────
alumnos = []
profesores = []
alumno_id_counter = 1
profesor_id_counter = 1

# ── Helpers de validación ──────────────────────────────────────────────────────
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

# ── Endpoints Alumnos ──────────────────────────────────────────────────────────
@app.route("/alumnos", methods=["GET"])
def get_alumnos():
    return jsonify(alumnos), 200

@app.route("/alumnos/<int:id>", methods=["GET"])
def get_alumno(id):
    alumno = next((a for a in alumnos if a["id"] == id), None)
    if alumno is None:
        return jsonify({"error": "Alumno no encontrado"}), 404
    return jsonify(alumno), 200

@app.route("/alumnos", methods=["POST"])
def create_alumno():
    global alumno_id_counter
    try:
        data = request.get_json()
        if data is None:
            return jsonify({"error": "El cuerpo debe ser JSON válido"}), 400
        errores = validar_alumno(data)
        if errores:
            return jsonify({"errores": errores}), 400
        nuevo = {
            "id": alumno_id_counter,
            "nombres": data["nombres"].strip(),
            "apellidos": data["apellidos"].strip(),
            "matricula": data["matricula"].strip(),
            "promedio": float(data["promedio"])
        }
        alumno_id_counter += 1
        alumnos.append(nuevo)
        return jsonify(nuevo), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/alumnos/<int:id>", methods=["PUT"])
def update_alumno(id):
    try:
        alumno = next((a for a in alumnos if a["id"] == id), None)
        if alumno is None:
            return jsonify({"error": "Alumno no encontrado"}), 404
        data = request.get_json()
        if data is None:
            return jsonify({"error": "El cuerpo debe ser JSON válido"}), 400
        errores = validar_alumno(data)
        if errores:
            return jsonify({"errores": errores}), 400
        alumno["nombres"] = data["nombres"].strip()
        alumno["apellidos"] = data["apellidos"].strip()
        alumno["matricula"] = data["matricula"].strip()
        alumno["promedio"] = float(data["promedio"])
        return jsonify(alumno), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/alumnos/<int:id>", methods=["DELETE"])
def delete_alumno(id):
    global alumnos
    alumno = next((a for a in alumnos if a["id"] == id), None)
    if alumno is None:
        return jsonify({"error": "Alumno no encontrado"}), 404
    alumnos = [a for a in alumnos if a["id"] != id]
    return jsonify({"message": "Alumno eliminado"}), 200

# ── Endpoints Profesores ───────────────────────────────────────────────────────
@app.route("/profesores", methods=["GET"])
def get_profesores():
    return jsonify(profesores), 200

@app.route("/profesores/<int:id>", methods=["GET"])
def get_profesor(id):
    profesor = next((p for p in profesores if p["id"] == id), None)
    if profesor is None:
        return jsonify({"error": "Profesor no encontrado"}), 404
    return jsonify(profesor), 200

@app.route("/profesores", methods=["POST"])
def create_profesor():
    global profesor_id_counter
    try:
        data = request.get_json()
        if data is None:
            return jsonify({"error": "El cuerpo debe ser JSON válido"}), 400
        errores = validar_profesor(data)
        if errores:
            return jsonify({"errores": errores}), 400
        nuevo = {
            "id": profesor_id_counter,
            "numeroEmpleado": data["numeroEmpleado"].strip(),
            "nombres": data["nombres"].strip(),
            "apellidos": data["apellidos"].strip(),
            "horasClase": int(data["horasClase"])
        }
        profesor_id_counter += 1
        profesores.append(nuevo)
        return jsonify(nuevo), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/profesores/<int:id>", methods=["PUT"])
def update_profesor(id):
    try:
        profesor = next((p for p in profesores if p["id"] == id), None)
        if profesor is None:
            return jsonify({"error": "Profesor no encontrado"}), 404
        data = request.get_json()
        if data is None:
            return jsonify({"error": "El cuerpo debe ser JSON válido"}), 400
        errores = validar_profesor(data)
        if errores:
            return jsonify({"errores": errores}), 400
        profesor["numeroEmpleado"] = data["numeroEmpleado"].strip()
        profesor["nombres"] = data["nombres"].strip()
        profesor["apellidos"] = data["apellidos"].strip()
        profesor["horasClase"] = int(data["horasClase"])
        return jsonify(profesor), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/profesores/<int:id>", methods=["DELETE"])
def delete_profesor(id):
    global profesores
    profesor = next((p for p in profesores if p["id"] == id), None)
    if profesor is None:
        return jsonify({"error": "Profesor no encontrado"}), 404
    profesores = [p for p in profesores if p["id"] != id]
    return jsonify({"message": "Profesor eliminado"}), 200

# ── Arranque ───────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)