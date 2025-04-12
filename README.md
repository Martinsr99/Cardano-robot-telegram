# Advanced Trading Bot

This is an advanced trading bot for cryptocurrency markets with price alerts, AI-powered market analysis, and forecasting capabilities.

## Project Structure

The project is organized into the following directories:

- **src/**: Core source code files
  - Main application logic
  - Price alerts system
  - AI analysis
  - Data providers
  - Models

- **config/**: Configuration files
  - Application configuration
  - Sensitive data (API keys, tokens)
  - JSON configuration files

- **utils/**: Utility functions and helpers
  - Telegram utilities
  - API key loading
  - General utility functions

- **tests/**: Test files
  - Unit tests
  - Integration tests
  - Test scripts

- **docs/**: Documentation
  - Project documentation
  - Usage guides

- **examples/**: Example files
  - Example implementations
  - Sample code

- **forecast_system/**: Forecasting system
  - Forecast models
  - Visualization tools
  - Position tracking

## Setup

1. Create a virtual environment:
   ```
   python -m venv venv
   ```

2. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - Linux/Mac: `source venv/bin/activate`

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Configure your API keys:
   - Copy `config/sensitive-data.txt.example` to `config/sensitive-data.txt`
   - Add your OpenAI API key and Telegram credentials

## Usage

Run the main application using the run.py script:
```
python run.py
```

You can also run the application directly:
```
python src/main.py
```

### Command Line Options

- `--monitor`: Run the bot in continuous monitoring mode
  ```
  python run.py --monitor
  ```

- `--ui`: Run the bot with the graphical user interface
  ```
  python run.py --ui
  ```

## Features

- Real-time price alerts for cryptocurrencies
- AI-powered market analysis using OpenAI's GPT-4
- Technical indicators and signals
- Forecasting system for price prediction
- Telegram integration for notifications
