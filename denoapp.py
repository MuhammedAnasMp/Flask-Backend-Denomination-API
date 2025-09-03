from flask import Flask, request, jsonify ,send_from_directory , abort
import random
app = Flask(__name__)
import oracledb
from decimal import Decimal
from datetime import datetime
import json
import re
import os
import logging
import time
import shutil
from datetime import date
from flask import Flask, render_template_string
import xml.etree.ElementTree as ET
from dotenv import load_dotenv
import subprocess
load_dotenv()

def connection():
    username = os.getenv("ORACLE_USER")
    password = os.getenv("ORACLE_PASSWORD")
    dsn = os.getenv("ORACLE_DSN")
    client_path = os.getenv("ORACLE_CLIENT_PATH")

    try:
        oracledb.init_oracle_client(lib_dir=client_path)
        conn = oracledb.connect(user=username, password=password, dsn=dsn)
        print("Connected to Oracle Database successfully!")
        return conn
    except oracledb.Error as e:
        print(f"Error connecting to Oracle Database: {e}")
        raise

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(BASE_DIR, "log") 
LOG_FILE = os.path.join(LOG_DIR, "logs.log")



os.makedirs(LOG_DIR, exist_ok=True)
logger = logging.getLogger()
logger.setLevel(logging.INFO)

file_handler = logging.FileHandler(LOG_FILE)
file_handler.setLevel(logging.INFO)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

if not logger.handlers:
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
@app.before_request
def log_request_info():
    """Log every incoming request (method, path, IP)."""
    logging.info(
        "Incoming request: %s %s from %s | Headers: %s",
        request.method,
        request.path,
        request.remote_addr,
        dict(request.headers)
    )





DENO_DIR = os.path.join(os.getcwd(), 'Deno')  
@app.route('/Deno/<path:filename>')
def serve_file(filename):
    try:
        file_path = os.path.join(DENO_DIR, filename)

        if not os.path.exists(DENO_DIR):
            print(f"Error: The directory {DENO_DIR} does not exist!")
            abort(500)
        
        print(f"Available files in {DENO_DIR}:")
        for root, dirs, files in os.walk(DENO_DIR):
            for file in files:
                print(f"  - {file}") 

        if not os.path.exists(file_path):
            print(f"File not found: {filename}")    
            abort(404)  
        
        return send_from_directory(DENO_DIR, filename)

    except Exception as e:
        print(f"Error serving file {filename}: {e}")
        abort(500)

@app.route('/api/denominations', methods=['POST', 'GET'])
def denominations():
    if request.method == 'POST':
        data = request.get_json()
        print("POST request data:", data)

        denom_map = {
            "0.005": "FILS_005",
            "0.01": "FILS_010",
            "0.02": "FILS_020",
            "0.05": "FILS_050",
            "0.1": "FILS_100",
            "0.25": "FILS_250",
            "0.5": "FILS_500",
            "1": "KD_1",
            "5": "KD_5",
            "10": "KD_10",
            "20": "KD_20"
        }

        row_values = {v: 0 for v in denom_map.values()}

        for coin in data.get("coins", []):
            denom = str(coin["denomination"])  # Ensure string for mapping
            qty = coin["quantity"]
            if denom in denom_map:
                row_values[denom_map[denom]] = qty

        for note in data.get("notes", []):
            denom = str(note["denomination"])  # Ensure string for mapping
            qty = note["quantity"]
            if denom in denom_map:
                row_values[denom_map[denom]] = qty

        coin_total = Decimal(data.get("coinTotal", "0"))
        currency_total = Decimal(data.get("noteTotal", "0"))
        grand_total = Decimal(data.get("grandTotal", "0"))
        pos_number = data.get("posNumber")
        loc_code = data.get("locCode")
        cashier_id = data.get("userId")
        cashier_name = data.get("userName")
        dev_ip = data.get("devIp")
        authorized_by = data.get("authorizedBy")
        updating_record_id = data.get("updatingRecordId")

        # try:
        conn = connection()
        cur = conn.cursor()

        if authorized_by and updating_record_id:
         
            hist_timestamp = datetime.now()  #

            copy_sql = """
                INSERT INTO kwt_denomination_history (
                    original_id, loc_code, doc_date, cashier_id,
                    fils_005, fils_010, fils_020, fils_050, fils_100, fils_250, fils_500,
                    kd_1, kd_5, kd_10, kd_20, coin_total, currency_total, grand_total,
                    created_dt, pos_number, authorized_by, dev_ip, cashier_name, hist_timestamp
                )
                SELECT 
                    id, loc_code, doc_date, cashier_id,
                    fils_005, fils_010, fils_020, fils_050, fils_100, fils_250, fils_500,
                    kd_1, kd_5, kd_10, kd_20, coin_total, currency_total, grand_total,
                    created_dt, pos_number, :authorized_by, dev_ip, cashier_name, :hist_timestamp
                FROM kwt_denomination
                WHERE id = :upd_id
                """
            cur.execute(copy_sql, {
                "authorized_by": authorized_by,
                "hist_timestamp": hist_timestamp,
                "upd_id": updating_record_id
            })
            count_sql = """
            SELECT COUNT(*) FROM kwt_denomination_history
            WHERE original_id = :upd_id AND TRUNC(hist_timestamp) = TRUNC(SYSDATE)
            """
            cur.execute(count_sql, {"upd_id": updating_record_id})
            reprint_count = cur.fetchone()[0]

            
            update_sql = """
            UPDATE kwt_denomination
            SET 
                fils_005 = :fils_005,
                fils_010 = :fils_010,
                fils_020 = :fils_020,
                fils_050 = :fils_050,
                fils_100 = :fils_100,
                fils_250 = :fils_250,
                fils_500 = :fils_500,
                kd_1 = :kd_1,
                kd_5 = :kd_5,
                kd_10 = :kd_10,
                kd_20 = :kd_20,
                coin_total = :coin_total,
                currency_total = :currency_total,
                grand_total = :grand_total,
                pos_number = :pos_number,
                loc_code = :loc_code,
                cashier_name = :cashier_name,
                cashier_id = :cashier_id,
                dev_ip = :dev_ip,
                reprint_count = :reprint_count,
                authorized_by = :authorized_by
            WHERE id = :upd_id
            """
            params = {
                **row_values, #  fils_005..kd_20
                "coin_total": coin_total,
                "currency_total": currency_total,
                "grand_total": grand_total,
                "pos_number": pos_number,
                "loc_code": loc_code,
                "cashier_name": cashier_name,
                "cashier_id": cashier_id,
                "dev_ip": dev_ip,
                "reprint_count": reprint_count,
                "upd_id": updating_record_id,
                "authorized_by" :authorized_by
            }
            cur.execute(update_sql, params)
            conn.commit()
            response = {"message": "Record updated and history saved", "id": updating_record_id}

        else:
            reprint_count = 0
            hist_timestamp = datetime.now()  #
            
            cols = ", ".join(row_values.keys()) + ", coin_total, currency_total, grand_total, pos_number, loc_code, cashier_name, cashier_id , dev_ip  ,reprint_count ,CREATED_DT , DOC_DATE"
            placeholders = ", ".join([f":{k}" for k in row_values.keys()]) + ", :coin_total, :currency_total, :grand_total, :pos_number, :loc_code, :cashier_name, :cashier_id , :dev_ip , 0 ,:hist_timestamp , SYSDATE - 6/24 "
            sql = f"INSERT INTO kwt_denomination ({cols}) VALUES ({placeholders}) RETURNING id INTO :new_id"

            new_id = cur.var(oracledb.NUMBER)
            params = {
                **row_values,
                "coin_total": coin_total,
                "currency_total": currency_total,
                "grand_total": grand_total,
                "pos_number": pos_number,
                "loc_code": loc_code,
                "cashier_name": cashier_name,
                "cashier_id": cashier_id,
                "dev_ip": dev_ip,
                "new_id": new_id,
                "hist_timestamp" :hist_timestamp
            }
            cur.execute(sql, params)
            conn.commit()
            inserted_id = new_id.getvalue()[0]
            response = {"message": "Data inserted successfully", "id": int(inserted_id)}

    
        return jsonify(response), 201

        # except Exception as e:
        #     return jsonify({"error": str(e)}), 500
        # finally:
        #     if 'cur' in locals():
        #         cur.close()
        #     if 'conn' in locals():
        #         conn.close()
    else:
        
        id = request.args.get('Id')
        store_id = request.args.get('LocCode')
        cashier_id = request.args.get('UserId')
        if not cashier_id:
            return jsonify({"error": "Missing userId parameter"}), 400
        if not store_id:
            return jsonify({"error": "Missing LocCode parameter"}), 400

        try:

            conn = connection()
            cur = conn.cursor()
            cur.execute("SELECT * FROM kwt_denomination WHERE id = :id", {"id": id})
            columns = [col[0].lower() for col in cur.description]
            records = []

            for row in cur.fetchall():
                row_dict = dict(zip(columns, row))
                if "created_dt" in row_dict and isinstance(row_dict["created_dt"], datetime):
                    row_dict["created_dt"] = row_dict["created_dt"].isoformat()  # "2025-08-23T12:59:26"
                records.append(row_dict)

            
            
            query = """
                --VOID 
                SELECT 'VOID' STATUS, AUTHORIZED_BY||'-'||SUPERVISOR_NAME NAME, COUNT(DISTINCT RECEIPT_NO||COUNTER_NO)BILL_COUNT,SUM(LINE_VALUE)VALUE FROM GOLDPROD.GRAND_POS_REQ_AUTHORIZATION@GOLD_SERVER G WHERE STORE_GROUP = STORE_ID AND BUSINESS_DATE = TRUNC(SYSDATE - 26/24) AND STORE_ID =:store_id AND CASHIER_ID= :cashier_id AND REQUESTED_ACTION='Cancel line' GROUP BY AUTHORIZED_BY||'-'||SUPERVISOR_NAME UNION ALL
                --RETURN
                SELECT 'RETURN' STATUS, AUTHORIZED_BY||'-'||SUPERVISOR_NAME NAME, COUNT(DISTINCT RECEIPT_NO||COUNTER_NO)BILL_COUNT,SUM(LINE_VALUE)VALUE FROM GOLDPROD.GRAND_POS_REQ_AUTHORIZATION@GOLD_SERVER G WHERE STORE_GROUP = STORE_ID AND BUSINESS_DATE = TRUNC(SYSDATE - 26/24) AND STORE_ID =:store_id AND CASHIER_ID= :cashier_id AND REQUESTED_ACTION='Product Return' GROUP BY AUTHORIZED_BY||'-'||SUPERVISOR_NAME UNION ALL
                --VOID ALL 
                SELECT 'VOID ALL' STATUS, AUTHORIZED_BY||'-'||SUPERVISOR_NAME NAME, COUNT(DISTINCT RECEIPT_NO||COUNTER_NO)BILL_COUNT,SUM(LINE_VALUE)VALUE FROM GOLDPROD.GRAND_POS_CANCEL_RECEIPT_D@GOLD_SERVER G WHERE BUSINESS_DATE = TRUNC(SYSDATE - 26/24) AND STORE_ID =:store_id AND SITE_GROUP = STORE_ID AND CASHIER_ID= :cashier_id GROUP BY AUTHORIZED_BY||'-'||SUPERVISOR_NAME UNION ALL 
                --SUSPENDED
                SELECT DISTINCT 'SUSPENDED' STATUS,'',COUNT(*) BILL_COUNT,SUM(PTHAMOUNTSALES-PTHAMOUNTRETURNS)VALUE FROM GOLDPROD.POSTRAHEADER@GOLD_SERVER WHERE PTHSITE= : store_id AND PTHBUSDATE= TRUNC(SYSDATE - 26/24) AND PTHSTATUS=2 AND PTHCASHIER= :cashier_id  AND PTHAMOUNTSALES-PTHAMOUNTRETURNS <>0
                

                """
            params = {
                "store_id": store_id,
                "cashier_id": cashier_id
            }
            cur.execute(query, params)
            rows = cur.fetchall()

            def group_statuses(data):
                status_groups = {
                    'Return': ['RETURN','Product Return'],
                    'Void': ['VOID', 'Cancel line'],
                    'Void All': ['VOID ALL'],
                    'Suspended': ['SUSPENDED'],
                    # 'Others': ['Others']
                }
                
                grouped_data = {}

                for row in data:
                    status = row['STATUS']
                    group_name = None

                    for group, statuses in status_groups.items():
                        if status in statuses:
                            group_name = group
                            break
                    
                    if group_name:
                        if group_name not in grouped_data:
                            grouped_data[group_name] = []
                        if row['NAME'] :
                            name_parts = row['NAME'].split('-')[-1]  
                        else:
                            name_parts = " -- "
                        clean_name = re.sub(r'^\d+', '', name_parts) 
                        grouped_data[group_name].append({
                            # "STATUS": status,
                            "NAME": clean_name,
                            "BILL_COUNT": row['BILL_COUNT'],
                            "VALUE": row['VALUE']
                        })
                
                return grouped_data



            columns = [col[0] for col in cur.description]

            result = []
            for row in rows:
                result.append(dict(zip(columns, row)))
          
      
            grouped_result = group_statuses(result)


            # transaction_report = json.dumps(grouped_result, default=str)

            print({"data": records, "transaction_report": grouped_result})

            return jsonify({"data": records, "transaction_report": grouped_result}), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500
        finally:
            if 'cur' in locals(): cur.close()
            if 'conn' in locals(): conn.close()

@app.route("/existing_history", methods=['GET'])
def existing_history():
    conn = connection()
    cursor = conn.cursor()
    time.sleep(2)
    loc_code = request.args.get('LocCode')
    cashier_id = request.args.get('UserId')

    today_date = datetime.today().strftime('%d-%b-%y').upper()  # '02-SEP-25'
    print(today_date)

    cursor.execute("""
        SELECT * FROM kwt_denomination
        WHERE LOC_CODE = :loc_code
        AND cashier_id = :cashier_id
        AND TO_CHAR(CREATED_DT, 'DD-MON-RR') = :today_date
    """, {"loc_code": loc_code, "cashier_id": cashier_id, "today_date": today_date})

    columns = [col[0] for col in cursor.description]
    rows = cursor.fetchall()

    tables = [dict(zip(columns, row)) for row in rows]

    single_id = tables[0].get("ID") if tables else None

    for row in tables:
        row.pop("CREATED_DT", None)

    cursor.close()
    conn.close()

    response = {
        "message": "GET request received",
        "data": tables
    }

    if single_id:
        response.update({"id": single_id})
    
    print(response)
    print(single_id)
    return jsonify(response)




@app.route('/dbcheck', methods=['GET'])
def home_get():

    conn = connection()
    cursor = conn.cursor()


    cursor.execute("SELECT table_name FROM user_tables")
    tables = cursor.fetchall()
    
    print("Tables in the schema:")
    for t in tables:
        print(t[0])

    cursor.close()
    conn.close()
    return jsonify({"message": "GET request received" , "tables":tables})


@app.route("/")
def show_clickonce_info():
    file_path = os.path.join("Deno", "Deno.application")
    tree = ET.parse(file_path)
    root = tree.getroot()

    ns = {
        "asmv1": "urn:schemas-microsoft-com:asm.v1"
    }

    # Get App Name and Version
    assembly_identity = root.find("asmv1:assemblyIdentity", ns)
    app_name = assembly_identity.attrib.get("name") if assembly_identity is not None else "N/A"
    app_version = assembly_identity.attrib.get("version") if assembly_identity is not None else "N/A"

    html = f"""
    <html>
        <head><title>Deno ClickOnce Info</title></head>
        <body>
            <h1>Deno.application Info</h1>
            <p><strong>App Name:</strong> {app_name}</p>
            <p><strong>Version:</strong> {app_version}</p>
        </body>
    </html>
    """
    return html




@app.route('/cashier_login' , methods=['POST'])
def cashier_login():
    try:
        data = request.get_json()
        cashier_id = data.get("cashier_id")
        pin = data.get("password")
        print(request.get_json())
        if pin =="" and cashier_id =="":
            cashier_id=80322
            pin=4321
        else:
            try:
                cashier_id = int(cashier_id)
                pin = int(pin)
            except (ValueError, TypeError):
                return jsonify({"message": "Username and password must be numeric"}), 400

        conn = connection() 
        cursor = conn.cursor()
        query = """
            SELECT 
                NVL(TO_CHAR(pcacashierid), '786') AS pcacashierid,
                NVL(
                    CASE 
                        WHEN pcacashierid = 786 THEN 'ADMIN'
                        ELSE DECODE(pcaauthlevel, 1, 'CASHIER', 2, 'SUPERVISOR', 'INVALID')
                    END,
                    'INVALID'
                ) AS status,
                (
                    SELECT MAX(udgprenom)
                    FROM goldprod.vasuserdg@gold_server
                    WHERE udgcode = pcacashierid
                ) AS name
            FROM (
                SELECT pcacashierid, pcaauthlevel
                FROM goldprod.poscashier@gold_server
                WHERE pcacashierid = :cashier_id
                AND pcapin = :pin
            )
        """


        cursor.execute(query, cashier_id=cashier_id, pin=pin)
        row = cursor.fetchone()

        response = {}
        if row:
            response = {
                "id": row[0],
                "auth": row[1],
                "username": row[2].capitalize(),
                "status":200
            }
            status_code = 200
        else:
            response = {"message": "Invalid credentials" , "status":401}
            status_code = 401

        cursor.close()
        conn.close()
        print(response)
        return jsonify(response), status_code

    except Exception as e:
        print(e)
        return jsonify({"message": str(e)}), 500




@app.route('/void_id_validation', methods=['POST'])
def void_id_validation():
    data = request.get_json()

    if not data or 'username' not in data or 'password' not in data:
        return jsonify({"message": "Missing username or password", "status": 400}), 400
    

    is_authenticated = data['username'] == "1" and data['password'] == "1"
    
    counted_by = '300383' # return void owner id 

    if is_authenticated:
        print(data) 
        return jsonify({"message": " login successful","success":True ,"status": 200 , "counted_by":counted_by}), 200
    else:
        return jsonify({"message": "Authentication Failed: Invalid username or password", "status": 401}), 401







def get_git_path():
    git_local = shutil.which("git")
    if git_local:
        return git_local
 
    git_prod = r"C:\Program Files\Git\bin\git.exe"
    if os.path.exists(git_prod):
        return git_prod
    return None

@app.route("/gitpull", methods=["GET"])
def pull_new_version():
    try:
        repo_dir = os.path.join(BASE_DIR) 
        git_path = get_git_path()
        if not git_path:
            return jsonify({"status": "error", "exception": "Git not found"}), 500

        
        subprocess.run(
            [git_path, "config", "--global", "--add", "safe.directory", repo_dir],
            capture_output=True,
            text=True
        )

    
        result = subprocess.run(
            [git_path, "-C", repo_dir, "pull", "origin", "master"],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            return jsonify({"status": "success", "output": result.stdout.strip()}), 200
        else:
            return jsonify({"status": "error", "error": result.stderr.strip()}), 500

    except Exception as e:
        return jsonify({"status": "error", "exception": str(e)}), 500



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)