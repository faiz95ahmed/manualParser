# manualParser
Parse PDF Manuals

## Usage

1. Create virtual environment: `python3 -m venv .venv` && activate `source .venv/bin/activate`
2. Install requirements with pip `pip install -r requirements.txt`
3. Create a `.env` file in the project directory with your openai api key as follows:
```
OPENAI_API_KEY=yourkeyhere
```
4. Run using `fastapi run main.py`
5. Upload a file using the `parse` endpoint (as part of the form-data on a POST request, with key: `file`)