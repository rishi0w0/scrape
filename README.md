Instagram Scraper App
=====================

A GUI-based Instagram scraper that allows you to scrape posts from a target profile within a specified time period.

Features
--------

* Scrape posts from a target Instagram profile
* Specify a time period for scraping (start and end dates)
* Scrape comments for each post (optional)
* Save scraped data to a JSON file
* Resume scraping from the last successful post in case of errors
* Handle rate limit errors and bad response errors
* GUI-based interface for easy use

Requirements
------------

* Python 3.x
* `tkinter` and `tkcalendar` packages (built-in Python packages)
* `instaloader` package (install using `pip install instaloader`)
* `json`, `os`, `random`, `time`, and `threading` packages (built-in Python packages)

Usage
-----

1. Clone the repository and navigate to the project directory.
2. Install the required packages using `pip install -r requirements.txt`.
3. Run the app using `python instagram_scraper_app.py`.
4. Enter the target Instagram profile, your Instagram username and password, and the start and end dates for scraping.
5. Click the "Scrape" button to start the scraping process.
6. The app will save the scraped data to a JSON file and display the progress in the GUI.

Note
----

* This app is for educational purposes only and should not be used to scrape data from Instagram without permission.
* Instagram's terms of service prohibit scraping, and using this app may result in your account being banned.
* Use at your own risk.

License
-------

This project is licensed under the MIT License. See `LICENSE` for details.

Author
------

[Your Name]
