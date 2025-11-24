from flask import Flask, request, jsonify ,send_from_directory , abort
import random
app = Flask(__name__)
import oracledb
from decimal import Decimal
from datetime import datetime,timedelta
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
from pyfiglet import figlet_format
import threading
load_dotenv()
from flask import Flask, request, g
DEBUG = os.getenv("DEBUG", "False").lower() == "true"

import requests





back_days = 0


import sys
debug_arg = None
for arg in sys.argv[1:]:
    if arg.lower().startswith("debug="):
        debug_arg = arg.split("=", 1)[1].lower()


if debug_arg is not None:
    DEBUG = debug_arg == "true"
else:
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"

text = "DEVELOPMENT" if DEBUG else "PRODUCTION"
banner = figlet_format(text, font="slant")
print(banner)
KWT_DENOMINATION_TABLE = "KWT_DENOMINATION_TEST" if DEBUG else "KWT_DENOMINATION"
KWT_DENOMINATION_HISTORY_TABLE = "KWT_DENOMINATION_HISTORY_TEST" if DEBUG else "KWT_DENOMINATION_HISTORY"
import socket

def get_server_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # connect to any public IP (not actually sending data)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    finally:
        s.close()
    return ip
def get_environment():
    ip = get_server_ip()
    if ip == "172.16.4.167":
        return "test"
    elif ip == "172.16.4.253":
        return "production"
    else:
        return "unknown"

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


# Log request info
@app.before_request
def log_request_info():
    try:
        body = request.get_json(silent=True)  # Try to parse JSON
        if body is None:
            body = request.form.to_dict() or request.data.decode("utf-8")
    except Exception:
        body = "<Could not parse body>"

    g.request_body = body  # store for logging response later

    logging.info("=== Incoming Request ===")
    logging.info("Method: %s", request.method)
    logging.info("Path: %s", request.path)
    logging.info("IP: %s", request.remote_addr)
    logging.info("Query Params: %s", dict(request.args))
    logging.info("Headers: %s", dict(request.headers))
    logging.info("Body: %s", json.dumps(body, indent=4, ensure_ascii=False))

# Log response info
@app.after_request
def log_response_info(response):
    try:
        content_type = response.content_type
        response_body = response.get_data(as_text=True)
        # If JSON, pretty print
        if "application/json" in content_type:
            response_body = json.dumps(json.loads(response_body), indent=4, ensure_ascii=False)
    except Exception:
        response_body = "<Could not parse response>"

    logging.info("=== Response ===")
    logging.info("Status: %s", response.status)
    logging.info("Headers: %s", dict(response.headers))
    logging.info("Body: %s", response_body)
    logging.info("=======================")
    return response




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









def send_data_async(store_id , cashier_id ,suspended_bills):
    
    conn = connection()
    cur = conn.cursor()

    try:
        query = "SELECT * FROM label_printers WHERE LBL_LOC_CODE = :store_id"
        cur.execute(query, {"store_id": store_id})
        row = cur.fetchone()
        if row:
            StoreName = row[0]  # first column
            print("StoreName from DB:", StoreName)

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
                
            )
        """


        cur.execute(query, cashier_id=cashier_id)
        row = cur.fetchone()

        response = {}
        if row and row[1].lower() != "invalid":
            CreatedByName = row[2].capitalize()
        


        url = "http://172.16.4.167:4000/send-data"
        data = {
        "StoreName": StoreName,
        "CreatedById": cashier_id,
        "CreatedByName": CreatedByName,
        "suspendedBills": suspended_bills
        }
        requests.post(url, json=data, timeout=1)  
        print(response.json())        
    except Exception as e:
        print(e)
    finally:
        cur.close()
        conn.close()


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
            denom = str(coin["denomination"])
            qty = coin["quantity"]
            if denom in denom_map:
                row_values[denom_map[denom]] = qty

        for note in data.get("notes", []):
            denom = str(note["denomination"]) 
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


        opening_amount = data.get("openingAmount")

      
        try:
            conn = connection()
            cur = conn.cursor()

            if authorized_by and updating_record_id:
            # trying to update one existing data (not printing)
                hist_timestamp = datetime.now()  #

                copy_sql = f"""
                    INSERT INTO {KWT_DENOMINATION_HISTORY_TABLE} (
                        original_id, loc_code, doc_date, cashier_id,
                        fils_005, fils_010, fils_020, fils_050, fils_100, fils_250, fils_500,
                        kd_1, kd_5, kd_10, kd_20, coin_total, currency_total, grand_total,
                         pos_number, authorized_by, dev_ip, cashier_name, hist_timestamp , opening_amount
                    )
                    SELECT 
                        id, loc_code, doc_date, cashier_id,
                        fils_005, fils_010, fils_020, fils_050, fils_100, fils_250, fils_500,
                        kd_1, kd_5, kd_10, kd_20, coin_total, currency_total, grand_total,
                         pos_number, :authorized_by, dev_ip, cashier_name, :hist_timestamp ,opening_amount
                    FROM {KWT_DENOMINATION_TABLE}
                    WHERE id = :upd_id 
                    """
                cur.execute(copy_sql, {
                    "authorized_by": authorized_by,
                    "hist_timestamp": hist_timestamp,
                    "upd_id": updating_record_id
                })


                count_sql = f"""
                SELECT COUNT(*) FROM {KWT_DENOMINATION_HISTORY_TABLE}
                WHERE original_id = :upd_id 
                
                """
                cur.execute(count_sql, {"upd_id": updating_record_id})
                reprint_count = cur.fetchone()[0] +1
                

                
                update_sql = f"""
                UPDATE {KWT_DENOMINATION_TABLE}
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
                    authorized_by = :authorized_by,
                    opening_amount = :opening_amount 

                WHERE id = :upd_id
                """
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
                    "reprint_count": reprint_count,
                    "upd_id": updating_record_id,
                    "authorized_by" :authorized_by,
                    "opening_amount" :opening_amount 
                }
                cur.execute(update_sql, params)
                conn.commit()
                response = {"message": "Record updated and history saved", "id": updating_record_id}

            else:
            # First time create  (not printing)
                reprint_count = 1
               
                current_date =  datetime.now() 
                cols = ", ".join(row_values.keys()) + ", coin_total, currency_total, grand_total, pos_number, loc_code, cashier_name, cashier_id , dev_ip  ,reprint_count ,CREATED_DT , DOC_DATE , opening_amount"
                placeholders = ", ".join([f":{k}" for k in row_values.keys()]) + ", :coin_total, :currency_total, :grand_total, :pos_number, :loc_code, :cashier_name, :cashier_id , :dev_ip , :reprint_count ,:current_date ,TRUNC(SYSDATE - 6/24)  ,:opening_amount"
                sql = f"INSERT INTO {KWT_DENOMINATION_TABLE} ({cols}) VALUES ({placeholders}) RETURNING id INTO :new_id"

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
                    "current_date" :current_date,
                    "opening_amount":opening_amount,
                    "reprint_count":reprint_count
                }
                cur.execute(sql, params)
                conn.commit()
                inserted_id = new_id.getvalue()[0]
                response = {"message": "Data inserted successfully", "id": int(inserted_id)}

        
            return jsonify(response), 201

        except Exception as e:
            return jsonify({"error": str(e)}), 500
        finally:
            if 'cur' in locals():
                cur.close()
            if 'conn' in locals():
                conn.close()
    else:
    # print denomination data is returnd by else case  
        id = request.args.get('Id')
        # id = 44
        store_id = request.args.get('LocCode')
        # store_id = 813
        cashier_id = request.args.get('UserId')
        # cashier_id = 8109
     
        if not cashier_id:
            return jsonify({"error": "Missing userId parameter"}), 400
        if not store_id:
            return jsonify({"error": "Missing LocCode parameter"}), 400

        try:
            records = []
            denom_row = {}
            conn = connection()
            cur = conn.cursor()
            
            cur.execute("""
                SELECT 
                    PTHCASHIER,
                    COUNT(DISTINCT CASE 
                                    WHEN PTHSUBTYPE = 0 
                                        AND PTHTYPE = 1 
                                        AND PTHSTATUS = 5 
                                        AND PTHAMOUNTSALES - PTHAMOUNTRETURNS <> 0 
                                    THEN TO_CHAR(PTHSTART,'HH24') 
                                END) AS SALES_HOURS,
                    SUM(CASE 
                        WHEN PTHSUBTYPE = 0 
                            AND PTHTYPE = 1 
                            AND PTHSTATUS = 5 
                            AND PTHAMOUNTSALES - PTHAMOUNTRETURNS <> 0 
                        THEN 1 
                        ELSE 0 
                        END) AS TOTAL_CUSTOMER,
                    TO_CHAR(MIN(CASE WHEN PTHSUBTYPE = 500 THEN PTHSTART END), 'DD-MON-YY HH24:MI:SS') AS LOGIN,
                    TO_CHAR(MAX(CASE WHEN PTHSUBTYPE = 0 
                                    AND PTHSTATUS = 5 
                                    AND PTHAMOUNTSALES - PTHAMOUNTRETURNS <> 0 
                                THEN PTHSTART END), 'DD-MON-YY HH24:MI:SS') AS LAST_SALE,
                    TO_CHAR(MAX(CASE WHEN PTHSUBTYPE = 400 THEN PTHSTART END), 'DD-MON-YY HH24:MI:SS') AS DECLARE,
                    TO_CHAR(MIN(CASE WHEN PTHSTATUS = 5 AND PTHAMOUNTSALES - PTHAMOUNTRETURNS <> 0 THEN PTHSTART END), 'DD-MON-YY HH24:MI:SS') AS FIRST_BILL,
                    TO_CHAR(MAX(CASE WHEN PTHSTATUS = 5 AND PTHAMOUNTSALES - PTHAMOUNTRETURNS <> 0 THEN PTHSTART END), 'DD-MON-YY HH24:MI:SS') AS LAST_BILL,
                    TO_CHAR(
                        TRUNC((MAX(CASE WHEN PTHSUBTYPE = 0 
                                        AND PTHSTATUS = 5 
                                        AND PTHAMOUNTSALES - PTHAMOUNTRETURNS <> 0 
                                    THEN PTHSTART END) - MIN(CASE WHEN PTHSUBTYPE = 500 THEN PTHSTART END)) * 24)
                    , 'FM00') || ':' ||
                    TO_CHAR(
                        TRUNC(MOD((MAX(CASE WHEN PTHSUBTYPE = 0 
                                            AND PTHSTATUS = 5 
                                            AND PTHAMOUNTSALES - PTHAMOUNTRETURNS <> 0 
                                        THEN PTHSTART END) -
                                MIN(CASE WHEN PTHSUBTYPE = 500 THEN PTHSTART END)) * 24 * 60, 60))
                    , 'FM00') AS HOURS_SPENT_IN_POS
                    FROM GOLDPROD.POSTRAHEADER@GOLD_SERVER
                    WHERE PTHSITE = :store_id
                    AND PTHBUSDATE = TRUNC(SYSDATE -(:back_days + 6/24))
                    AND PTHCASHIER = :cashier_id
                    GROUP BY PTHCASHIER
                """, {"store_id": store_id, "cashier_id": cashier_id , "back_days": back_days})

            bill_row = cur.fetchone()
            row_dict = {
                "cashier": bill_row[0] if bill_row and bill_row[0] is not None else "N/A",
                "sales_hours": bill_row[1] if bill_row and bill_row[1] is not None else 0,
                "total_customer": bill_row[2] if bill_row and bill_row[2] is not None else 0,
                "login": bill_row[3] if bill_row and bill_row[3] is not None else "N/A",
                "last_sale": bill_row[4] if bill_row and bill_row[4] is not None else "N/A",
                "declare": bill_row[5] if bill_row and bill_row[5] is not None else "N/A",
                "first_bill": bill_row[6] if bill_row and bill_row[6] is not None else "N/A",
                "last_bill": bill_row[7] if bill_row and bill_row[7] is not None else "N/A",
                "hours_spent_in_pos": bill_row[8] if bill_row and bill_row[8] is not None else "00:00"

            }



            cur.execute(f"SELECT * FROM {KWT_DENOMINATION_TABLE} WHERE id = :id", {"id": id})
            columns = [col[0].lower() for col in cur.description]

            for row in cur.fetchall():
                denom_row = dict(zip(columns, row))
                denom_row.update(row_dict)  
                if "created_dt" in denom_row and isinstance(denom_row["created_dt"], datetime):
                    denom_row["created_dt"] = denom_row["created_dt"].isoformat()
                records.append(denom_row)
          
            query = """
                --VOID 
                SELECT 'VOID' STATUS, AUTHORIZED_BY||'-'||SUPERVISOR_NAME NAME, COUNT(DISTINCT RECEIPT_NO||COUNTER_NO)BILL_COUNT,SUM(LINE_VALUE)VALUE FROM GOLDPROD.GRAND_POS_REQ_AUTHORIZATION@GOLD_SERVER G WHERE STORE_GROUP = STORE_ID AND BUSINESS_DATE = TRUNC(SYSDATE - (:back_days + 6/24)) AND STORE_ID =:store_id AND CASHIER_ID= :cashier_id AND REQUESTED_ACTION='Cancel line' GROUP BY AUTHORIZED_BY||'-'||SUPERVISOR_NAME UNION ALL
                --RETURN
                SELECT 'RETURN' STATUS, AUTHORIZED_BY||'-'||SUPERVISOR_NAME NAME, COUNT(DISTINCT RECEIPT_NO||COUNTER_NO)BILL_COUNT,SUM(LINE_VALUE)VALUE FROM GOLDPROD.GRAND_POS_REQ_AUTHORIZATION@GOLD_SERVER G WHERE STORE_GROUP = STORE_ID AND BUSINESS_DATE = TRUNC(SYSDATE - (:back_days + 6/24)) AND STORE_ID =:store_id AND CASHIER_ID= :cashier_id AND REQUESTED_ACTION='Product Return' GROUP BY AUTHORIZED_BY||'-'||SUPERVISOR_NAME UNION ALL
                --VOID ALL 
                SELECT 'VOID ALL' STATUS, AUTHORIZED_BY||'-'||SUPERVISOR_NAME NAME, COUNT(DISTINCT RECEIPT_NO||COUNTER_NO)BILL_COUNT,SUM(LINE_VALUE)VALUE FROM GOLDPROD.GRAND_POS_CANCEL_RECEIPT_D@GOLD_SERVER G WHERE BUSINESS_DATE = TRUNC(SYSDATE - (:back_days + 6/24)) AND STORE_ID =:store_id AND SITE_GROUP = STORE_ID AND CASHIER_ID= :cashier_id GROUP BY AUTHORIZED_BY||'-'||SUPERVISOR_NAME UNION ALL 
                --SUSPENDED
                SELECT DISTINCT 'SUSPENDED' STATUS,'',COUNT(*) BILL_COUNT,SUM(PTHAMOUNTSALES-PTHAMOUNTRETURNS)VALUE FROM GOLDPROD.POSTRAHEADER@GOLD_SERVER WHERE PTHSITE= : store_id AND PTHBUSDATE= TRUNC(SYSDATE - (:back_days + 6/24)) AND PTHSTATUS=2 AND PTHCASHIER= :cashier_id  AND PTHAMOUNTSALES-PTHAMOUNTRETURNS <>0
                
                """
            params = {
                "store_id": store_id,
                "cashier_id": cashier_id ,
                 "back_days": back_days
            }
            cur.execute(query, params)
            rows = cur.fetchall()

            def group_statuses(data):
                status_groups = {
                    'Return': ['RETURN','Product Return'],
                    'Void': ['VOID', 'Cancel line'],
                    'Void All': ['VOID ALL'],
                    'Suspended': ['SUSPENDED'],
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

            suspended_bills = []
          
            for summary_data in result:
                if summary_data.get('STATUS') == "SUSPENDED" and summary_data.get('BILL_COUNT')  > 0: 
                    print("i found one bill")
                    query = """
                    SELECT PTHCR as POS_NUMBER , PTHAMOUNTSALES as AMOUNT , PTHTXNUM as BILL_NUMBER , TO_CHAR(PTHEND, 'hh:mi AM') AS BILL_TIME FROM GOLDPROD.POSTRAHEADER@GOLD_SERVER WHERE PTHSITE= :store_id AND PTHBUSDATE= TRUNC(SYSDATE -(:back_days + 6/24)) AND PTHSTATUS=2 AND PTHCASHIER= :cashier_id  And pthmode =1 and pthstatus =2 and pthtype =1  AND PTHAMOUNTSALES-PTHAMOUNTRETURNS <>0 
                        """
                    params = {
                        "store_id": store_id,
                        "cashier_id": cashier_id,
                         "back_days": back_days
                    }
               
                    cur.execute(query, params)
                    rows = cur.fetchall()
                    columns = [col[0] for col in cur.description]

               
                    for row in rows:
                        print(row)
                        suspended_bills.append(dict(zip(columns, row)))
                    suspended_bills = sorted(suspended_bills, key=lambda x: x["BILL_NUMBER"])

                    threading.Thread(target=send_data_async, args=(store_id,cashier_id ,suspended_bills,), daemon=True).start() 
            return jsonify({"data": records, "transaction_report": grouped_result , "suspended_bills": suspended_bills }), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500
        finally:
            if 'cur' in locals(): cur.close()
            if 'conn' in locals(): conn.close()

@app.route("/existing_history", methods=['GET'])
def existing_history():
    conn = connection()
    cursor = conn.cursor()
    loc_code = request.args.get('LocCode')
    cashier_id = request.args.get('UserId')

    today_date = datetime.today().strftime('%d-%b-%y').upper()  # '02-SEP-25'


    # cursor.execute(f"""
    #     SELECT * FROM {KWT_DENOMINATION_TABLE}
    #     WHERE LOC_CODE = :loc_code
    #     AND cashier_id = :cashier_id
    #     AND TO_CHAR(DOC_DATE, 'DD-MON-RR') = :today_date
    # """, {"loc_code": loc_code, "cashier_id": cashier_id, "today_date": today_date})
    cursor.execute(f"""
        SELECT * FROM {KWT_DENOMINATION_TABLE}
        WHERE LOC_CODE = :loc_code
        AND cashier_id = :cashier_id
        AND TO_CHAR(DOC_DATE, 'DD-MON-RR') = TRUNC(SYSDATE-:back_days) 
    """, {"loc_code": loc_code, "cashier_id": cashier_id , "back_days": back_days})

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


# Convert version string to tuple for comparison
def version_to_tuple(version_str):
    try:
        parts = version_str.split(".")
        parts = [int(p) for p in parts]
        while len(parts) < 3:
            parts.append(0)
        return tuple(parts)
    except:
        return (0, 0, 0)

def version_to_int_tuple(ver_str):
    return tuple(int(x) for x in ver_str.split("."))

@app.route("/", methods=["GET", "POST"])
def show_clickonce_info():
    # --- Read local ClickOnce XML ---
    file_path = os.path.join("Deno", "Deno.application")
    tree = ET.parse(file_path)
    root = tree.getroot()

    ns = {"asmv1": "urn:schemas-microsoft-com:asm.v1"}
    assembly_identity = root.find("asmv1:assemblyIdentity", ns)
    app_name = assembly_identity.attrib.get("name") if assembly_identity is not None else "N/A"
    app_version = assembly_identity.attrib.get("version") if assembly_identity is not None else "N/A"

    if request.method == "POST":
        return jsonify({"app_name": app_name, "app_version": app_version})

    # --- Fetch DB entries ---
    conn = connection()
    cur = conn.cursor()
    cur.execute("""
       SELECT loc_code, loc_name, pos_number, dev_ip, current_version, installed_date, last_updated_date
        FROM kwt_denomination_version
        ORDER BY installed_date DESC

    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    latest_version = app_version

    # --- Color logic ---
    def color_for_version(version_str):
        current = version_to_int_tuple(version_str)
        latest = version_to_int_tuple(latest_version)

    
        if current == (0,0,0,0):
            return "#bbbb33"
        if current == latest:
            return "#ffffff"  # white for latest
        else:
            # Compute a difference factor based on version numbers
            diff_sum = sum(l - c for l, c in zip(latest, current))
            lightness = max(25, 80 - diff_sum * 10)  # older → darker red
            return f"hsl(0, 80%, {lightness}%)"  # red shades

    # --- Build HTML cards ---
    cards_html = ""
    for r in rows:
        loc_code, loc_name, pos_number, dev_ip, version, installed_date, last_updated_date = r
        color = color_for_version(version)

        # Ensure datetime objects, then format with AM/PM
        if isinstance(installed_date, datetime):
            installed_date_str = installed_date.strftime("%Y-%m-%d %I:%M %p")  # 12-hr with AM/PM
        else:
            installed_date_str = str(installed_date)

        if isinstance(last_updated_date, datetime):
            last_updated_date_str = last_updated_date.strftime("%Y-%m-%d %I:%M %p")
        else:
            last_updated_date_str = str(last_updated_date)

        cards_html += f"""
            <div class="card" 
                data-loc="{ loc_code }" 
                data-name="{ loc_name }" 
                style="border-color:{ color };">
                <h3>{ loc_name }</h3>
                <span>{ loc_code }-{ pos_number }</span>
                <p><strong>IP:</strong> <span class="copy-ip" onclick="copyToClipboard('{dev_ip}')">{dev_ip}</span></p>
                <p><strong>Installed Version:</strong> { version }</p>
                <p><strong>Installed Date:</strong> { installed_date_str }</p>
                <p><strong>Last Updated Date:</strong> { last_updated_date_str }</p>
            </div>
        """

    
    return f"""
        <html>
        <head>
            <style>
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    margin: 20px;
                    background-color: #f5f5f5;
                }}
                h1 {{
                    color: #333;
                }}
                #filter-input {{
                    padding: 10px;
                    margin-bottom: 20px;
                    font-size: 16px;
                    width: 250px;
                    border-radius: 5px;
                    border: 1px solid #ccc;
                }}
                #view-reports-btn {{
                    padding: 10px 15px;
                    margin-left: 10px;
                    font-size: 16px;
                    border-radius: 5px;
                    border: none;
                    background-color: #4CAF50;
                    color: white;
                    cursor: pointer;
                    transition: background 0.2s;
                }}
                #view-reports-btn:hover {{
                    background-color: #45a049;
                }}
                .cards-container, .reports-container {{
                    margin-top: 15px;
                }}
                .cards-container {{
                    display: flex;
                    flex-wrap: wrap;
                    gap: 15px;
                }}
                .card {{
                    flex: 1 1 220px;
                    border-radius: 12px;
                    padding: 15px;
                    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
                    transition: transform 0.2s, box-shadow 0.2s;
                    color: #333;
                    background: #fff;
                    border: 3px solid transparent;
                }}
                .card:hover {{
                    transform: translateY(-5px);
                    box-shadow: 0 8px 20px rgba(0,0,0,0.15);
                }}
                .card h3 {{
                    margin-top: 0;
                    margin-bottom: 8px;
                    font-size: 18px;
                }}
                .card span {{
                    font-weight: 600;
                    color: #555;
                }}
                .card p {{
                    margin: 5px 0;
                    font-size: 14px;
                }}
                .copy-ip {{
                    color: #007bff;
                    cursor: pointer;
                    text-decoration: underline;
                }}
                .copy-ip:hover {{
                    color: #0056b3;
                }}
                table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin-top: 15px;
                }}
                th, td {{
                    border: 1px solid #ddd;
                    padding: 8px;
                    text-align: left;
                }}
                th {{
                    background-color: #4CAF50;
                    color: white;
                }}
                tr:nth-child(even) {{ background-color: #f2f2f2; }}
                tr:hover {{ background-color: #ddd; }}
            </style>
        </head>
        <body>
            <p><strong>Latest Version:</strong> {app_version}</p>

            <input type="text" id="filter-input" placeholder="CTRL+K Filter by loc_code..." onkeyup="filterCards()">
            <button id="view-reports-btn" onclick="showReports()">View Posts</button>
            
            <div class="cards-container" id="cards-container">
                {cards_html}
            </div>

            <div class="reports-container" id="reports-container" style="display:none;">
               
            </div>

        <script>
        function filterCards() {{
            var input = document.getElementById('filter-input').value;
            var cardsContainer = document.getElementById('cards-container');
            var reportsContainer = document.getElementById('reports-container');

            if(input.trim() !== "") {{
                // Show cards, hide reports
                cardsContainer.style.display = 'flex';
                reportsContainer.style.display = 'none';
            }} else {{
                // If input empty and reports loaded, keep reports hidden until button clicked
                cardsContainer.style.display = 'flex';
            }}

            var filter = input.toUpperCase();
            var cards = document.querySelectorAll('.card');
            cards.forEach(card => {{
                var loc = card.getAttribute('data-loc').toUpperCase();
                var name = card.querySelector('h3').textContent.toUpperCase();
                card.style.display = (loc.includes(filter) || name.includes(filter)) ? 'block' : 'none';
            }});
        }}

        function showReports() {{
            var cardsContainer = document.getElementById('cards-container');
            var reportsContainer = document.getElementById('reports-container');
            var input = document.getElementById('filter-input').value;
            
            if(true) {{
                // Fetch the reports table via AJAX
                fetch('/helpus')
                    .then(response => response.text())
                    .then(html => {{
                        reportsContainer.innerHTML = html;
                        reportsContainer.style.display = 'block';
                        cardsContainer.style.display = 'none';
                    }})
                    .catch(err => console.error("Failed to load reports:", err));
            }} else {{
                // If user typed something, show cards
                reportsContainer.style.display = 'none';
                cardsContainer.style.display = 'flex';
            }}
        }}

        function copyToClipboard(text) {{
            if (navigator.clipboard && navigator.clipboard.writeText) {{
                navigator.clipboard.writeText(text).then(function() {{
                    console.log("Copied IP: " + text);
                }}).catch(function(err) {{
                    console.error("Failed to copy: ", err);
                }});
            }} else {{
                console.error("Clipboard API not supported.");
            }}
        }}

        // Ctrl+K to focus search
        document.addEventListener("keydown", function(event) {{
            if (event.ctrlKey && event.key.toLowerCase() === "k") {{
                event.preventDefault();
                document.getElementById("filter-input").focus();
            }}
        }});
        </script>
        </body>
        </html>
        """

@app.route('/cashier_login' , methods=['POST'])
def cashier_login():
    try:
     
        data = request.get_json()
        cashier_id = data.get("cashier_id")
        pin = data.get("password")
        print(request.get_json())
        if DEBUG :
            if pin =="" and cashier_id =="":
                cashier_id=80937
                pin=10753
            else:
                try:
                    cashier_id = int(cashier_id)
                    pin = int(pin)
                except (ValueError, TypeError):
                    return jsonify({"message": "Username and password must be numeric"}), 400
        else :
            if pin =="" or cashier_id =="":
             
                 return jsonify({"message": "Please enter the username and password"}), 400
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
        if row and row[1].lower() != "invalid":
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





def get_git_path():
    git_local = shutil.which("git")
    if git_local:
        return git_local
 
    git_prod = r"C:\Program Files\Git\bin\git.exe"
    if os.path.exists(git_prod):
        return git_prod
    return None

@app.route("/webhook/gitpull", methods=["GET","POST"])
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



import time 
from flask import request, jsonify
# Assuming connection() and get_environment() are defined elsewhere

@app.route("/version", methods=["GET", "POST"])
def version():
    conn = connection()
    cur = conn.cursor()

    if request.method == "POST":
        data = request.json
        loc_code = data.get("loc_code")
        loc_name = data.get("loc_name")
        pos_number = data.get("pos_number")
        dev_ip = data.get("dev_ip")
        current_version = data.get("current_version")

        # Auto-detect environment
        environment = get_environment()

        sql = """
        MERGE INTO kwt_denomination_version t
        USING (SELECT :loc_code AS loc_code,
                      :loc_name AS loc_name,
                      :pos_number AS pos_number,
                      :dev_ip AS dev_ip,
                      :environment AS environment,
                      :current_version AS current_version
               FROM dual) s
        ON (t.dev_ip = s.dev_ip)
        WHEN MATCHED THEN
            UPDATE SET
                t.loc_code = s.loc_code,
                t.loc_name = s.loc_name,
                t.pos_number = s.pos_number,
                t.environment = s.environment,
                t.current_version = CASE 
                                      WHEN t.current_version <> s.current_version 
                                      THEN s.current_version 
                                      ELSE t.current_version 
                                    END,
                t.last_updated_date = CASE 
                                        WHEN t.current_version <> s.current_version 
                                        AND (t.current_version < s.current_version OR t.current_version IS NULL)
                                        THEN CURRENT_TIMESTAMP 
                                        ELSE t.last_updated_date 
                                      END
        WHEN NOT MATCHED THEN
            INSERT (ID, loc_code, loc_name, pos_number, dev_ip, installed_date, last_updated_date, current_version, environment)
            VALUES (kwt_denomination_version_seq.NEXTVAL, s.loc_code, s.loc_name, s.pos_number, s.dev_ip, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, s.current_version, s.environment)
        """

        cur.execute(sql, {
            "loc_code": loc_code,
            "loc_name": loc_name,
            "pos_number": pos_number,
            "dev_ip": dev_ip,
            "current_version": current_version,
            "environment": environment
        })
        conn.commit()

        return jsonify({"status": "ok", "environment": environment, "message": "Version stored/updated"})
    elif request.method == "GET":
        cur.execute("""
            SELECT ID, loc_code, loc_name, pos_number, dev_ip, 
                   TO_CHAR(installed_date, 'YYYY-MM-DD HH24:MI:SS'),
                   TO_CHAR(last_updated_date, 'YYYY-MM-DD HH24:MI:SS'),
                   current_version,
                   environment
            FROM kwt_denomination_version 
        """)
        rows = cur.fetchall()

        result = []
        for r in rows:
            result.append({
                "id": r[0],
                "loc_code": r[1],
                "loc_name": r[2],
                "pos_number": r[3],
                "dev_ip": r[4],
                "installed_date": r[5],
                "last_updated_date": r[6],
                "current_version": r[7],
                "environment": r[8]
            })

        return jsonify(result)

    cur.close()
    conn.close()


@app.route("/helpus", methods=["POST","GET"])
def helpus():
    conn = connection()
    cursor = conn.cursor()

    if request.method =="POST":

        try:
            data = request.json
            sql = """
                INSERT INTO kwt_denomination_Issue_report
                (ID, TYPE, MESSAGE, USER_NAME, USER_ID, DATE_TIME, POS_NUMBER, DEV_IP , LOC_CODE)
                VALUES (kwt_denomination_ISSUE_SEQ.NEXTVAL, :type, :message, :username, :userid, :datetime, :posnumber, :devip ,:loccode)
            """
            cursor.execute(sql, {
                "type": data.get("Type"),
                "message": data.get("Message"),
                "username": data.get("UserName"),
                "userid": data.get("UserId"),
                "datetime": datetime.fromisoformat(data.get("Datetime")),
                "posnumber": data.get("PosNumber"),
                "devip": data.get("DevIp"),
                "loccode": data.get("LocCode")
            })
            conn.commit()
            return jsonify({"status": "success"}), 200
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)}), 500
    else:
        try:
            cursor.execute("""
                SELECT ID, TYPE, MESSAGE, USER_NAME, USER_ID, DATE_TIME, POS_NUMBER, DEV_IP, LOC_CODE
                FROM kwt_denomination_Issue_report
                ORDER BY DATE_TIME DESC
            """)
            rows = cursor.fetchall()
            # HTML template for table
            html_template = """
            <!DOCTYPE html>
            <html>
            <head>
                <title>Posts from locations</title>
                <style>
                    body { font-family: Arial, sans-serif; margin: 20px; }
                    table { border-collapse: collapse; width: 100%; }
                    th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                    th { background-color: #4CAF50; color: white; }
                    tr:nth-child(even) { background-color: #f2f2f2; }
                    tr:hover { background-color: #ddd; }
                    h2 { color: #333; }
                </style>
            </head>
            <body>
                <h2>Posted resports</h2>
                <table>
                    <tr>
                        <th>ID</th>
                        <th>Type</th>
                        <th>Message</th>
                        <th>User Name</th>
                        <th>User ID</th>
                        <th>Date Time</th>
                        <th>POS Number</th>
                        <th>Dev IP</th>
                        <th>Loc Code</th>
                    </tr>
                    {% for row in rows %}
                    <tr>
                        <td>{{ row[0] }}</td>
                        <td>{{ row[1] }}</td>
                        <td>{{ row[2] }}</td>
                        <td>{{ row[3] }}</td>
                        <td>{{ row[4] }}</td>
                        <td>{{ row[5] }}</td>
                        <td>{{ row[6] }}</td>
                        <td>{{ row[7] }}</td>
                        <td>{{ row[8] }}</td>
                    </tr>
                    {% endfor %}
                </table>
            </body>
            </html>
            """
            return render_template_string(html_template, rows=rows)
        except Exception as e:
            return f"Error: {str(e)}"


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)