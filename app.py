import os
import json
import dotenv
import pytz
import jwt
from datetime import datetime
from pyairtable import Table, Base
from pyairtable import formulas as atf
from flask import Flask, render_template, request, redirect, url_for, make_response, send_from_directory, abort

app = Flask(__name__)
dotenv.load_dotenv()
timezone = pytz.timezone('Asia/Singapore')

ENABLE_TEST_VALUES = False


@app.route('/sidebar', methods=["POST"])
def index():
    token = request.form.get('token')
    

    if not token:
        return "Not a valid Zendesk instance."
    try:
        key = os.environ.get('ZENDESK_APP_PUBLIC_KEY')
        audience = os.environ.get('ZENDESK_APP_AUD')
        #print("key=" + key + "audience=" + audience)
        payload = jwt.decode(token, key, algorithms = ['RS256'], audience = audience)
        print("Successfully decoded!")
    except jwt.InvalidTokenError:
        return "401 Invalid token."
    else:
        qs = request.query_string.decode("utf-8") # get the query string and convert it from bytes to str
        app_guid = request.args.get('app_guid')
        origin = request.args.get('origin')
        # resp = make_response(render_template('index.html', qs=qs))
        resp = make_response(redirect(url_for('await_user_input', origin=origin, app_guid=app_guid, token=token)))
        resp.set_cookie('app_params', qs)
        # resp.set_cookie('token', payload['qsh'])
    
    return resp

@app.route('/request-details', methods=["GET", "POST"])
def await_user_input():
    token = request.args.get('token')
    if not token:
        print("Forbidden in await_user_input()")
        return abort(403)
    zendesk_auth(token) # Authenticate

    app_guid = request.args.get("app_guid")
    origin = request.args.get("origin")
    qs = request.args.get('qs')
    resp = make_response(render_template('index.html', app_guid = app_guid, origin = origin, token=token))
    

    if request.form:
        qs = request.cookies.get("qs")
        serial_no = request.form['serial-num'].upper()
        contract_no = request.form['contract-num'].upper()

        # Build and send information to Airtable API
        record = None
        if serial_no != "" or contract_no != "":
            record = get_airtable_records(serial_no, contract_no)
        record_exists = False
        if record:
            with open("example.json", 'w') as f:
                json.dump(record, f)

            record_exists = True
        return redirect(url_for('display', 
                                origin = origin,
                                app_guid = app_guid,
                                exist = record_exists,
                                serial = serial_no, 
                                contract = contract_no,
                                token = token
                                ))
    return resp
    
@app.route('/list')
def display():
    token = request.args.get('token')
    if not token:
        print("Forbidden in display()")
        return abort(403)
    zendesk_auth(token)

    exists = request.args.get('exist')
    serial = request.args.get('serial')
    contract = request.args.get('contract')
    qs = request.cookies.get('app_params')
    app_guid = request.args.get("app_guid")
    origin = request.args.get("origin")
    print("User requested for contract: {} and serial: {}".format(contract, serial))
    
    record = []
    service_validity = None
    if exists == "True":
        # Load in json file
        with open('example.json', 'r') as f:
            record = json.load(f)
        
        service_validity = []
        for rec in record:
            # Check service validity
            service_validity.append(get_service_validity(rec))

    return render_template('record_list.html',
                            origin = origin,
                            app_guid = app_guid,
                            record=record,
                            validity=service_validity,
                            serial=serial,
                            contract=contract,
                            token = token
                            )

def get_airtable_records(serial, contract):
    AIRTABLE_TOKEN = os.environ.get('AIRTABLE_API_KEY')
    SG_CONTRACT_TBL = os.environ.get('SG_CONTRACT_TABLE')
    SG_CONTRACT_VIEW = os.environ.get('SG_CONTRACT_VIEW')
    JP_CONTRACT_TBL = os.environ.get('JP_CONTRACT_TABLE')
    JP_CONTRACT_VIEW = os.environ.get('JP_CONTRACT_VIEW')
    BASE_ID = os.environ.get('BASE_ID')

    rec_list = []
    jp_table = Table(AIRTABLE_TOKEN, BASE_ID, JP_CONTRACT_TBL)
    sg_table = Table(AIRTABLE_TOKEN, BASE_ID, SG_CONTRACT_TBL)
    airtable_formula = formula_builder(serial, contract)
    if airtable_formula == {}:
        raise Exception("Both are empty")
    formula = atf.match(airtable_formula)

    sg_table_matches = sg_table.all(formula=formula)
    jp_table_matches = jp_table.all(formula=formula)
    if sg_table_matches:
        for sg_match in sg_table_matches:
            sg_match['url'] = "/".join(["https://airtable.com", BASE_ID, SG_CONTRACT_TBL, SG_CONTRACT_VIEW, sg_match['id']])
        rec_list.extend(sg_table_matches)
    if jp_table_matches:
        for jp_match in jp_table_matches:
            jp_match['url'] = "/".join(["https://airtable.com", BASE_ID, JP_CONTRACT_TBL, JP_CONTRACT_VIEW, jp_match['id']])
            # print(f"{jp_match=}")
        rec_list.extend(jp_table_matches)
    # rec_list = sg_table.all(formula=formula)
    
    return rec_list

def get_service_validity(record):
    # Extract date field
    end_date = record['fields']['Service End Date']
    delim = "/" if "/" in end_date else "."
    day, month, year = end_date.split(delim) # Date is delimited by either dots or slashes
    if len(year) == 2: # In case of format like 21, 22, 23, etc.
        year = "20" + year

    # Format dates
    end_date_formatted = datetime(int(year), int(month), int(day), 0, tzinfo=timezone)
    current_date = datetime.now(tz=timezone)

    # Compare the dates
    service = 'Active' if current_date <= end_date_formatted else 'Expired'

    return service

@app.route('/js/<path:filename>')
def send_js(filename):
    return send_from_directory('static/js', filename)

def formula_builder(serial, contract):
    formula = {}
    if contract.strip(): # If contract is not blank
        formula["Contract No."] = contract
    
    if serial.strip():
        formula["Serial No."] = serial

    return formula
  
def zendesk_auth(token):
  try:
      key = os.environ.get('ZENDESK_APP_PUBLIC_KEY')
      audience = os.environ.get('ZENDESK_APP_AUD')
      payload = jwt.decode(token, key, algorithms = ['RS256'], audience = audience)
  except jwt.InvalidTokenError:
      return "401 Invalid token"

  return True

if __name__=="__main__":
    if os.environ.get("FLASK_ENV") == "development":
        app.debug = True
        app.run("0.0.0.0", port=5000)

