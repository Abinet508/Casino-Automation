# 🎰 Casino Automation Project: Advanced Web Interaction & Analytics 🎰

## ✨ Project Overview ✨

The Casino Automation Project is a sophisticated system designed to interact with online casino affiliate websites, meticulously track user-like interactions, and present the collected data through an intuitive web interface. This tool leverages the power of Playwright for web automation, Flask for creating a dynamic web application, and real-time updates through Flask-SocketIO. The project's core goal is to simulate user behavior on affiliate sites, record interactions (like clicking "signup" or "play now" buttons), and provide comprehensive statistics about these simulated actions.

## 🚀 Key Features 🚀

*   **🤖 Advanced Web Automation:**
    *   Employs Playwright for robust browser automation.
    *   Navigates and interacts with multiple casino affiliate websites.
    *   Handles different website layouts and structures effectively.
    *   Includes `playwright-stealth` to minimize bot detection.
    *   Configurable proxy settings for geographically diverse interactions.
    *   Handles cookie consent popups automatically.
*   **📊 Comprehensive Data Tracking & Analytics:**
    *   Tracks the number of clicks per casino.
    *   Maintains a detailed history log of each interaction (casino, affiliate, timestamp).
    *   Saves screenshots of the interacted casino pages.
    *   Provides real-time and historical data visualization on the web interface.
*   **🌐 User-Friendly Web Interface:**
    *   Developed with Flask, providing a dynamic and responsive web experience.
    *   **Control Panel:** Start/stop the automation and toggle continuous mode.
    *   **Dashboard:** View real-time statistics (total clicks, unique casinos, most clicked, last clicked).
    *   **History:** Detailed log of clicks, including timestamps, affiliates, and screenshots.
    *   **Settings:** Reset statistics.
*   **🔄 Real-Time Updates:**
    *   `Flask-SocketIO` enables live updates to the web interface.
    *   Dashboard and history sections dynamically update without needing to refresh the page.
*   **♾️ Continuous Operation:**
    *   Can run in continuous mode, endlessly interacting with affiliate sites.
*   **🧵 Concurrency & Efficiency:**
    *   Uses multi-threading (`threading`, `queue.Queue`) for concurrent processing of multiple affiliate sites.
*   **⚠️ Robust Error Handling:**
    *   Includes error management throughout the automation and web interface.
    *   Errors are logged and displayed to the user.
*   **🛡️ Detection Evasion:**
    *   Incorporates `playwright-stealth` techniques.
    *   Utilizes proxy settings (CatProxies) for increased anonymity.
* **🗂️ Clean Project Structure**: 
    * The project is organized logically with separate files for the core automation, the web application, static assets, and data storage.
* **📃 Clear Documentation**: 
    * The `README.md` file is very well written and documented.

## 🛠️ Technologies & Libraries 🛠️

*   **🐍 Python 3.x:** The backbone of the project.
*   **🎭 Playwright:** For cross-browser automation.
*   **🔌 `playwright-stealth`:** To evade detection as a bot.
*   **🧮 Flask:** For the web application backend.
*   **🔌 Flask-SocketIO:** For real-time WebSocket communication.
*   **🔑 `python-dotenv`:** To manage environment variables (for proxy credentials, etc.).
*   **📈 Chart.js:** For creating interactive data visualizations.
*   **💙 Bootstrap:** For responsive and modern web design.
*   **🧵 `threading`, `queue.Queue`:** For multi-threading and task management.
*   **📦 `json`:** For data serialization (saving and loading stats).
*   **📅 `datetime`:** For time-related operations.
* **🪵 `logging`**: For the management of logs
*   **🎨 HTML, CSS, JavaScript:** For the web interface's frontend.

## ⚙️ Setup & Installation ⚙️

1.  **Navigate to the Project Directory:**
    ```bash
    cd casino-automation
    ```

2.  **Install Python Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Install Playwright Browsers:**
    ```bash
    playwright install
    ```

4.  **Environment Variables (Optional):**
    *   Create a `.env` file in the root directory.
    *   Add any necessary environment variables (e.g., proxy credentials).

5. **Run the application**
    ```bash
    python app.py
    ```
    *  Access the web interface at `http://0.0.0.0:5000`.

## 🎛️ Configuration 🎛️

*   **`main_automation.py`:**
    *   `blacklisted_sites`: List of casino sites to avoid.
    *   `country_codes`: Dictionary mapping country names to country codes.
    *   `urls`: Nested dictionary containing affiliate website URLs, organized by country and affiliate site name.
    *   `image_folder`: Path to the folder where screenshots are saved.
    *   `stats_file`: Path to the `stats.json` file.
    * The handle_xxx methods contain the specific logic per affiliate website.
*   **`app.py`:**
    *   `SECRET_KEY`: Flask secret key.
    * `IMAGE_FOLDER`: Path to the static image folder.
    * `socketio`: Path to the socket
*   **`static/css/style.css`:** Styles the web interface.
*   **`static/js/main.js`:** Handles web interface interactivity and data display.
*   **`templates/index.html`:** Defines the structure of the web interface.
* **`requirements.txt`**: Contains the list of dependancies
* **`data/stats.json`**: Stores the current data

## 🕹️ Usage Guide 🕹️

1.  **Access the Web Interface:**
    *   Open your web browser and go to the URL where the Flask app is running (e.g., `http://0.0.0.0:5000`).

2.  **Control the Automation:**
    *   Navigate to the "Control" section.
    *   Click "Start Automation" to begin the process.
    *   Toggle the "Continuous Mode" checkbox for continuous operation.
    *   Click "Stop Automation" to halt the process.

3.  **View Statistics:**
    *   The "Dashboard" section displays real-time data about the automation.
    *   View total clicks, unique casinos, the most clicked casino, and the last clicked casino.
    * The two charts displays the clicks distribution and history
4.  **Explore History:**
    *   Go to the "History" section to see a detailed log of all interactions.
    *   The table displays the casino, the affiliate site, and the timestamp.
    * You can hover over the rows to have more details and the screenshot

5. **Reset data:**
   * Go to the settings tab to reset the stats.

## 📂 Project Structure 📂

```
casino-automation/
├── app.py
├── main_automation.py
├── requirements.txt
├── data/
│   └── stats.json
├── static/
│   ├── css/
│   │   └── style.css
│   ├── js/
│   │   └── main.js
│   └── Images/
├── templates/
│   └── index.html
├── README.md
└── .env
```

## 🎉 Conclusion 🎉

The Casino Automation Project represents a significant step in web interaction automation and data analytics. It blends cutting-edge web technologies to deliver a robust, user-friendly, and highly functional tool. This project offers a compelling foundation for further enhancements and expansion.
