import instaloader
import json
import os
from tkinter import Tk, Label, Entry, Button, Text, Scrollbar, VERTICAL, Y, END, messagebox, Checkbutton, IntVar

class InstagramScraperApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Instagram Scraper")

        # Create and pack GUI components
        self.label_username = Label(root, text="Enter Instagram Username:")
        self.label_username.pack()

        self.username_entry = Entry(root)
        self.username_entry.pack()

        self.label_ig_password = Label(root, text="Your Instagram Password:")
        self.label_ig_password.pack()

        self.ig_password_entry = Entry(root, show='*')
        self.ig_password_entry.pack()

        self.show_password_var = IntVar()
        self.show_password_check = Checkbutton(root, text="Show Password", variable=self.show_password_var, command=self.toggle_password_visibility)
        self.show_password_check.pack()

        self.scrape_button = Button(root, text="Login and Scrape", command=self.scrape_profile)
        self.scrape_button.pack()

        self.output_text = Text(root, wrap='word', height=20, width=80)
        self.output_text.pack()

        # Add a scrollbar to the Text widget
        self.scrollbar = Scrollbar(root, orient=VERTICAL, command=self.output_text.yview)
        self.output_text.configure(yscrollcommand=self.scrollbar.set)
        self.scrollbar.pack(side='right', fill=Y)

    def toggle_password_visibility(self):
        if self.show_password_var.get():
            self.ig_password_entry.config(show='')
        else:
            self.ig_password_entry.config(show='*')

    def scrape_profile(self):
        username = self.username_entry.get()
        ig_password = self.ig_password_entry.get()

        if username and ig_password:
            self.output_text.delete(1.0, END)  # Clear previous content

            loader = instaloader.Instaloader(dirname_pattern=f"{username}_media")

            try:
                # Login to Instagram
                loader.login(username, ig_password)

                # Load profile data
                profile = instaloader.Profile.from_username(loader.context, username)
                profile_data = {"profile": {}, "posts": []}

                # Store profile details
                profile_data["profile"] = {
                    "username": profile.username,
                    "full_name": profile.full_name,
                    "bio": profile.biography,
                    "followers": profile.followers,
                    "following": profile.followees,
                    "number_of_posts": profile.mediacount,
                }

                # Display profile details in the GUI
                profile_details = (
                    f"Username: {profile.username}\n"
                    f"Full Name: {profile.full_name}\n"
                    f"Bio: {profile.biography}\n"
                    f"Followers: {profile.followers}\n"
                    f"Following: {profile.followees}\n"
                    f"Number of Posts: {profile.mediacount}\n"
                )
                self.output_text.insert(END, profile_details)

                # Scrape posts and download media
                for post in profile.get_posts():
                    post_details = {
                        "post_date": str(post.date),
                        "caption": post.caption,
                        "likes": post.likes,
                        "comments_count": post.comments,
                        "shortcode": post.shortcode,
                    }

                    # Download post media
                    loader.download_post(post, target=profile.username)

                    # Collect comments
                    comments = []
                    for comment in post.get_comments():
                        comments.append({
                            "comment_text": comment.text,
                            "comment_date": str(comment.created_at_utc),  # Corrected attribute
                            "commenter_username": comment.owner.username,
                        })
                    post_details["comments"] = comments

                    # Append post details to profile data
                    profile_data["posts"].append(post_details)

                    # Display post summary in the GUI
                    self.output_text.insert(END, f"Downloaded post from {post.date}\n")

                # Save data to JSON file
                with open(f"{username}_data.json", "w") as json_file:
                    json.dump(profile_data, json_file, indent=4)

                self.output_text.insert(END, f"\nData saved to {username}_data.json")

            except instaloader.exceptions.BadCredentialsException:
                messagebox.showerror("Login Error", "Incorrect username or password.")
            except instaloader.exceptions.TwoFactorAuthRequiredException:
                messagebox.showerror("Login Error", "Two-factor authentication is required. Please disable it temporarily.")
            except Exception as e:
                self.output_text.insert(END, f"An error occurred: {e}")

        else:
            messagebox.showerror("Input Error", "Please enter both username and password.")

if __name__ == "__main__":
    root = Tk()
    app = InstagramScraperApp(root)
    root.mainloop()
