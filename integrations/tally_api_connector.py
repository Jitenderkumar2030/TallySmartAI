import requests
import xml.etree.ElementTree as ET
import pandas as pd
from datetime import datetime

class TallyAPIConnector:
    def __init__(self, tally_server="localhost", tally_port=9000):
        self.base_url = f"http://{tally_server}:{tally_port}"
        self.session = requests.Session()
    
    def test_connection(self):
        """Test connection to Tally server"""
        try:
            response = self.session.get(f"{self.base_url}/")
            return response.status_code == 200
        except:
            return False
    
    def fetch_ledger_data(self, company_name, from_date, to_date):
        """Fetch ledger data directly from Tally"""
        xml_request = f"""
        <ENVELOPE>
            <HEADER>
                <TALLYREQUEST>Export Data</TALLYREQUEST>
            </HEADER>
            <BODY>
                <EXPORTDATA>
                    <REQUESTDESC>
                        <REPORTNAME>Ledger</REPORTNAME>
                        <STATICVARIABLES>
                            <SVCOMPANY>{company_name}</SVCOMPANY>
                            <SVFROMDATE>{from_date}</SVFROMDATE>
                            <SVTODATE>{to_date}</SVTODATE>
                        </STATICVARIABLES>
                    </REQUESTDESC>
                </EXPORTDATA>
            </BODY>
        </ENVELOPE>
        """
        
        try:
            response = self.session.post(
                self.base_url,
                data=xml_request,
                headers={'Content-Type': 'application/xml'}
            )
            
            if response.status_code == 200:
                return self._parse_tally_xml(response.text)
            else:
                return None
        except Exception as e:
            print(f"Error fetching data: {e}")
            return None
    
    def _parse_tally_xml(self, xml_data):
        """Parse Tally XML response to DataFrame"""
        try:
            root = ET.fromstring(xml_data)
            records = []
            
            # Parse XML structure (simplified)
            for voucher in root.findall('.//VOUCHER'):
                record = {
                    'Date': voucher.find('DATE').text if voucher.find('DATE') is not None else '',
                    'VoucherType': voucher.find('VOUCHERTYPE').text if voucher.find('VOUCHERTYPE') is not None else '',
                    'Amount': float(voucher.find('AMOUNT').text) if voucher.find('AMOUNT') is not None else 0,
                    'Particulars': voucher.find('PARTICULARS').text if voucher.find('PARTICULARS') is not None else ''
                }
                records.append(record)
            
            return pd.DataFrame(records)
        except Exception as e:
            print(f"Error parsing XML: {e}")
            return pd.DataFrame()

tally_connector = TallyAPIConnector()