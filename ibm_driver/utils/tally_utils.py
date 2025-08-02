import requests
import logging
import xml.etree.ElementTree as ET
from flask import Flask, jsonify
import json
app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.DEBUG)

CLOUD_SERVER_URL = "https://smartcard-cloud.onrender.com/receive-tally"
#BEARER_TOKEN = "supersecretkey123"  # Bearer token for authentication

def fetch_companies_ledgers_and_vouchers_from_tally():
    url = "http://localhost:9000"  # Mock Tally ERP 9 URL
    xml_request_companies = """<ENVELOPE>
        <HEADER>
            <TALLYREQUEST>Export</TALLYREQUEST>
            <TYPE>Data</TYPE>
            <ID>Company</ID>
        </HEADER>
        <BODY>
            <DESC>
                <STATICVARIABLES>
                    <SVEXPORTFORMAT>XML</SVEXPORTFORMAT>
                </STATICVARIABLES>
            </DESC>
        </BODY>
    </ENVELOPE>"""

    logging.debug("Sending request to Mock Tally at %s with XML:\n%s", url, xml_request_companies)

    try:
        response = requests.post(url, data=xml_request_companies, headers={'Content-Type': 'application/xml'})
        logging.debug("HTTP Response Status from Mock Tally: %s", response.status_code)
        logging.debug("Raw XML response for companies: %s", response.text)

        if response.status_code == 200:
            companies = parse_companies_from_xml(response.text)
            data = {}

            for company in companies:
                ledgers_xml = fetch_ledgers_for_company(company)
                vouchers_xml = fetch_vouchers_for_company(company)
                data[company] = {
                    "ledgers": parse_ledgers_from_xml(ledgers_xml),
                    "vouchers": parse_vouchers_from_xml(vouchers_xml)
                }

            return data
        else:
            logging.error("Failed to fetch companies from Mock Tally. Status Code: %s", response.status_code)
            return None

    except Exception as e:
        logging.error("Error while fetching companies from Mock Tally: %s", str(e))
        return None

def fetch_ledgers_for_company(company_name):
    url = "http://localhost:9000"
    xml_request_ledgers = f"""<ENVELOPE>
        <HEADER>
            <TALLYREQUEST>Export</TALLYREQUEST>
            <TYPE>Data</TYPE>
            <ID>Ledger</ID>
        </HEADER>
        <BODY>
            <DESC>
                <STATICVARIABLES>
                    <SVEXPORTFORMAT>XML</SVEXPORTFORMAT>
                    <SVCOMPANY>{company_name}</SVCOMPANY>
                </STATICVARIABLES>
            </DESC>
        </BODY>
    </ENVELOPE>"""

    logging.debug("Sending request to Mock Tally for ledgers of %s with XML:\n%s", company_name, xml_request_ledgers)

    try:
        response = requests.post(url, data=xml_request_ledgers, headers={'Content-Type': 'application/xml'})
        return response.text if response.status_code == 200 else None
    except Exception as e:
        logging.error("Error while fetching ledgers for company %s: %s", company_name, str(e))
        return None

def fetch_vouchers_for_company(company_name):
    url = "http://localhost:9000"  # Mock Tally ERP 9 URL
    xml_request_vouchers = f"""<ENVELOPE>
        <HEADER>
            <TALLYREQUEST>Export</TALLYREQUEST>
            <TYPE>Data</TYPE>
            <ID>Vouchers</ID>
        </HEADER>
        <BODY>
            <DESC>
                <STATICVARIABLES>
                    <SVEXPORTFORMAT>XML</SVEXPORTFORMAT>
                    <SVCOMPANY>{company_name}</SVCOMPANY>
                </STATICVARIABLES>
            </DESC>
        </BODY>
    </ENVELOPE>"""

    logging.debug("Sending request to Mock Tally for vouchers of %s with XML:\n%s", company_name, xml_request_vouchers)

    try:
        response = requests.post(url, data=xml_request_vouchers, headers={'Content-Type': 'application/xml'})
        return response.text if response.status_code == 200 else None
    except Exception as e:
        logging.error("Error while fetching vouchers for company %s: %s", company_name, str(e))
        return None

def parse_companies_from_xml(xml_data):
    companies = []
    try:
        root = ET.fromstring(xml_data)
        for company in root.findall('.//COMPANY'):
            companies.append(company.text)
    except ET.ParseError as e:
        logging.error("Error parsing XML for companies: %s", str(e))
    return companies

def parse_ledgers_from_xml(xml_data):
    ledgers = []
    try:
        root = ET.fromstring(xml_data)
        for ledger in root.findall('.//LEDGER'):
            ledgers.append(ledger.text)
    except ET.ParseError as e:
        logging.error("Error parsing XML for ledgers: %s", str(e))
    return ledgers

def parse_vouchers_from_xml(xml_data):
    vouchers = []
    try:
        root = ET.fromstring(xml_data)
        for voucher in root.findall('.//VOUCHER'):
            voucher_details = {
                "date": voucher.find('DATE').text if voucher.find('DATE') is not None else None,
                "type": voucher.find('VOUCHERTYPENAME').text if voucher.find('VOUCHERTYPENAME') is not None else None,
                "amount": voucher.find('AMOUNT').text if voucher.find('AMOUNT') is not None else None,
                "narration": voucher.find('NARRATION').text if voucher.find('NARRATION') is not None else None,
            }
            vouchers.append(voucher_details)
    except ET.ParseError as e:
        logging.error("Error parsing XML for vouchers: %s", str(e))
    return vouchers

def send_data_to_cloud(data):
    try:
        payload = {
            "records": [
                {
                    "company": company,
                    "ledgers": data[company]["ledgers"],
                    "vouchers": data[company]["vouchers"]
                }
                for company in data
            ]
        }
        logging.debug("Sending data to cloud server: %s", payload)

        headers = {
            'Content-Type': 'application/json'
        }

        response = requests.post(CLOUD_SERVER_URL, json=payload, headers=headers)
        logging.debug("HTTP Response Status from cloud: %s", response.status_code)
        logging.debug("Response from cloud: %s", response.text)

        if response.status_code == 200:
            logging.info("Data successfully sent to cloud.")
        else:
            logging.error("Failed to send data to cloud. Status Code: %s", response.status_code)

    except Exception as e:
        logging.error("Error while sending data to cloud: %s", str(e))

@app.route('/sync_tally_data', methods=['GET'])
def sync_tally_data():
    logging.info("Starting data synchronization from Mock Tally to cloud...")
    data = fetch_companies_ledgers_and_vouchers_from_tally()
    
    if data:
        send_data_to_cloud(data)
        return jsonify({"message": "Data synchronization completed.", "data": data}), 200
    else:
        return jsonify({"error": "Failed to fetch data from Mock Tally."}), 500

if __name__ == '__main__':
    app.run(debug=True)
