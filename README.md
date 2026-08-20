# Ticketmaster Global Events Analysis

## Local Environment
### Environment Variables
From the root of your project, run the following to create your .env file with the required variables:

```bash
cp .env.example .env
```

You will need to replace those key values with API keys retrieved from the [Ticketmaster API]('https://developer.ticketmaster.com/products-and-docs/apis/getting-started/') and from Duke's [AI Gateway]('https://dashboard.ai.duke.edu/api-keys').

### Install dependencies
Create your virtual environment with

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Once your virtual environment is activated, install the required dependencies:

```bash
pip install -r requirements.txt
```