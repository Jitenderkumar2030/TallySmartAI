import PyPDF2
import pdfplumber
import pandas as pd
import re
from datetime import datetime
import io

class PDFInvoiceParser:
    def __init__(self):
        self.invoice_patterns = {
            'invoice_number': [
                r'invoice\s*(?:no|number|#)?\s*:?\s*([A-Z0-9\-/]+)',
                r'bill\s*(?:no|number|#)?\s*:?\s*([A-Z0-9\-/]+)'
            ],
            'date': [
                r'date\s*:?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
                r'invoice\s*date\s*:?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})'
            ],
            'amount': [
                r'total\s*:?\s*₹?\s*([0-9,]+\.?\d*)',
                r'grand\s*total\s*:?\s*₹?\s*([0-9,]+\.?\d*)',
                r'amount\s*:?\s*₹?\s*([0-9,]+\.?\d*)'
            ],
            'gstin': [
                r'gstin\s*:?\s*([0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1})',
                r'gst\s*no\s*:?\s*([0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1})'
            ],
            'vendor': [
                r'from\s*:?\s*([A-Za-z\s&\.]+?)(?:\n|address)',
                r'vendor\s*:?\s*([A-Za-z\s&\.]+?)(?:\n|address)'
            ]
        }
    
    def parse_pdf_invoice(self, pdf_file):
        """Extract invoice data from PDF"""
        try:
            # Try pdfplumber first (better for tables)
            with pdfplumber.open(pdf_file) as pdf:
                text = ""
                for page in pdf.pages:
                    text += page.extract_text() or ""
            
            if not text.strip():
                # Fallback to PyPDF2
                pdf_file.seek(0)
                pdf_reader = PyPDF2.PdfReader(pdf_file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text()
            
            return self._extract_invoice_data(text)
            
        except Exception as e:
            return {'error': f"PDF parsing failed: {str(e)}"}
    
    def _extract_invoice_data(self, text):
        """Extract structured data from invoice text"""
        data = {}
        text_lower = text.lower()
        
        for field, patterns in self.invoice_patterns.items():
            for pattern in patterns:
                match = re.search(pattern, text_lower, re.IGNORECASE)
                if match:
                    value = match.group(1).strip()
                    
                    # Clean and format the extracted value
                    if field == 'amount':
                        value = float(re.sub(r'[,₹\s]', '', value))
                    elif field == 'date':
                        value = self._parse_date(value)
                    elif field in ['vendor', 'invoice_number']:
                        value = value.upper()
                    
                    data[field] = value
                    break
        
        # Extract line items if possible
        line_items = self._extract_line_items(text)
        if line_items:
            data['line_items'] = line_items
        
        return data
    
    def _extract_line_items(self, text):
        """Extract individual line items from invoice"""
        lines = text.split('\n')
        items = []
        
        # Look for table-like structures
        for i, line in enumerate(lines):
            # Pattern for: Description Qty Rate Amount
            item_match = re.search(r'(.+?)\s+(\d+)\s+([0-9,]+\.?\d*)\s+([0-9,]+\.?\d*)$', line.strip())
            if item_match:
                items.append({
                    'description': item_match.group(1).strip(),
                    'quantity': int(item_match.group(2)),
                    'rate': float(re.sub(r'[,]', '', item_match.group(3))),
                    'amount': float(re.sub(r'[,]', '', item_match.group(4)))
                })
        
        return items[:10]  # Limit to first 10 items
    
    def _parse_date(self, date_str):
        """Parse date string to standard format"""
        date_formats = ['%d/%m/%Y', '%d-%m-%Y', '%d/%m/%y', '%d-%m-%y']
        
        for fmt in date_formats:
            try:
                return datetime.strptime(date_str, fmt).strftime('%Y-%m-%d')
            except ValueError:
                continue
        
        return date_str  # Return original if parsing fails
    
    def convert_to_dataframe(self, parsed_invoices):
        """Convert parsed invoice data to DataFrame"""
        records = []
        
        for invoice in parsed_invoices:
            if 'error' not in invoice:
                record = {
                    'Invoice_Number': invoice.get('invoice_number', ''),
                    'Date': invoice.get('date', ''),
                    'Vendor': invoice.get('vendor', ''),
                    'Amount': invoice.get('amount', 0),
                    'GSTIN': invoice.get('gstin', ''),
                    'Items_Count': len(invoice.get('line_items', []))
                }
                records.append(record)
        
        return pd.DataFrame(records)
    
    def validate_extracted_data(self, df):
        """Validate extracted invoice data"""
        issues = []
        
        # Check for missing critical fields
        if df['Amount'].isna().any():
            issues.append("Some invoices have missing amounts")
        
        if df['Date'].isna().any():
            issues.append("Some invoices have missing dates")
        
        # Check for duplicate invoice numbers
        duplicates = df[df.duplicated('Invoice_Number', keep=False)]
        if not duplicates.empty:
            issues.append(f"Found {len(duplicates)} duplicate invoice numbers")
        
        # Validate GSTIN format
        invalid_gstin = df[df['GSTIN'].notna() & 
                          ~df['GSTIN'].str.match(r'^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$')]
        if not invalid_gstin.empty:
            issues.append(f"Found {len(invalid_gstin)} invalid GSTIN formats")
        
        return issues

class PDFParser:
    def extract_financial_data(self, pdf_file):
        # PDF text extraction
        # Financial data parsing
        pass

# Global instance
pdf_parser = PDFInvoiceParser()
