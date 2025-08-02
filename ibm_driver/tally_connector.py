from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# Change if Tally runs on a different port
TALLY_URL = "http://localhost:9000"

@app.route("/query_tally", methods=["POST"])
def query_tally():
    try:
        xml_query = request.json.get("xml")
        if not xml_query:
            return jsonify({"error": "No XML provided"}), 400

        headers = {"Content-Type": "application/xml"}
        response = requests.post(TALLY_URL, data=xml_query, headers=headers)

        return jsonify({
            "status_code": response.status_code,
            "tally_response": response.text
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/get_ledgers", methods=["GET"])
def get_ledgers():
    xml = """
<ENVELOPE>
  <HEADER>
    <VERSION>1</VERSION>
    <TALLYREQUEST>Export</TALLYREQUEST>
    <TYPE>Collection</TYPE>
    <ID>List of Ledgers</ID>
  </HEADER>
  <BODY>
    <DESC>
      <STATICVARIABLES>
        <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
        <SVCOMPANY>Test Company</SVCOMPANY>
      </STATICVARIABLES>
      <TDL>
        <TDLMESSAGE>
          <COLLECTION NAME="List of Ledgers" ISMODIFY="No">
            <TYPE>Ledger</TYPE>
          </COLLECTION>
        </TDLMESSAGE>
      </TDL>
    </DESC>
  </BODY>
</ENVELOPE>
"""
    headers = {"Content-Type": "application/xml"}
    response = requests.post(TALLY_URL, data=xml, headers=headers)
    return response.text

if __name__ == "__main__":
    app.run(debug=True, port=5001)
