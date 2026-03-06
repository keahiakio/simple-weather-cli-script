# simple-weather-cli-script

A command-line tool to fetch weather forecasts from weather.gov based on coordinates, city names, or zip codes.

## Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/keahiakio/simple-weather-cli-script.git
    cd simple-weather-cli-script
    ```

2.  **Set up a virtual environment (recommended):**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

## Usage

You can run the script directly:
```bash
python3 get_weather.py <latitude> <longitude>
python3 get_weather.py <city_or_airport_name>
python3 get_weather.py <zipcode>
```

## Global Execution

To run the weather script from any directory, you can create a symlink in your local bin directory:

1.  **Ensure the script is executable:**
    ```bash
    chmod +x get_weather.py
    ```

2.  **Create a symlink:**
    ```bash
    ln -s $(pwd)/get_weather.py ~/.local/bin/weather
    ```

3.  **Verify your PATH:**
    Ensure `~/.local/bin` is in your `$PATH`. You can then run `weather <location>` from anywhere.

## Testing

This project uses `pytest` for unit testing.

1.  **Install pytest:**
    ```bash
    pip install pytest
    ```

2.  **Run tests:**
    ```bash
    PYTHONPATH=. pytest tests/
    ```
