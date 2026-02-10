## =============================================
## ============== Bases de Dados ===============
## ==================HOSPITAL===================
## =============================================
##
##   Authors:
##   Daniel Pereira  2021237092
##   Eduardo Marques 2022231584
##   Andre Cardoso   2022222265


from calendar import month_name
import hashlib
import os
import flask
import logging
import psycopg2
import time
from flask import request, jsonify
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
import datetime
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
app = flask.Flask(__name__)
app.config['JWT_SECRET_KEY'] = 'super-secret'
jwt = JWTManager(app)

##########################STATUS##########################

StatusCodes = {
    'success': 200,
    'api_error': 400,
    'internal_error': 500
}


##########################################################
####################DATABASE ACCESS#######################
##########################################################

def db_connection():
    db = psycopg2.connect(
        user='projeto',
        password='projeto',
        host='127.0.0.1',
        port='5432',
        database='projetoBD'
    )
    return db


@app.route('/')
def landing_page():
    return """
    Olá Bem-vindo à Base de Dados do Hospital!  <br/>
    <br/>
    <br/>
    Daniel Pereira  2021237092
    <br/>
    Eduardo Marques 2022231584
    <br/>
    André Cardoso   2022222265
    <br/>
    Equipa do Projeto de BD de 2023-2024 <br/>
    <br/>
    """


def hash_password(password):
    salt = os.urandom(16)
    hash_obj = hashlib.sha256(salt + password.encode())
    return salt + hash_obj.digest()


def check_password(stored_password, provided_password):
    salt = stored_password[:16]
    stored_hash = stored_password[16:]
    hash_obj = hashlib.sha256(salt + provided_password.encode())
    return stored_hash == hash_obj.digest()


def autenticacao(numero_cc, password):
    conn = db_connection()
    cur = conn.cursor()
    cur.execute('SELECT numero_cc, password FROM pessoa WHERE numero_cc = %s ', (numero_cc,))
    usuario = cur.fetchone()
    if usuario and check_password(bytes.fromhex(usuario[1]), password):
        return usuario[0]
    return None


@app.route('/dbproj/user', methods=['PUT'])
def login():
    numero_cc = flask.request.json.get('numero_cc', None)
    password = flask.request.json.get('password', None)
    if not numero_cc or not password:
        return jsonify({"msg": "Por favor, forneça o número de CC e a password"}), 400
    usuario = autenticacao(numero_cc, password)
    if not usuario:
        return jsonify({"msg": "Credenciais inválidas"}), 401
    access_token = create_access_token(identity=usuario)
    return jsonify(access_token=access_token), 200


def criar_pessoa(cur, payload):
    conn = db_connection()
    hashed_password = hash_password(payload['password'])
    cur.execute('INSERT INTO pessoa (numero_cc, password, nome, data_nascimento, mail) VALUES (%s, %s, %s, %s, %s)', (
    payload['numero_cc'], hashed_password.hex(), payload['nome'], payload['data_nascimento'], payload['mail']))
    conn.commit()
    conn.close()


@app.route('/dbproj/register/patient', methods=['POST'])
def criar_paciente():
    logger.info('POST /dbproj/register/patient')
    payload = flask.request.get_json()
    conn = db_connection()
    cur = conn.cursor()
    logger.debug(f'POST /dbproj/register/patient - payload: {payload}')
    requesitos = ['numero_cc', 'password', 'nome', 'data_nascimento', 'mail']
    falta = [elemento for elemento in requesitos if elemento not in payload]
    if falta:
        resposta = {
            'status': StatusCodes['api_error'],
            'results': f'Faltam os seguintes parâmetros para o registro: {", ".join(falta)}'
        }
        return flask.jsonify(resposta)
    try:
        cur.execute('SELECT numero_cc FROM pessoa WHERE numero_cc = %s', (payload['numero_cc'],))
        pessoa_existe = cur.fetchone()
        if not pessoa_existe:
            criar_pessoa(cur, payload)
        cur.execute('INSERT INTO paciente (pessoa_numero_cc) VALUES (%s)', (payload['numero_cc'],))
        conn.commit()
        resposta = {'status': StatusCodes['success'],
                    'results': f'O paciente com o número de CC {payload["numero_cc"]} foi inserido com sucesso.'}
    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(f'POST /dbproj/register/patient - error: {error}')
        resposta = {'status': StatusCodes['internal_error'], 'errors': str(error)}
        conn.rollback()
    finally:
        if conn is not None:
            conn.close()
    return flask.jsonify(resposta)


def criar_funcionario(cur, payload):
    cur.execute("SELECT MAX(id_funcionario) FROM funcionario")
    ultimo_id = cur.fetchone()[0]
    novo_id = 1 if ultimo_id is None else ultimo_id + 1
    cur.execute(
        'INSERT INTO funcionario (id_funcionario, contrato_valido, inicio_contrato_atual, salario, pessoa_numero_cc) VALUES (%s, %s, %s, %s, %s) RETURNING id_funcionario',
        (novo_id, payload['contrato_valido'], payload['inicio_contrato_atual'], payload['salario'],
         payload['numero_cc']))
    return novo_id


def criar_especialidade(medico_cc, id_especialidade, cur):
    conn = db_connection()
    cur.execute(
        "INSERT INTO medico_especialidade (medico_funcionario_pessoa_numero_cc, especialidade_id_especialidade) VALUES (%s, %s)",
        (medico_cc, id_especialidade))
    conn.commit()
    conn.close()


@app.route('/dbproj/register/doctor', methods=['POST'])
def criar_medico():
    logger.info('POST /dbproj/register/doctor')
    payload = flask.request.get_json()
    conn = db_connection()
    cur = conn.cursor()
    logger.debug(f'POST /dbproj/register/doctor - payload: {payload}')
    requesitos = ['licenca_medica', 'contrato_valido', 'inicio_contrato_atual', 'salario', 'numero_cc', 'password']
    falta = [elemento for elemento in requesitos if elemento not in payload]
    if falta:
        resposta = {
            'status': StatusCodes['api_error'],
            'results': f'Faltam os seguintes parâmetros para o registro: {", ".join(falta)}'
        }
        return flask.jsonify(resposta)
    try:
        cur.execute('SELECT numero_cc FROM pessoa WHERE numero_cc = %s', (payload['numero_cc'],))
        pessoa_existe = cur.fetchone()
        if not pessoa_existe:
            criar_pessoa(cur, payload)
        funcionario_id = criar_funcionario(cur, payload)
        cur.execute('INSERT INTO medico (licenca_medica, funcionario_pessoa_numero_cc) VALUES (%s, %s)',
                    (payload['licenca_medica'], payload['numero_cc']))
        criar_especialidade(payload['numero_cc'], payload['id_especialidade'], cur)
        conn.commit()
        resposta = {'status': StatusCodes['success'],
                    'results': f'O medico com o número de CC {payload["numero_cc"]} e ID {funcionario_id} foi inserido com sucesso.'}
    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(f'POST /dbproj/register/doctor - error: {error}')
        resposta = {'status': StatusCodes['internal_error'], 'errors': str(error)}
        conn.rollback()
    finally:
        if conn is not None:
            conn.close()
    return flask.jsonify(resposta)


@app.route('/dbproj/register/nurse', methods=['POST'])
def criar_enfermeiro():
    logger.info('POST /dbproj/register/nurse')
    payload = flask.request.get_json()
    conn = db_connection()
    cur = conn.cursor()
    logger.debug(f'POST /dbproj/register/nurse - payload: {payload}')
    requesitos = ['cat_herarquica', 'contrato_valido', 'inicio_contrato_atual', 'salario', 'numero_cc', 'password']
    falta = [elemento for elemento in requesitos if elemento not in payload]
    if falta:
        resposta = {
            'status': StatusCodes['api_error'],
            'results': f'Faltam os seguintes parâmetros para o registro: {", ".join(falta)}'
        }
        return flask.jsonify(resposta)
    try:
        cur.execute('SELECT numero_cc FROM pessoa WHERE numero_cc = %s', (payload['numero_cc'],))
        pessoa_existe = cur.fetchone()
        if not pessoa_existe:
            criar_pessoa(cur, payload)
        funcionario_id = criar_funcionario(cur, payload)
        cur.execute('INSERT INTO enfermeiro (cat_herarquica, funcionario_pessoa_numero_cc) VALUES (%s, %s)',
                    (payload['cat_herarquica'], payload['numero_cc']))
        conn.commit()
        resposta = {'status': StatusCodes['success'],
                    'results': f'O enfermeiro com o número de CC {payload["numero_cc"]} e ID {funcionario_id} foi inserido com sucesso'}
    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(f'POST /dbproj/register/nurse - error: {error}')
        resposta = {'status': StatusCodes['internal_error'], 'errors': str(error)}
        conn.rollback()
    finally:
        if conn is not None:
            conn.close()

    return flask.jsonify(resposta)


@app.route('/dbproj/register/assistant', methods=['POST'])
def criar_assistente():
    logger.info('POST /dbproj/register/assistant')
    payload = flask.request.get_json()
    conn = db_connection()
    cur = conn.cursor()
    logger.debug(f'POST /dbproj/register/assistant - payload: {payload}')
    requesitos = ['contrato_valido', 'inicio_contrato_atual', 'salario', 'numero_cc', 'password']
    falta = [elemento for elemento in requesitos if elemento not in payload]
    if falta:
        resposta = {
            'status': StatusCodes['api_error'],
            'results': f'Faltam os seguintes parâmetros para o registro: {", ".join(falta)}'
        }
        return flask.jsonify(resposta)
    try:
        cur.execute('SELECT numero_cc FROM pessoa WHERE numero_cc = %s', (payload['numero_cc'],))
        pessoa_existe = cur.fetchone()
        if not pessoa_existe:
            criar_pessoa(cur, payload)
        funcionario_id = criar_funcionario(cur, payload)
        cur.execute('INSERT INTO assistente (funcionario_pessoa_numero_cc) VALUES (%s)', (payload['numero_cc'],))
        conn.commit()
        resposta = {'status': StatusCodes['success'],
                    'results': f'O assistente com o número de CC {payload["numero_cc"]} e ID {funcionario_id} foi inserido com sucesso'}
    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(f'POST /dbproj/register/assistant - error: {error}')
        resposta = {'status': StatusCodes['internal_error'], 'errors': str(error)}
        conn.rollback()
    finally:
        if conn is not None:
            conn.close()
    return flask.jsonify(resposta)


def conflito_horarios_medico(medico_id, data, cur):
    conn = db_connection()
    cur = conn.cursor()

    cur.execute("SELECT pessoa_numero_cc FROM funcionario WHERE id_funcionario = %s", (medico_id,))
    numero_cc = cur.fetchone()[0]

    cur.execute("""
        SELECT COUNT(*) FROM consulta 
        WHERE medico_funcionario_pessoa_numero_cc = %s 
        AND ((data_consulta >= %s AND data_consulta < CAST(%s AS TIMESTAMP) + INTERVAL '1 hour')
        OR (data_consulta + INTERVAL '1 hour' > %s AND data_consulta < %s))
    """, (numero_cc, data, data, data, data))

    consultas_count = cur.fetchone()[0]

    cur.execute("""
        SELECT COUNT(*) FROM cirurgia 
        WHERE medico_funcionario_pessoa_numero_cc = %s 
        AND ((data_cirurgia >= %s AND data_cirurgia < CAST(%s AS TIMESTAMP) + INTERVAL '2 hours')
        OR (data_cirurgia + INTERVAL '2 hours' > %s AND data_cirurgia < %s))
    """, (numero_cc, data, data, data, data))

    cirurgias_count = cur.fetchone()[0]
    total_conflitos = consultas_count + cirurgias_count
    conn.close()
    return 0 if total_conflitos > 0 else 1


def conflito_horarios_paciente(paciente_cc, data, cur):
    conn = db_connection()
    cur = conn.cursor()

    cur.execute("""
            SELECT COUNT(*) FROM consulta 
            WHERE paciente_pessoa_numero_cc = %s 
            AND ((data_consulta >= %s AND data_consulta < CAST(%s AS TIMESTAMP) + INTERVAL '1 hour')
            OR (data_consulta + INTERVAL '1 hour' > %s AND data_consulta < %s))
        """, (paciente_cc, data, data, data, data))

    consultas_count = cur.fetchone()[0]

    cur.execute("""
            SELECT COUNT(*) FROM cirurgia 
            WHERE paciente_pessoa_numero_cc = %s 
            AND ((data_cirurgia >= %s AND data_cirurgia < CAST(%s AS TIMESTAMP) + INTERVAL '2 hours')
            OR (data_cirurgia + INTERVAL '2 hours' > %s AND data_cirurgia < %s))
        """, (paciente_cc, data, data, data, data))

    cirurgias_count = cur.fetchone()[0]
    total_conflitos = consultas_count + cirurgias_count
    conn.close()
    return 0 if total_conflitos > 0 else 1


def conflito_horarios_enfermeiros(enfermeiro_id, data, cur):
    conn = db_connection()
    cur = conn.cursor()
    cur.execute("SELECT pessoa_numero_cc FROM funcionario WHERE id_funcionario = %s", (enfermeiro_id,))
    numero_cc = cur.fetchone()[0]

    cur.execute("""
            SELECT COUNT(*) FROM cirurgia 
            WHERE id_cirurgia in (SELECT cirurgia_id_cirurgia FROM enfermeiro_cirurgia WHERE enfermeiro_funcionario_pessoa_numero_cc = %s)
            AND ((data_cirurgia >= %s AND data_cirurgia < CAST(%s AS TIMESTAMP) + INTERVAL '2 hours')
            OR (data_cirurgia + INTERVAL '2 hours' > %s AND data_cirurgia < %s))
        """, (numero_cc, data, data, data, data))

    cirurgias_count = cur.fetchone()[0]
    conn.close()
    return 0 if cirurgias_count > 0 else 1


def criar_fatura(montante, paciente_cc, cur):
    conn = db_connection()
    cur.execute("SELECT MAX(id_despesa) FROM fatura")
    ultimo_id = cur.fetchone()[0]
    novo_id = 1 if ultimo_id is None else ultimo_id + 1
    cur.execute(
        "INSERT INTO fatura (id_despesa, montante , liquidacao, paciente_pessoa_numero_cc) VALUES (%s, %s, %s, %s)",
        (novo_id, montante, False, paciente_cc))
    conn.commit()
    conn.close()
    return novo_id


def criar_consulta(fatura_id, medico_id, usuario, cur, payload):
    cur.execute("SELECT MAX(id_consulta) FROM consulta")
    ultimo_id_consulta = cur.fetchone()[0]
    novo_id = 1 if ultimo_id_consulta is None else ultimo_id_consulta + 1
    cur.execute('SELECT pessoa_numero_cc FROM funcionario WHERE id_funcionario = %s', (medico_id,))
    medico_cc = cur.fetchone()
    cur.execute(
        'INSERT INTO consulta (id_consulta, data_consulta, preco, especialidade_id_especialidade, fatura_id_despesa, medico_funcionario_pessoa_numero_cc, paciente_pessoa_numero_cc) VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id_consulta',
        (novo_id, payload['data_consulta'], payload['preco'], payload['id_especialidade'],
         fatura_id, medico_cc, payload['paciente_cc']))
    return novo_id


@app.route('/dbproj/appointment', methods=['POST'])
@jwt_required()
def adicionar_consulta():
    usuario = get_jwt_identity()
    conn = db_connection()
    cur = conn.cursor()

    payload = flask.request.get_json()
    requesitos = ['data_consulta', 'preco', 'id_especialidade', 'medico_id', 'paciente_cc']
    falta = [elemento for elemento in requesitos if elemento not in payload]
    if falta:
        resposta = {
            'status': StatusCodes['api_error'],
            'results': f'Faltam os seguintes parâmetros: {", ".join(falta)}'
        }
        return flask.jsonify(resposta)
    paciente_cc = payload['paciente_cc']
    paciente_existe = str(usuario) == str(paciente_cc)
    conn.close()
    if not paciente_existe:
        return jsonify({"msg": f"Apenas o próprio paciente pode criar consultas"}), 400
    if conflito_horarios_medico(payload['medico_id'], payload['data_consulta'], cur) == 0:
        return jsonify({"msg": "O médico não tem disponibilidade nesse horário"}), 400

    if conflito_horarios_paciente(payload['paciente_cc'], payload['data_consulta'], cur) == 0:
        return jsonify({"msg": "O paciente não tem disponibilidade nesse horário"}), 400

    try:
        conn = db_connection()
        cur = conn.cursor()
        fatura_id = criar_fatura(payload['preco'], payload['paciente_cc'], cur)
        novo_id = criar_consulta(fatura_id, payload['medico_id'], usuario, cur, payload)
        conn.commit()
        resposta = {'status': StatusCodes['success'],
                    'results': f'A consulta foi criada com sucesso com o ID {novo_id} e a fatura com o ID {fatura_id}'}
    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(f'POST /dbproj/appointment - error: {error}')
        resposta = {'status': StatusCodes['internal_error'], 'errors': str(error)}
        conn.rollback()
    finally:
        if conn is not None:
            conn.close()
    return flask.jsonify(resposta)


@app.route('/dbproj/appointments/<int:patient_user_id>', methods=['GET'])
@jwt_required()
def imprimir_consultas(patient_user_id):
    usuario = get_jwt_identity()
    conn = db_connection()
    cur = conn.cursor()
    cur.execute('SELECT * FROM paciente WHERE pessoa_numero_cc = %s', (patient_user_id,))
    confirmacao = cur.fetchone()
    if not confirmacao:
        return jsonify({"msg": f'Não existe paciente com o ID {patient_user_id}'}), 400
    try:
        cur.execute('SELECT * FROM medico WHERE funcionario_pessoa_numero_cc = %s', (usuario,))
        medico_existe = cur.fetchone()
        cur.execute('SELECT * FROM assistente WHERE funcionario_pessoa_numero_cc = %s', (usuario,))
        assistente_existe = cur.fetchone()
        paciente_existe = usuario == patient_user_id
        if not medico_existe and not assistente_existe and not paciente_existe:
            return jsonify(
                {"msg": "Apenas assistentes, o próprio médico e o próprio paciente podem imprimir as consultas."}), 400
        cur.execute(
            'SELECT id_consulta, medico_funcionario_pessoa_numero_cc, data_consulta FROM consulta WHERE paciente_pessoa_numero_cc = %s',
            (patient_user_id,))
        consultas = cur.fetchall()
        consultas_detalhes = []
        for consulta in consultas:
            consulta_id, medico_cc, data = consulta
            cur.execute('SELECT nome FROM pessoa WHERE numero_cc = %s', (medico_cc,))
            medico_nome = cur.fetchone()[0]
            cur.execute('SELECT id_funcionario FROM funcionario WHERE pessoa_numero_cc = %s', (medico_cc,))
            medico_id = cur.fetchone()[0]
            consulta_detalhes = {
                "consulta_id": consulta_id,
                "medico_id": medico_id,
                "medico_name": medico_nome,
                "date": data
            }
            consultas_detalhes.append(consulta_detalhes)
        resposta = {'status': 200, 'results': consultas_detalhes}
    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(f'GET /dbproj/appointments/{patient_user_id} - error: {error}')
        resposta = {'status': 500, 'errors': str(error)}
    finally:
        if conn is not None:
            conn.close()
    return flask.jsonify(resposta)


@app.route('/dbproj/prescriptions/<int:patient_user_id>', methods=['GET'])
@jwt_required()
def imprimir_receitas(patient_user_id):
    usuario = get_jwt_identity()
    conn = db_connection()
    cur = conn.cursor()
    cur.execute('SELECT * FROM paciente WHERE pessoa_numero_cc = %s', (patient_user_id,))
    confirmacao = cur.fetchone()
    if not confirmacao:
        return jsonify({"msg": f'Não existe paciente com o ID {patient_user_id}'}), 400
    try:
        cur.execute('SELECT * FROM assistente WHERE funcionario_pessoa_numero_cc = %s', (usuario,))
        assistente_existe = cur.fetchone()
        cur.execute('SELECT * FROM medico WHERE funcionario_pessoa_numero_cc = %s', (usuario,))
        medico_existe = cur.fetchone()
        cur.execute('SELECT * FROM enfermeiro WHERE funcionario_pessoa_numero_cc = %s', (usuario,))
        enfermeiro_existe = cur.fetchone()
        paciente_existe = usuario == patient_user_id
        if not assistente_existe and not medico_existe and not enfermeiro_existe and not paciente_existe:
            return jsonify({"msg": "Apenas funcionarios e o próprio paciente podem visualizar as receitas"}), 400
        cur.execute('''
        SELECT r.id_receita, r.validade, m.nome AS medicamento_nome, m.dosagem AS medicamento_dose, m.frequencia AS medicamento_frequencia
        FROM receita r
        LEFT JOIN consulta_receita cr ON r.id_receita = cr.receita_id_receita
        LEFT JOIN receita_internamento ir ON r.id_receita = ir.receita_id_receita
        LEFT JOIN consulta c ON cr.consulta_id_consulta = c.id_consulta
        LEFT JOIN internamento i ON ir.internamento_id_internamento = i.id_internamento
        LEFT JOIN medicamento m ON m.receita_id_receita = r.id_receita
        WHERE (c.paciente_pessoa_numero_cc = %s OR i.paciente_pessoa_numero_cc = %s)
        ''', (patient_user_id, patient_user_id))
        receitas = cur.fetchall()
        receita_detalhes = {}
        for receita in receitas:
            receita_id, validade, medicamento_nome, medicamento_dose, medicamento_frequencia = receita
            receita_detalhes[receita_id] = {
                "receita_id": receita_id,
                "validade": validade,
                "podologia": []
            }
            receita_detalhes[receita_id]["podologia"].append({
                "dose": medicamento_dose,
                "frequencia": medicamento_frequencia,
                "medicamento": medicamento_nome
            })
        resposta = {'status': 200, 'results': list(receita_detalhes.values())}
    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(f'GET /dbproj/prescriptions/{patient_user_id} - error: {error}')
        resposta = {'status': 500, 'errors': str(error)}
    finally:
        if conn is not None:
            conn.close()
    return jsonify(resposta)


def criar_prescricao(tipo, evento_id, cur, payload):
    conn = db_connection()
    cur.execute("SELECT MAX(id_receita) FROM receita")
    ultimo_id = cur.fetchone()[0]
    novo_id = 1 if ultimo_id is None else ultimo_id + 1
    cur.execute('INSERT INTO receita (id_receita, validade) VALUES (%s, %s) RETURNING id_receita',
                (novo_id, payload['validade']))
    if (tipo == 'consulta'):
        cur.execute(
            'INSERT INTO consulta_receita (consulta_id_consulta, receita_id_receita) VALUES (%s, %s)',
            (evento_id, novo_id))
        conn.commit()
        conn.close()
        return novo_id
    elif (tipo == 'internamento'):
        cur.execute(
            'INSERT INTO receita_internamento (receita_id_receita, internamento_id_internamento) VALUES (%s, %s) ',
            (novo_id, evento_id))
        conn.commit()
        conn.close()
        return novo_id
    else:
        return 'erro'


def criar_medicamento(receita_id, nome, dosagem, frequencia, cur):
    conn = db_connection()
    cur.execute("SELECT MAX(id_medicamento) FROM medicamento")
    ultimo_id = cur.fetchone()[0]
    novo_id = 1 if ultimo_id is None else ultimo_id + 1
    cur.execute(
        "INSERT INTO medicamento (id_medicamento, nome, dosagem, receita_id_receita, frequencia) VALUES (%s, %s, %s, %s, %s)",
        (novo_id, nome, dosagem, receita_id, frequencia))
    conn.commit()
    conn.close()
    return novo_id


def criar_efeito(nome, gravidade, id_medicamento, probabilidade, cur):
    conn = db_connection()
    cur.execute(
        "INSERT INTO efeito_colateral (nome, gravidade, medicamento_id_medicamento, probabilidade) VALUES (%s, %s, %s, %s)",
        (nome, gravidade, id_medicamento, probabilidade))
    conn.commit()
    conn.close()


@app.route('/dbproj/prescription', methods=['POST'])
@jwt_required()
def adicionar_prescricao():
    usuario = get_jwt_identity()
    conn = db_connection()
    cur = conn.cursor()

    payload = flask.request.get_json()
    requesitos = ['tipo', 'evento_id', 'validade', 'medicamentos']
    falta = [elemento for elemento in requesitos if elemento not in payload]
    if falta:
        resposta = {
            'status': StatusCodes['api_error'],
            'results': f'Faltam os seguintes parâmetros: {", ".join(falta)}'
        }
        return flask.jsonify(resposta)

    cur.execute('SELECT * FROM consulta WHERE medico_funcionario_pessoa_numero_cc = %s AND id_consulta = %s',
                (usuario, payload['evento_id']))
    verificar_consulta = cur.fetchone()

    cur.execute(
        'SELECT * FROM internamento WHERE enfermeiro_funcionario_pessoa_numero_cc = %s AND id_internamento = %s',
        (usuario, payload['evento_id']))
    verificar_internamento = cur.fetchone()

    if (not verificar_consulta) and (not verificar_internamento):
        return jsonify({"msg": f'Apenas o próprio médico ou o próprio enfermeiro podem adicionar receitas'}), 400

    try:
        conn = db_connection()
        cur = conn.cursor()

        prescricao_id = criar_prescricao(payload['tipo'], payload['evento_id'], cur, payload)
        if prescricao_id == 'erro':
            return jsonify({"msg": f'Insira um tipo correto (consulta ou internamento)'}), 400
        for medicamento in payload['medicamentos']:
            medicamento_id = criar_medicamento(prescricao_id, medicamento['nome'], medicamento['dosagem'], medicamento['frequencia'], cur)
            for efeito in medicamento['efeitos']:
                criar_efeito(efeito['nome'], efeito['gravidade'], medicamento_id, efeito['probabilidade'], cur)
        conn.commit()
        resposta = {'status': StatusCodes['success'],
                    'results': f'A receita foi criada com sucesso com o ID {prescricao_id}'}
    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(f'POST /dbproj/prescription - error: {error}')
        resposta = {'status': StatusCodes['internal_error'], 'errors': str(error)}
        conn.rollback()
    finally:
        if conn is not None:
            conn.close()
    return flask.jsonify(resposta)


def criar_pagamento(metodo, id_fatura, montante, cur):
    conn = db_connection()
    cur.execute("SELECT MAX(id_pagamento) FROM pagamento")
    ultimo_id = cur.fetchone()[0]
    data = datetime.datetime.now()
    novo_id = 1 if ultimo_id is None else ultimo_id + 1
    cur.execute(
        "INSERT INTO pagamento (id_pagamento, metodo, fatura_id_despesa, montante, data) VALUES (%s, %s, %s, %s, %s)",
        (novo_id, metodo, id_fatura, montante, data))
    conn.commit()
    conn.close()


@app.route('/dbproj/bills/<int:bill_id>', methods=['POST'])
@jwt_required()
def efetuar_pagamento(bill_id):
    conn = db_connection()
    cur = conn.cursor()
    usuario = get_jwt_identity()
    payload = flask.request.get_json()
    requesitos = ['montante', 'metodo']
    falta = [elemento for elemento in requesitos if elemento not in payload]
    if falta:
        resposta = {
            'status': StatusCodes['api_error'],
            'results': f'Faltam os seguintes parâmetros: {", ".join(falta)}'
        }
        return flask.jsonify(resposta)
    cur.execute('SELECT * FROM fatura WHERE id_despesa = %s', (bill_id,))
    confirmacao = cur.fetchone()
    if not confirmacao:
        return jsonify({"msg": f'Não existe fatura com o ID {bill_id}'}), 400
    try:
        cur.execute('SELECT paciente_pessoa_numero_cc FROM fatura WHERE id_despesa = %s', (bill_id,))
        paciente_cc = cur.fetchone()[0]
        if usuario != paciente_cc:
            return jsonify({"msg": "Apenas o próprio paciente pode efetuar o pagamento"}), 400
        montante = payload['montante']
        if montante <= 0:
            return jsonify({"msg": "A quantia inserida tem que ser superior a zero"})
        metodo = payload['metodo']
        cur.execute('SELECT montante FROM fatura WHERE id_despesa = %s', (bill_id,))
        montante_total = cur.fetchone()[0]
        if montante_total == 0:
            return jsonify({
                "msg": f"A fatura {bill_id} encontra-se liquidada"}), 400
        if payload['montante'] > montante_total:
            return jsonify({
                "msg": f"O valor inserido é superior ao montante a pagar. Montante a pagar {montante_total}"}), 400
        restante = montante_total - montante
        if (restante == 0):
            cur.execute('UPDATE fatura SET liquidacao = %s WHERE id_despesa = %s', (True, bill_id))
        cur.execute('UPDATE fatura SET montante = %s WHERE id_despesa = %s', (restante, bill_id))
        criar_pagamento(metodo, bill_id, montante, cur)
        conn.commit()
        resposta = {'status': StatusCodes['success'],
                    'results': f'O pagamento com o ID {bill_id} foi efetuado com sucesso. Montante a pagar {restante}'}
    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(f'POST /dbproj/bills/{bill_id} - error: {error}')
        resposta = {'status': 500, 'errors': str(error)}
    finally:
        if conn is not None:
            conn.close()
    return flask.jsonify(resposta)


@app.route('/dbproj/daily_summary/<string:date>', methods=['GET'])
@jwt_required()
def sumario_diario(date):
    usuario = get_jwt_identity()
    conn = db_connection()
    cur = conn.cursor()
    try:
        cur.execute('SELECT * FROM assistente WHERE funcionario_pessoa_numero_cc = %s', (usuario,))
        assistente_existe = cur.fetchone()
        if not assistente_existe:
            return jsonify({"msg": "Apenas assistentes podem visualizar o sumario diário"}), 400
        cur.execute('''
                    SELECT 
                        (SELECT SUM(montante) 
                        FROM pagamento
                        WHERE data = %s ) AS somatorio_pagamentos,

                        (SELECT COUNT(DISTINCT c.id_consulta)
                         FROM consulta c
                         WHERE DATE(c.data_consulta) = %s) AS contador_consultas,

                        (SELECT COUNT(DISTINCT s.id_cirurgia)
                         FROM cirurgia s
                         WHERE DATE(s.data_cirurgia) = %s) AS contador_cirurgias,

                        (SELECT COUNT(DISTINCT r.id_receita)
                         FROM receita r
                         LEFT JOIN consulta_receita cr ON r.id_receita = cr.receita_id_receita
                         LEFT JOIN receita_internamento ir ON r.id_receita = ir.receita_id_receita
                         LEFT JOIN consulta c ON cr.consulta_id_consulta = c.id_consulta
                         LEFT JOIN internamento i ON ir.internamento_id_internamento = i.id_internamento
                         WHERE DATE(c.data_consulta) = %s OR DATE(i.inicio) = %s) AS contador_receitas
                ''', (date, date, date, date, date))
        resultados = cur.fetchone()
        resposta = {'status': 200, 'results': {
            'data': date,
            'total_gasto': resultados[0] if resultados[0] is not None else 0,
            'num_consultas': resultados[1],
            'num_cirurgias': resultados[2],
            'num_receitas': resultados[3]
        }},
    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(f'GET /dbproj/daily_summary/{date} - error: {error}')
        resposta = {'status': 500, 'errors': str(error)}
    finally:
        if conn is not None:
            conn.close()
    return flask.jsonify(resposta)


@app.route('/dbproj/top3', methods=['GET'])
@jwt_required()
def imprimir_top_3():
    usuario = get_jwt_identity()
    conn = db_connection()
    cur = conn.cursor()
    try:
        cur.execute('SELECT * FROM assistente WHERE funcionario_pessoa_numero_cc = %s', (usuario,))
        assistente_existe = cur.fetchone()
        if not assistente_existe:
            return jsonify({"msg": "Apenas assistentes podem visualizar o sumario diário"}), 400
        cur.execute('''
                    SELECT f.paciente_pessoa_numero_cc, SUM(pg.montante) AS total_gasto
                    FROM fatura f
                    INNER JOIN pagamento pg ON f.id_despesa = pg.fatura_id_despesa
                    GROUP BY f.paciente_pessoa_numero_cc
                    ORDER BY total_gasto DESC
                    LIMIT 3
                    ''')
        top3 = cur.fetchall()
        top3_detalhes = []
        for pessoa in top3:
            paciente_cc, total_gasto = pessoa
            cur.execute('SELECT nome FROM pessoa WHERE numero_cc = %s', (paciente_cc,))
            paciente_nome = cur.fetchone()[0]
            top3_detalhe = {
                "nome": paciente_nome,
                "total_gasto": total_gasto,
            }
            top3_detalhes.append(top3_detalhe)
        resposta = {'status': 200, 'results': top3_detalhes}
    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(f'GET /dbproj/top3 - error: {error}')
        resposta = {'status': 500, 'errors': str(error)}
    finally:
        if conn is not None:
            conn.close()
    return flask.jsonify(resposta)


def criar_enfermeiro_cirurgia(enfermeiro_id, id_cirurgia, cur):
    conn = db_connection()
    cur.execute('SELECT pessoa_numero_cc FROM funcionario WHERE id_funcionario = %s', (enfermeiro_id,))
    enfermeiro_cc = cur.fetchone()
    cur.execute(
        "INSERT INTO enfermeiro_cirurgia (enfermeiro_funcionario_pessoa_numero_cc, cirurgia_id_cirurgia) VALUES (%s, %s)",
        (enfermeiro_cc, id_cirurgia))
    conn.commit()
    conn.close()


def criar_cirurgia(id_internamento, tipo, data, preco, paciente_cc, id_especialidade, fatura_id, medico_id, cur,
                   payload):
    cur.execute("SELECT MAX(id_cirurgia) FROM cirurgia")
    ultimo_id = cur.fetchone()[0]
    novo_id = 1 if ultimo_id is None else ultimo_id + 1
    cur.execute('SELECT pessoa_numero_cc FROM funcionario WHERE id_funcionario = %s', (medico_id,))
    medico_cc = cur.fetchone()
    cur.execute(
        'INSERT INTO cirurgia (id_cirurgia, tipo, data_cirurgia, preco, paciente_pessoa_numero_cc, especialidade_id_especialidade, fatura_id_despesa, medico_funcionario_pessoa_numero_cc, internamento_id_internamento) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id_cirurgia',
        (novo_id, tipo, data, preco, paciente_cc, id_especialidade, fatura_id, medico_cc, id_internamento))
    return novo_id


@app.route('/dbproj/surgery/<int:id_internamento>', methods=['POST'])
@jwt_required()
def adicionar_cirurgia(id_internamento):
    usuario = get_jwt_identity()
    conn = db_connection()
    cur = conn.cursor()
    cur.execute('SELECT * FROM assistente WHERE funcionario_pessoa_numero_cc = %s', (usuario,))
    assistente_existe = cur.fetchone()
    conn.close()
    if not assistente_existe:
        return jsonify({"msg": "Apenas assistentes podem criar cirurgias"}), 400
    payload = flask.request.get_json()
    requesitos = ['paciente_cc', 'medico_id', 'enfermeiros', 'tipo', 'data', 'preco', 'id_especialidade']
    falta = [elemento for elemento in requesitos if elemento not in payload]

    if falta:
        resposta = {
            'status': StatusCodes['api_error'],
            'results': f'Faltam os seguintes parâmetros: {", ".join(falta)}'
        }
        return flask.jsonify(resposta)

    if conflito_horarios_medico(payload['medico_id'], payload['data'], cur) == 0:
        return jsonify({"msg": "O médico não tem disponibilidade nesse horário"}), 400

    if conflito_horarios_paciente(payload['paciente_cc'], payload['data'], cur) == 0:
        return jsonify({"msg": "O paciente não tem disponibilidade nesse horário"}), 400

    for enfermeiro in payload['enfermeiros']:
        if conflito_horarios_enfermeiros(enfermeiro['id'], payload['data'], cur) == 0:
            return jsonify(
                {"msg": f"O enfermeiro com o id {enfermeiro['id']} não tem disponibilidade nesse horário"}), 400

    try:
        conn = db_connection()
        cur = conn.cursor()
        cur.execute('SELECT fatura_id_despesa FROM internamento WHERE id_internamento = %s', (id_internamento,))
        fatura_id = cur.fetchone()
        cur.execute('SELECT montante FROM fatura WHERE id_despesa = %s', (fatura_id,))
        montante = cur.fetchone()
        preco_total = montante[0] + payload['preco']
        cur.execute('UPDATE fatura SET montante = %s WHERE id_despesa = %s', (preco_total, fatura_id))
        cirurgia_id = criar_cirurgia(id_internamento, payload['tipo'], payload['data'], payload['preco'],
                                     payload['paciente_cc'], payload['id_especialidade'], fatura_id,
                                     payload['medico_id'], cur, payload)
        for enfermeiro in payload['enfermeiros']:
            criar_enfermeiro_cirurgia(enfermeiro['id'], cirurgia_id, cur)
        conn.commit()
        resposta = {"status": StatusCodes['success'],
                    "results": {
                        "internamento_id": id_internamento,
                        "cirurgia_id": cirurgia_id,
                        "paciente_cc": payload['paciente_cc'],
                        "medico_id": payload['medico_id']}
                    }
    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(f'POST /dbproj/surgery/{id_internamento} - error: {error}')
        resposta = {'status': StatusCodes['internal_error'], 'errors': str(error)}
        conn.rollback()
    finally:
        if conn is not None:
            conn.close()
    return flask.jsonify(resposta)


def criar_internamento(inicio, preco, fatura_id_despesa, paciente_cc, assistente_cc, id_enfermeiro, cur):
    conn = db_connection()
    cur.execute('SELECT pessoa_numero_cc FROM funcionario WHERE id_funcionario = %s', (id_enfermeiro,))
    enfermeiro_cc = cur.fetchone()
    cur.execute("SELECT MAX(id_internamento) FROM internamento")
    ultimo_id_internamento = cur.fetchone()[0]
    novo_id = 1 if ultimo_id_internamento is None else ultimo_id_internamento + 1
    cur.execute(
        "INSERT INTO internamento (id_internamento, inicio, terminado, preco, fatura_id_despesa, paciente_pessoa_numero_cc, assistente_funcionario_pessoa_numero_cc,enfermeiro_funcionario_pessoa_numero_cc) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
        (novo_id, inicio, False, preco, fatura_id_despesa, paciente_cc, assistente_cc, enfermeiro_cc))
    conn.commit()
    conn.close()
    return novo_id


def criar_cirurgia_internamento(data, preco, tipo, id_especialidade, id_fatura, paciente_cc,
                                assistente_funcionario_pessoa_numero_cc, id_medico, id_internamento, cur, payload):
    cur.execute("SELECT MAX(id_cirurgia) FROM cirurgia")
    ultimo_id = cur.fetchone()[0]
    novo_id = 1 if ultimo_id is None else ultimo_id + 1
    cur.execute('SELECT pessoa_numero_cc FROM funcionario WHERE id_funcionario = %s', (id_medico,))
    medico_cc = cur.fetchone()
    cur.execute(
        'INSERT INTO cirurgia (id_cirurgia, tipo, data_cirurgia, preco, paciente_pessoa_numero_cc, especialidade_id_especialidade, fatura_id_despesa, medico_funcionario_pessoa_numero_cc, internamento_id_internamento) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) ',
        (novo_id, tipo, data, preco, paciente_cc, id_especialidade, id_fatura, medico_cc, id_internamento))
    return novo_id


@app.route('/dbproj/surgery', methods=['POST'])
@jwt_required()
def adicionar_cirurgia_internamento():
    usuario = get_jwt_identity()
    conn = db_connection()
    cur = conn.cursor()
    cur.execute('SELECT * FROM assistente WHERE funcionario_pessoa_numero_cc = %s', (usuario,))
    assistente_existe = cur.fetchone()
    conn.close()
    if not assistente_existe:
        return jsonify({"msg": "Apenas assistentes podem criar cirurgias"}), 400
    payload = flask.request.get_json()
    requesitos = ['paciente_cc', 'medico_id', 'enfermeiros', 'tipo', 'data', 'preco', 'id_especialidade']
    falta = [elemento for elemento in requesitos if elemento not in payload]
    if falta:
        resposta = {
            'status': StatusCodes['api_error'],
            'results': f'Faltam os seguintes parâmetros: {", ".join(falta)}'
        }
        return flask.jsonify(resposta)
    conn = db_connection()
    cur = conn.cursor()
    if conflito_horarios_medico(payload['medico_id'], payload['data'], cur) == 0:
        return jsonify({"msg": "O médico não tem disponibilidade nesse horário"}), 400

    if conflito_horarios_paciente(payload['paciente_cc'], payload['data'], cur) == 0:
        return jsonify({"msg": "O paciente não tem disponibilidade nesse horário"}), 400

    for enfermeiro in payload['enfermeiros']:
        if conflito_horarios_enfermeiros(enfermeiro['id'], payload['data'], cur) == 0:
            return jsonify(
                {"msg": f"O enfermeiro com o id {enfermeiro['id']} não tem disponibilidade nesse horário"}), 400

    try:
        id_enfermeiro_chefe = 0
        for enfermeiro in payload['enfermeiros']:
            cur.execute('SELECT pessoa_numero_cc FROM funcionario WHERE id_funcionario = %s', (enfermeiro["id"],))
            enfermeiro_cc = cur.fetchone()
            cur.execute('SELECT cat_herarquica FROM enfermeiro WHERE funcionario_pessoa_numero_cc = %s',
                        (enfermeiro_cc[0],))
            enfermeiro_funcao = cur.fetchone()
            if enfermeiro_funcao[0] == 'enfermeiro-chefe':
                id_enfermeiro_chefe = enfermeiro['id']
        if id_enfermeiro_chefe == 0:
            return jsonify(
                {"msg": f"Não foi referido nenhum ID de um enfermeiro-chefe"}), 400
        fatura_id = criar_fatura(payload['preco'], payload['paciente_cc'], cur)
        internamento_id = criar_internamento(payload['data'], payload['preco'], fatura_id, payload['paciente_cc'],
                                             usuario, id_enfermeiro_chefe, cur)
        cirurgia_id = criar_cirurgia_internamento(payload['data'], payload['preco'], payload['tipo'],
                                                  payload['id_especialidade'], fatura_id, payload['paciente_cc'],
                                                  usuario, payload['medico_id'], internamento_id, cur, payload)
        for enfermeiro in payload['enfermeiros']:
            criar_enfermeiro_cirurgia(enfermeiro['id'], cirurgia_id, cur)
        conn.commit()
        resposta = {"status": StatusCodes['success'],
                    "results": {
                        "internamento_id": internamento_id,
                        "cirurgia_id": cirurgia_id,
                        "paciente_cc": payload['paciente_cc'],
                        "medico_id": payload['medico_id'],
                        "enfermeiro_chefe_id": id_enfermeiro_chefe}
                    }
    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(f'POST /dbproj/surgery - error: {error}')
        resposta = {'status': StatusCodes['internal_error'], 'errors': str(error)}
        conn.rollback()
    finally:
        if conn is not None:
            conn.close()
    return flask.jsonify(resposta)


@app.route('/dbproj/report', methods=['GET'])
@jwt_required()
def imprimir_resumo_mensal():
    usuario = get_jwt_identity()
    conn = db_connection()
    cur = conn.cursor()
    cur.execute('SELECT * FROM assistente WHERE funcionario_pessoa_numero_cc = %s', (usuario,))
    assistente_existe = cur.fetchone()
    if not assistente_existe:
        return jsonify({"msg": "Apenas assistentes podem visualizar o sumário mensal"}), 400
    try:
        data_atual = datetime.datetime.now()
        ano_atual = data_atual.year
        mes_atual = data_atual.month
        resposta = []
        for i in range(12):
            mes = mes_atual - i
            ano = ano_atual
            if mes <= 0:
                mes += 12
                ano -= 1
            nome_mes = month_name[mes]

            cur.execute('''
                       SELECT medico_funcionario_pessoa_numero_cc, COUNT(*) AS total_cirurgias
                       FROM cirurgia
                       WHERE EXTRACT(MONTH FROM data_cirurgia) = %s AND EXTRACT(YEAR FROM data_cirurgia) = %s
                       GROUP BY medico_funcionario_pessoa_numero_cc
                       ORDER BY total_cirurgias DESC
                       LIMIT 1
                   ''', (mes, ano))

            linhas = cur.fetchone()

            if linhas:
                medico_cc = linhas[0]
                total_cirurgias = linhas[1]
                cur.execute('SELECT id_funcionario FROM funcionario WHERE pessoa_numero_cc = %s', (medico_cc,))
                nome_id = cur.fetchone()[0]
                resposta.append({'mes': f"{nome_mes} {ano}", 'medico': nome_id, 'cirurgias': total_cirurgias})

        return jsonify({'status': StatusCodes['success'], 'resultados': resposta})

    except Exception as error:
        logger.error(f'GET /dbproj/report - error: {error}')
        resposta = {'status': StatusCodes['internal_error'], 'errors': str(error)}
        conn.rollback()

    finally:
        if conn is not None:
            conn.close()
        return flask.jsonify(resposta)

if __name__ == '__main__':
    logging.basicConfig(filename='log_file.log')
    logging.basicConfig(filename='log_file.log')
    logger = logging.getLogger('logger')
    logger.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s [%(levelname)s]:  %(message)s', '%H:%M:%S')
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    host = '127.0.0.1'
    port = 8080
    app.run(host=host, debug=True, threaded=True, port=port)
    logger.info(f'API v1.0 online: http://{host}:{port}')