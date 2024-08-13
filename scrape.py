import json
import os
import random
import time
import threading
import instaloader
import signal
from tkinter import *
from tkinter import messagebox
from tkcalendar import Calendar
from datetime import datetime

class InstagramScraperApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Instagram Scraper")

        # Create and pack GUI components
        self.label_target_profile = Label(root, text="Target Instagram Profile:")
        self.label_target_profile.pack()

        self.target_profile_entry = Entry(root)
        self.target_profile_entry.pack()

        self.label_username = Label(root, text="Instagram Username:")
        self.label_username.pack()

        self.username_entry = Entry(root)
        self.username_entry.pack()

        self.label_password = Label(root, text="Instagram Password:")
        self.label_password.pack()

        # Entry field for password
        self.password_entry = Entry(root, show="*")
        self.password_entry.pack()

        # Variable to track password visibility state
        self.show_password_var = BooleanVar()
        self.show_password_var.set(False)  # Initially, password is hidden

        # Checkbox for showing password
        self.show_password_checkbox = Checkbutton(root, text="Show Password", variable=self.show_password_var, command=self.toggle_password_visibility)
        self.show_password_checkbox.pack()

        self.select_time_button = Button(root, text="Select Time Period", command=self.open_calendar)
        self.select_time_button.pack()

        # Checkbox for scraping comments
        self.scrape_comments_var = BooleanVar()
        self.scrape_comments_var.set(False)  # By default, do not scrape comments
        self.scrape_comments_checkbox = Checkbutton(root, text="Scrape Comments", variable=self.scrape_comments_var)
        self.scrape_comments_checkbox.pack()

        self.scrape_button = Button(root, text="Scrape", command=self.start_scraping)
        self.scrape_button.pack()

        self.output_text = Text(root, wrap='word', height=20, width=80)
        self.output_text.pack()

        # Add a scrollbar to the Text widget
        self.scrollbar = Scrollbar(root, orient=VERTICAL, command=self.output_text.yview)
        self.output_text.configure(yscrollcommand=self.scrollbar.set)
        self.scrollbar.pack(side='right', fill=Y)

        self.start_date = None
        self.end_date = None
        self.last_post_shortcode = None
        self.state_filename = "scraping_state.json"  # File to save state

        # Initialize data storage
        self.profile_data = {"profile": {}, "posts": []}
        self.data_filename = None

        # Register signal handler for graceful shutdown
        signal.signal(signal.SIGINT, self.handle_exit)
        signal.signal(signal.SIGTERM, self.handle_exit)

    def toggle_password_visibility(self):
        if self.show_password_var.get():
            self.password_entry.config(show="")
        else:
            self.password_entry.config(show="*")

    def open_calendar(self):
        self.calendar_window = Toplevel(self.root)
        self.calendar_window.title("Select Time Period")

        # Start Date Label and Calendar
        self.start_label = Label(self.calendar_window, text="Start Date")
        self.start_label.pack()
        self.cal_start = Calendar(self.calendar_window, selectmode="day", date_pattern="y-mm-dd")
        self.cal_start.pack(pady=10)

        # End Date Label and Calendar
        self.end_label = Label(self.calendar_window, text="End Date")
        self.end_label.pack()
        self.cal_end = Calendar(self.calendar_window, selectmode="day", date_pattern="y-mm-dd")
        self.cal_end.pack(pady=10)

        self.confirm_button = Button(self.calendar_window, text="Confirm", command=self.select_dates)
        self.confirm_button.pack(pady=10)

    def select_dates(self):
        self.start_date = self.cal_start.get_date()
        self.end_date = self.cal_end.get_date()
        self.update_output(f"Selected time period: {self.start_date} to {self.end_date}")
        self.calendar_window.destroy()

    def start_scraping(self):
        # Start the scraping process in a new thread
        threading.Thread(target=self.scrape_profile).start()

    def update_output(self, message, overwrite=False):
        """Update the GUI output text widget from a different thread."""
        if overwrite:
            # Move the cursor to the end of the last line and overwrite it
            self.output_text.delete('end-1c linestart', 'end')  # Delete the last line's content
            self.output_text.insert('end-1c linestart', message + "\n")
        else:
            self.output_text.insert(END, message + "\n")
        self.output_text.yview(END)
        self.root.update_idletasks()  # Ensure GUI updates in real-time

    def random_delay(self):
        """Introduce a random delay to humanize the scraping process."""
        delay = random.uniform(2, 5)  # Random delay between 2 and 5 seconds
        self.update_output(f"Waiting for {delay:.2f} seconds...")
        self.root.update_idletasks()  # Ensure GUI updates in real-time
        time.sleep(delay)

    def random_scroll(self):
        """Simulate random scrolling to humanize the scraping process."""
        scroll_amount = random.randint(1, 10)
        scroll_direction = random.choice(['up', 'down'])
        self.update_output(f"Scrolling {scroll_direction} by {scroll_amount} lines...")
        self.output_text.yview_scroll(scroll_amount if scroll_direction == 'down' else -scroll_amount, "units")
        self.random_delay()

    def save_data(self):
        """Save the current profile data to the JSON file."""
        if self.data_filename:
            try:
                with open(self.data_filename, "w", encoding="utf-8") as json_file:
                    json.dump(self.profile_data, json_file, ensure_ascii=False, indent=4)
                self.update_output(f"Data saved to {self.data_filename}")
            except IOError as e:
                self.update_output(f"Error writing to file: {e}")

    def save_state(self):
        """Save the current state to a JSON file."""
        state = {
            "last_post_shortcode": self.last_post_shortcode,
            "start_date": self.start_date,
            "end_date": self.end_date,
        }
        with open(self.state_filename, "w", encoding="utf-8") as state_file:
            json.dump(state, state_file, ensure_ascii=False, indent=4)
        self.update_output(f"State saved to {self.state_filename}")

    def load_state(self):
        """Load the saved state from a JSON file."""
        if os.path.exists(self.state_filename):
            with open(self.state_filename, "r", encoding="utf-8") as state_file:
                state = json.load(state_file)
                self.last_post_shortcode = state.get("last_post_shortcode")
                self.start_date = state.get("start_date")
                self.end_date = state.get("end_date")
                self.update_output(f"Resumed from saved state: {state}")
        else:
            self.update_output("No saved state found. Starting fresh.")

    def countdown_timer(self, delay_seconds):
        """Show a countdown timer in the GUI and wait."""
        for remaining in range(delay_seconds, 0, -1):
            self.update_output(f"Resuming in {remaining} seconds...", overwrite=True)
            time.sleep(1)
        self.update_output("Resuming...", overwrite=True)

    def exponential_backoff(self, attempt):
        """Calculate the delay for exponential backoff."""
        base_delay = 60  # Base delay in seconds
        max_delay = 600  # Maximum delay in seconds
        delay = min(base_delay * (1.5 ** attempt), max_delay)
        self.update_output(f"Waiting for {delay} seconds before retrying...")
        time.sleep(delay)

    def scrape_profile(self):
        target_profile = self.target_profile_entry.get()
        username = self.username_entry.get()
        password = self.password_entry.get()
        scrape_comments = self.scrape_comments_var.get()

        # Load state if available
        self.load_state()

        if target_profile and self.start_date and self.end_date:
            self.update_output("Starting scraping process...")

            # Define JSON filename
            self.data_filename = f"{target_profile}.json"

            loader = instaloader.Instaloader()

            attempt = 0
            while attempt < 5:  # Retry up to 5 times
                try:
                    # Perform login
                    self.update_output("Logging in...")
                    loader.login(username, password)
                    self.update_output("Login successful")

                    # Load target profile data
                    profile = instaloader.Profile.from_username(loader.context, target_profile)
                    self.profile_data["profile"] = {
                        "username": profile.username,
                        "fullname": profile.full_name,
                        "bio": profile.biography,
                        "followers": profile.followers,
                        "following": profile.followees,
                        "posts": profile.mediacount
                    }

                    # Scrape posts
                    posts_scraped = 0
                    for post in profile.get_posts():
                        if post.date < datetime.strptime(self.start_date, '%Y-%m-%d') or post.date > datetime.strptime(self.end_date, '%Y-%m-%d'):
                            continue

                        post_details = {
                            "shortcode": post.shortcode,
                            "date": post.date.strftime('%Y-%m-%d %H:%M:%S'),
                            "caption": post.caption,
                            "likes": post.likes,
                            "comments": 0
                        }

                        # Save state after each post
                        self.last_post_shortcode = post.shortcode
                        self.save_state()

                        try:
                            self.update_output(f"Scraping post {post.date.strftime('%Y-%m-%d %H:%M:%S')}")
                            posts_scraped += 1
                        except instaloader.exceptions.BadResponseException as e:
                            self.update_output(f"Bad Response Exception for post {post.date.strftime('%Y-%m-%d %H:%M:%S')}: {e}")
                            self.handle_bad_request_error(post.shortcode)
                            continue  # Skip to the next post

                        # Scrape comments if enabled
                        if scrape_comments:
                            try:
                                comments = []
                                for comment in post.get_comments():
                                    comments.append({
                                        "comment": comment.text,
                                        "commenter": comment.owner.username
                                    })
                                post_details["comments"] = comments
                                self.update_output(f"Scraped comments for post {post.date.strftime('%Y-%m-%d %H:%M:%S')}")
                            except Exception as e:
                                self.update_output(f"Error scraping comments for post {post.date.strftime('%Y-%m-%d %H:%M:%S')}: {e}")

                        # Update profile data
                        self.profile_data["posts"].append(post_details)

                        # Save data after each post
                        self.save_data()

                        # Handle rate limit errors
                        if posts_scraped % 10 == 0:  # Example threshold
                            self.handle_rate_limit()

                        self.random_scroll()  # Add random scrolling

                    self.update_output(f"Scraped {posts_scraped} posts from {target_profile}")
                    self.save_data()
                    break  # Exit retry loop on success

                except instaloader.exceptions.InstaloaderException as e:
                    if "checkpoint_required" in str(e).lower():
                        self.update_output("Checkpoint required. Please log in manually and solve the CAPTCHA.")
                        self.save_state()  # Save state before pausing
                        messagebox.showinfo("Manual Login Required", 
                            "A checkpoint is required. Please log in manually and solve any CAPTCHA. Afterward, click OK to resume scraping.")
                        self.resume_scraping(self.last_post_shortcode)
                        break
                    else:
                        self.update_output(f"Instaloader Exception encountered: {e}")
                        attempt += 1
                        self.exponential_backoff(attempt)  # Wait before retrying
                except Exception as e:
                    self.update_output(f"Unexpected error: {e}")
                    break

    def handle_rate_limit(self):
        """Handle rate limit errors by waiting and retrying."""
        self.update_output("Encountered rate limit error. Waiting before retrying...")
        delay_seconds = random.randint(120, 300)  # Wait between 2 and 5 minutes
        self.countdown_timer(delay_seconds)
        self.update_output("Resuming scraping...")

    def handle_bad_request_error(self, last_post_shortcode):
        """Handle Bad Response errors by waiting and resuming."""
        self.update_output("Encountered a Bad Response error. Waiting before retrying...")
        delay_seconds = random.randint(60, 120)  # Wait between 1 and 2 minutes
        self.countdown_timer(delay_seconds)
        self.update_output("Resuming scraping...")
        self.resume_scraping(last_post_shortcode)

    def resume_scraping(self, last_post_shortcode):
        """Resume scraping from the last successful post."""
        self.update_output(f"Resuming scraping from post {last_post_shortcode}...")
        self.start_scraping()  # Restart scraping process

    def handle_exit(self, signum, frame):
        """Handle exit signals to clean up resources."""
        self.update_output("Exiting gracefully...")
        sys.exit(0)

# Main function to run the app
if __name__ == "__main__":
    root = Tk()
    app = InstagramScraperApp(root)
    root.mainloop()
