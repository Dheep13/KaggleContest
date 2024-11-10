# app.py

from flask import Flask, render_template, request, jsonify, make_response
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
import json
import io
import logging
import os
from datetime import datetime
from openai import OpenAI
from dotenv import load_dotenv
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from pathlib import Path
import logging
import logging.handlers
from datetime import datetime

# Create the application instance
app = Flask(__name__, 
    static_folder='static',
    template_folder='templates'
)

# Load environment variables
load_dotenv()


# Configure logging
def setup_logging():
    """Configure logging with both file and console handlers"""
    # Create logs directory if it doesn't exist
    if not os.path.exists('logs'):
        os.makedirs('logs')

    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Create file handler for all logs
    file_handler = logging.handlers.RotatingFileHandler(
        filename=f'logs/app_{datetime.now().strftime("%Y%m%d")}.log',
        maxBytes=10485760,  # 10MB
        backupCount=5
    )
    file_handler.setFormatter(formatter)

    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    # Get root logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)  # Set to DEBUG for more detailed logs

    # Remove existing handlers
    logger.handlers = []

    # Add handlers
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger

# Initialize logging
logger = setup_logging()

# Initialize OpenAI client with API key from .env
try:
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        raise ValueError("OpenAI API key not found in environment variables")
    
    client = OpenAI(api_key=openai_api_key)
    logger.info("OpenAI client initialized successfully")
except Exception as e:
    logger.error(f"Error initializing OpenAI client: {str(e)}")
    raise

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def generate_design_document_content(mapping_data: dict) -> str:
    """
    Generates detailed design document content using GPT with Informatica expertise.
    """
    try:
        logger.info("Starting design document generation")
        
        # Extract SQL queries for analysis
        sql_sections = []
        for transformation in mapping_data['mapping']['transformations']:
            for attr in transformation['attributes']:
                if attr['name'] in ['Sql Query', 'Pre SQL', 'Post SQL', 'Lookup Sql Override'] and attr['value']:
                    sql_sections.append({
                        'transformation': transformation['name'],
                        'type': attr['name'],
                        'sql': attr['value']
                    })

        system_prompt = """You are an expert Informatica ETL developer and technical documentation specialist.
        Create a concise yet comprehensive technical design document, including SQL analysis.
        
        Focus on:
        1. Data Flow Architecture and Business Logic
        2. Transformation Analysis
        3. Transformation Logic
        4. SQL Analysis
        
        Keep sections within word limits while maintaining technical accuracy."""

        sections = [
            {
                "title": "1. Executive Summary",
                "prompt": f"""Provide a concise executive summary (100 words max) for:
                Mapping Name: {mapping_data['mapping']['name']}
                Description: {mapping_data['mapping']['description']}
                
                Include only the most critical aspects:
                - Core business purpose
                - Key technical components
                - Critical impacts""",
                "max_words": 100
            },
            {
                "title": "2. Architecture Overview",
                "prompt": f"""Provide a brief architectural analysis (150 words max):
                Sources: {mapping_data['mapping']['sources']}
                Targets: {mapping_data['mapping']['targets']}
                Transformations: {len(mapping_data['mapping']['transformations'])}
                
                Focus only on:
                - Essential data flow patterns
                - Critical design decisions""",
                "max_words": 150
            },
            {
                "title": "3. Transformation Analysis",
                "prompt": f"""Analyze key transformations (200 words max):
                {json.dumps([{
                    'name': t['name'],
                    'type': t['type'],
                    'fields': [{'name': f['name'], 'datatype': f['datatype']} 
                              for f in t['fields']]
                } for t in mapping_data['mapping']['transformations']], indent=2)}
                
                Focus on:
                - Critical business logic
                - Key data impacts""",
                "max_words": 200
            },
            {
                "title": "4. SQL Analysis",
                "prompt": f"""Analyze these SQL queries from the mapping (200 words max):
                {json.dumps(sql_sections, indent=2)}
                
                Focus on:
                - Key SQL patterns and logic
                - Query optimization opportunities
                - Data quality implications
                - Performance considerations""",
                "max_words": 200
            }
        ]

        logger.info("Generating document sections using OpenAI with word limits")
        complete_document = []
        
        for section in sections:
            logger.debug(f"Generating section: {section['title']}")
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": (
                    f"{section['prompt']}\n\n"
                    f"IMPORTANT: Limit your response to {section['max_words']} words maximum. "
                    "Be concise while maintaining technical accuracy."
                )}
            ]
            
            try:
                response = client.chat.completions.create(
                    model="gpt-4",
                    messages=messages,
                    temperature=0.7,
                    max_tokens=400  # Adjusted token limit for shorter responses
                )
                
                section_content = response.choices[0].message.content
                # Quick word count check
                word_count = len(section_content.split())
                logger.debug(f"Section {section['title']} word count: {word_count}")
                
                complete_document.extend([
                    section["title"],
                    "",
                    section_content,
                    "",
                    ""
                ])
                
            except Exception as e:
                logger.error(f"Error generating section {section['title']}: {str(e)}")
                raise

        logger.info("Document generation completed successfully")
        return "\n".join(complete_document)

    except Exception as e:
        logger.error(f"Error in generate_design_document_content: {str(e)}")
        raise

# Create necessary directories
def create_directories():
    """Create necessary static directories if they don't exist"""
    try:
        Path(app.static_folder, 'css').mkdir(parents=True, exist_ok=True)
        Path(app.static_folder, 'js').mkdir(parents=True, exist_ok=True)
        logging.info("Static directories created successfully")
    except Exception as e:
        logging.error(f"Error creating directories: {str(e)}")
        raise

create_directories()

# Data Classes
@dataclass
class Field:
    name: str
    datatype: str
    precision: Optional[str] = None
    scale: Optional[str] = None
    porttype: Optional[str] = None
    defaultvalue: Optional[str] = None
    expression: Optional[str] = None
    expressiontype: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in self.__dict__.items() if v is not None}

@dataclass
class TableAttribute:
    name: str
    value: str

    def to_dict(self) -> Dict[str, Any]:
        return self.__dict__

@dataclass
class Expression:
    name: Optional[str] = None
    value: str = ""
    input_field: Optional[str] = None
    expressiontype: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in self.__dict__.items() if v is not None}

@dataclass
class Transformation:
    name: str
    type: str
    description: str
    fields: List[Field]
    attributes: List[TableAttribute]
    expressions: List[Expression] = field(default_factory=list)
    reusable: str = "NO"

    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'type': self.type,
            'description': self.description,
            'fields': [field.to_dict() for field in self.fields],
            'attributes': [attr.to_dict() for attr in self.attributes],
            'expressions': [expr.to_dict() for expr in self.expressions],
            'reusable': self.reusable
        }

@dataclass
class Connector:
    frominstance: str
    frominstancetype: str
    toinstance: str
    toinstancetype: str
    fromfield: str
    tofield: str

    def to_dict(self) -> Dict[str, Any]:
        return self.__dict__

@dataclass
class Mapping:
    name: str
    description: str
    transformations: List[Transformation]
    connectors: List[Connector]
    sources: List[str]
    targets: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'description': self.description,
            'transformations': [t.to_dict() for t in self.transformations],
            'connectors': [c.to_dict() for c in self.connectors],
            'sources': self.sources,
            'targets': self.targets
        }

class InformaticaAnalyzer:
    def extract_mapping_content(self, xml_string: str) -> str:
        """Extracts mapping content from XML string"""
        try:
            root = ET.fromstring(xml_string)
            if root.tag == "document":
                document_content = root.find(".//document_content")
                if document_content is not None and len(document_content) > 0:
                    return ET.tostring(document_content[0], encoding='unicode')
            return xml_string
        except ET.ParseError as e:
            logger.error(f"XML parsing error: {str(e)}")
            raise ValueError(f"Invalid XML format: {str(e)}") from e

    def _extract_sql_queries(self, transformation_elem: ET.Element) -> Dict[str, str]:
        """Extracts SQL queries from transformation attributes"""
        sql_queries = {}
        
        # SQL attributes to check
        sql_attributes = {
            'Sql Query': 'main_query',
            'Pre SQL': 'pre_sql',
            'Post SQL': 'post_sql',
            'Lookup Sql Override': 'lookup_sql',
            'Source Filter': 'source_filter'
        }
        
        for attr_name, key in sql_attributes.items():
            sql_attr = transformation_elem.find(f"TABLEATTRIBUTE[@NAME='{attr_name}']")
            if sql_attr is not None and sql_attr.get("VALUE"):
                sql_queries[key] = sql_attr.get("VALUE")
        
        return sql_queries


    def _process_instances(self, root: ET.Element, mapping: Mapping) -> None:
        """Process source and target instances"""
        for instance_elem in root.findall("INSTANCE"):
            instance_type = instance_elem.get("TYPE")
            instance_name = instance_elem.get("NAME")
            if instance_type == "SOURCE":
                mapping.sources.append(instance_name)
            elif instance_type == "TARGET":
                mapping.targets.append(instance_name)

    def _process_connectors(self, root: ET.Element, mapping: Mapping) -> None:
        """Process mapping connectors"""
        for connector_elem in root.findall("CONNECTOR"):
            connector = Connector(
                frominstance=connector_elem.get("FROMINSTANCE", ""),
                frominstancetype=connector_elem.get("FROMINSTANCETYPE", ""),
                toinstance=connector_elem.get("TOINSTANCE", ""),
                toinstancetype=connector_elem.get("TOINSTANCETYPE", ""),
                fromfield=connector_elem.get("FROMFIELD", ""),
                tofield=connector_elem.get("TOFIELD", "")
            )
            mapping.connectors.append(connector)

    def parse_xml_string(self, xml_string: str) -> Mapping:
        """Main method to parse XML string into Mapping object"""
        try:
            logger.debug("Starting XML parsing")
            mapping_xml = self.extract_mapping_content(xml_string)
            root = ET.fromstring(mapping_xml)
            
            if root.tag != "MAPPING":
                raise ValueError(f"Expected MAPPING element, got {root.tag}")
            
            mapping = Mapping(
                name=root.get("NAME", "Unknown"),
                description=root.get("DESCRIPTION", ""),
                transformations=[],
                connectors=[],
                sources=[],
                targets=[]
            )

            for transform_elem in root.findall("TRANSFORMATION"):
                try:
                    transformation = self._parse_transformation(transform_elem)
                    mapping.transformations.append(transformation)
                except Exception as e:
                    logger.error(f"Error parsing transformation {transform_elem.get('NAME', 'Unknown')}: {str(e)}")
                    continue

            self._process_instances(root, mapping)
            self._process_connectors(root, mapping)
            
            return mapping
            
        except ET.ParseError as e:
            logger.error(f"XML parsing error: {str(e)}")
            raise ValueError("Invalid XML format") from e
        except Exception as e:
            logger.error(f"Error parsing XML: {str(e)}")
            raise

    def _parse_transformation(self, transform_elem: ET.Element) -> Transformation:
        fields = []
        attributes = []
        expressions = []
        
        # Extract SQL queries
        sql_queries = self._extract_sql_queries(transform_elem)
        
        # Add SQL queries to attributes
        for sql_type, sql_value in sql_queries.items():
            attributes.append(TableAttribute(
                name=f"SQL_{sql_type}",
                value=sql_value
            ))
        
        # Rest of the parsing logic...
        for field_elem in transform_elem.findall("TRANSFORMFIELD"):
            field = Field(
                name=field_elem.get("NAME", ""),
                datatype=field_elem.get("DATATYPE", ""),
                precision=field_elem.get("PRECISION"),
                scale=field_elem.get("SCALE"),
                porttype=field_elem.get("PORTTYPE"),
                defaultvalue=field_elem.get("DEFAULTVALUE"),
                expression=field_elem.get("EXPRESSION"),
                expressiontype=field_elem.get("EXPRESSIONTYPE")
            )
            fields.append(field)
        
        for attr_elem in transform_elem.findall("TABLEATTRIBUTE"):
            attr = TableAttribute(
                name=attr_elem.get("NAME", ""),
                value=attr_elem.get("VALUE", "")
            )
            attributes.append(attr)
        
        return Transformation(
            name=transform_elem.get("NAME", ""),
            type=transform_elem.get("TYPE", ""),
            description=transform_elem.get("DESCRIPTION", ""),
            fields=fields,
            attributes=attributes,
            expressions=expressions,
            reusable=transform_elem.get("REUSABLE", "NO")
        )

def generate_design_document_pdf(content: str) -> io.BytesIO:
    """
    Creates a PDF document from the generated content using reportlab.
    Now accepts string content instead of mapping data.
    """
    # Create a buffer for the PDF
    buffer = io.BytesIO()
    
    # Create the PDF document template
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=inch,
        leftMargin=inch,
        topMargin=inch,
        bottomMargin=inch
    )
    
    # Get the default styles
    styles = getSampleStyleSheet()
    
    # Create custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Title'],
        fontSize=24,
        spaceAfter=30,
        textColor=colors.HexColor('#1a237e')
    )
    
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=11,
        spaceBefore=6,
        spaceAfter=6,
        leading=14
    )
    
    # Create the story (content) for the PDF
    story = []
    
    # Add title
    story.append(Paragraph("Informatica Mapping Design Document", title_style))
    story.append(Spacer(1, 20))
    
    # Add generated content sections
    # Split content into sections and paragraphs
    sections = content.split('\n\n')
    for section in sections:
        if section.strip():
            story.append(Paragraph(section, normal_style))
            story.append(Spacer(1, 12))
    
    try:
        # Build the PDF
        doc.build(story)
    except Exception as e:
        logger.error(f"Error building PDF: {str(e)}")
        raise
    
    # Reset buffer position to the beginning
    buffer.seek(0)
    return buffer

# Routes
@app.route('/')
def index():
    """Serve the main page"""
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze_mapping():
    try:
        xml_content = request.json.get('xml', '')
        if not xml_content:
            return jsonify({'error': 'No XML content provided'}), 400
        
        logger.info("Received XML content for analysis")
        analyzer = InformaticaAnalyzer()
        mapping = analyzer.parse_xml_string(xml_content)  # Using the correct method name
        
        # Use the to_dict() method for serialization
        return jsonify({'mapping': mapping.to_dict()})
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error analyzing mapping: {str(e)}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500
    

@app.route('/generate_document', methods=['POST'])
def generate_document():
    try:
        mapping_data = request.json
        if not mapping_data:
            logger.error("No mapping data provided")
            return jsonify({'error': 'No mapping data provided'}), 400

        logger.info(f"Starting document generation for mapping: {mapping_data['mapping']['name']}")

        # 1. First generate the content using OpenAI
        try:
            logger.info("Generating document content using OpenAI")
            document_content = generate_design_document_content(mapping_data)
            logger.info("Successfully generated document content")
        except Exception as e:
            logger.error(f"Error in generate_design_document_content: {str(e)}")
            raise Exception("Failed to generate document content") from e

        # 2. Then convert the content to PDF
        try:
            logger.info("Converting content to PDF")
            # Fix: Pass document_content instead of mapping_data
            pdf_buffer = generate_design_document_pdf(document_content)
            logger.info("Successfully generated PDF")
        except Exception as e:
            logger.error(f"Error in PDF generation: {str(e)}")
            raise Exception("Failed to create PDF") from e

        # 3. Return the PDF
        response = make_response(pdf_buffer.getvalue())
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename=design_document_{datetime.now().strftime("%Y%m%d%H%M%S")}.pdf'
        
        logger.info("Successfully completed document generation")
        return response

    except Exception as e:
        logger.error(f"Error in generate_document route: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal error: {str(error)}", exc_info=True)
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    # Ensure directories exist on startup
    create_directories()
    
    # Run the app
    app.run(
        host='0.0.0.0',
        port=int(os.getenv('PORT', 5000)),
        debug=os.getenv('FLASK_ENV') == 'development'
    )