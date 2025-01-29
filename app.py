from flask import Flask, jsonify, request
import mysql.connector
import os
import re
from dotenv import load_dotenv
from flask_cors import CORS  # Opcional para CORS

load_dotenv()

app = Flask(__name__)
CORS(app)  # Opcional: Habilitar CORS para desarrollo

# Configuración de la base de datos
DB_CONFIG = {
    'user': os.environ.get('MYSQL_USER'),
    'password': os.environ.get('MYSQL_PASSWORD'),
    'host': os.environ.get('MYSQL_HOST'),
    'database': os.environ.get('MYSQL_DATABASE'),
    'port': int(os.environ.get('MYSQL_PORT', 3306)),
    'ssl_ca': os.environ.get('MYSQL_SSL_CA') or None
}

# Helper para conexiones a la BD
def get_db_connection():
    return mysql.connector.connect(**DB_CONFIG)

# Endpoint 1: Consultar proveedores
@app.route('/cons_prov', methods=['GET'])
def consultar_proveedores():
    try:
        conexion = get_db_connection()
        cursor = conexion.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT idprov, nom_emp, ruc, nom_per, telefono, 
                   correo, direccion, cond_pago, comp_gener 
            FROM proveedores
        """)
        
        resultados = cursor.fetchall()
        cursor.close()
        conexion.close()
        
        return jsonify({'proveedores': resultados, 'total': len(resultados)}), 200
    
    except mysql.connector.Error as err:
        return jsonify({'error': f'Error MySQL: {err}'}), 500
    except Exception as e:
        return jsonify({'error': f'Error general: {str(e)}'}), 500

# Endpoint 2: Actualizar proveedor
@app.route('/act_prov/<int:idprov>', methods=['PUT'])
def actualizar_proveedor(idprov):
    try:
        datos = request.get_json()
        if not datos:
            return jsonify({'error': 'Sin datos para actualizar'}), 400
        
        # Validación básica de RUC
        if 'ruc' in datos:
            if len(datos['ruc']) != 11 or not datos['ruc'].isdigit():
                return jsonify({'error': 'RUC inválido'}), 400
        
        campos_permitidos = [
            'nom_emp', 'ruc', 'nom_per', 'telefono',
            'correo', 'direccion', 'cond_pago', 'comp_gener'
        ]
        
        campos_actualizar = []
        valores = []
        for campo, valor in datos.items():
            if campo in campos_permitidos:
                campos_actualizar.append(f"{campo} = %s")
                valores.append(valor.strip() if isinstance(valor, str) else valor)
        
        if not campos_actualizar:
            return jsonify({'error': 'No hay campos válidos para actualizar'}), 400
        
        valores.append(idprov)
        
        conexion = get_db_connection()
        cursor = conexion.cursor()
        
        query = f"UPDATE proveedores SET {', '.join(campos_actualizar)} WHERE idprov = %s"
        cursor.execute(query, valores)
        
        if cursor.rowcount == 0:
            return jsonify({'error': 'Proveedor no encontrado'}), 404
        
        conexion.commit()
        
        # Obtener datos actualizados
        cursor = conexion.cursor(dictionary=True)
        cursor.execute("SELECT * FROM proveedores WHERE idprov = %s", (idprov,))
        proveedor_actualizado = cursor.fetchone()
        
        cursor.close()
        conexion.close()
        
        return jsonify({
            'mensaje': 'Proveedor actualizado',
            'proveedor': proveedor_actualizado
        }), 200
        
    except mysql.connector.IntegrityError as err:
        return jsonify({'error': f'Error de integridad: {err}'}), 400
    except mysql.connector.Error as err:
        return jsonify({'error': f'Error MySQL: {err}'}), 500
    except Exception as e:
        return jsonify({'error': f'Error general: {str(e)}'}), 500

# Endpoint 3: Crear proveedor
@app.route('/prov', methods=['POST'])
def crear_proveedor():
    try:
        datos = request.get_json()
        
        # Validar campos requeridos
        campos_requeridos = {'nom_emp': 'Nombre de empresa', 'ruc': 'RUC'}
        for campo, nombre in campos_requeridos.items():
            if campo not in datos or not datos[campo].strip():
                return jsonify({'error': f'{nombre} es requerido'}), 400
        
        # Validar formato RUC
        if len(datos['ruc']) != 11 or not datos['ruc'].isdigit():
            return jsonify({'error': 'RUC debe tener 11 dígitos numéricos'}), 400
        
        # Validar formato email
        if 'correo' in datos and datos['correo']:
            if not re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', datos['correo']):
                return jsonify({'error': 'Formato de email inválido'}), 400
        
        # Preparar datos
        campos_permitidos = [
            'nom_emp', 'ruc', 'nom_per', 'telefono',
            'correo', 'direccion', 'cond_pago', 'comp_gener'
        ]
        
        datos_proveedor = {
            k: v.strip() if isinstance(v, str) else v
            for k, v in datos.items()
            if k in campos_permitidos and v not in [None, '']
        }
        
        conexion = get_db_connection()
        cursor = conexion.cursor()
        
        columnas = ', '.join(datos_proveedor.keys())
        placeholders = ', '.join(['%s'] * len(datos_proveedor))
        
        cursor.execute(
            f"INSERT INTO proveedores ({columnas}) VALUES ({placeholders})",
            list(datos_proveedor.values())
        )
        
        id_nuevo = cursor.lastrowid
        conexion.commit()
        
        # Obtener registro creado
        cursor = conexion.cursor(dictionary=True)
        cursor.execute("SELECT * FROM proveedores WHERE idprov = %s", (id_nuevo,))
        nuevo_proveedor = cursor.fetchone()
        
        cursor.close()
        conexion.close()
        
        return jsonify({
            'mensaje': 'Proveedor creado exitosamente',
            'proveedor': nuevo_proveedor
        }), 201
        
    except mysql.connector.IntegrityError as err:
        return jsonify({'error': 'RUC ya existe en la base de datos'}), 409
    except mysql.connector.Error as err:
        return jsonify({'error': f'Error MySQL: {err}'}), 500
    except Exception as e:
        return jsonify({'error': f'Error general: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=os.environ.get('PORT', 5000))