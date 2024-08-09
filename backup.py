import time
import requests
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from textblob import TextBlob
from tkinter import Tk, Label, Entry, Button, messagebox

class InstagramScraper:
    def __init__(self):
        self.driver = self.prepare_browser()
        self.wait = WebDriverWait(self.driver, 10)

    def prepare_browser(self):
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        service = Service(executable_path=r"C:\Users\rishi\Desktop\scrapescrape\chromedriver.exe")  # Update path
        return webdriver.Chrome(service=service, options=options)

    def scrape_profile(self, profile_username):
        try:
            self.driver.get(f"https://www.instagram.com/{profile_username}/")
            self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "article div img")))

            self.scroll_down()

            posts = self.driver.find_elements(By.CSS_SELECTOR, "article div img")
            all_comments = []
            for post in posts:
                try:
                    self.driver.execute_script("arguments[0].click();", post)
                    self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "img.FFVAD")))

                    # Extract post details
                    comments_elements = self.driver.find_elements(By.CSS_SELECTOR, "ul.Mr508 span")
                    comments = [comment.text for comment in comments_elements]
                    all_comments.extend(comments)

                    self.driver.back()
                    self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "article div img")))
                except TimeoutException:
                    print(f"Error loading post: {post.get_attribute('src')}")

            return all_comments
        except TimeoutException as e:
            print(f"TimeoutException: {e}")
            print(f"Page source: {self.driver.page_source}")
        except Exception as e:
            print(f"An error occurred while scraping profile: {e}")
        finally:
            self.driver.quit()

    def scrape_contact_info(self, username):
        try:
            self.driver.get(f"https://www.instagram.com/{username}/")
            self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "meta[property='og:description']")))

            bio_element = self.driver.find_element(By.CSS_SELECTOR, "div.-vDIg span")
            bio_text = bio_element.text

            contact_info = {
                "bio": bio_text,
            }
            
            print(f"Bio: {bio_text}")

            return contact_info
        except Exception as e:
            print(f"An error occurred while scraping contact info: {e}")
        finally:
            self.driver.quit()

    def scrape_followers_following(self, username, list_type):
        try:
            self.driver.get(f"https://www.instagram.com/{username}/")
            self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "a[href$='followers/']")))

            if list_type == "followers":
                link = self.driver.find_element(By.CSS_SELECTOR, "a[href$='followers/']")
            elif list_type == "following":
                link = self.driver.find_element(By.CSS_SELECTOR, "a[href$='following/']")
            else:
                raise ValueError("Invalid list_type. Use 'followers' or 'following'.")

            link.click()
            time.sleep(2)  # Wait for the modal to load

            modal = self.driver.find_element(By.CSS_SELECTOR, "div[role='dialog'] ul")
            self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "li div div span a")))

            user_elements = modal.find_elements(By.CSS_SELECTOR, "li div div span a")
            users = [user.text for user in user_elements]

            print(f"{list_type.capitalize()}: {users}")
            return users
        except TimeoutException as e:
            print(f"TimeoutException: {e}")
            print(f"Page source: {self.driver.page_source}")
        except Exception as e:
            print(f"An error occurred while scraping {list_type}: {e}")
        finally:
            self.driver.quit()

    def download_reels(self, username):
        try:
            self.driver.get(f"https://www.instagram.com/{username}/")
            self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "a[href$='reels/']")))

            reels_link = self.driver.find_element(By.CSS_SELECTOR, "a[href$='reels/']")
            reels_link.click()
            time.sleep(2)

            reel_elements = self.driver.find_elements(By.CSS_SELECTOR, "article div img")
            for reel in reel_elements:
                reel_url = reel.getAttribute("src")
                print(f"Reel URL: {reel_url}")

                response = requests.get(reel_url)
                with open(f"reel_{time.time()}.mp4", "wb") as file:
                    file.write(response.content)
        except Exception as e:
            print(f"An error occurred while downloading reels: {e}")
        finally:
            self.driver.quit()

    def download_photos_videos(self, username):
        try:
            self.driver.get(f"https://www.instagram.com/{username}/")
            self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "article div img")))

            self.scroll_down()

            media_elements = self.driver.find_elements(By.CSS_SELECTOR, "article div img, article div video")
            for media in media_elements:
                media_url = media.get_attribute("src")
                media_type = 'photo' if 'video' not in media.tag_name else 'video'
                print(f"{media_type.capitalize()} URL: {media_url}")

                response = requests.get(media_url)
                with open(f"{media_type}_{time.time()}.{'jpg' if media_type == 'photo' else 'mp4'}", "wb") as file:
                    file.write(response.content)
        except Exception as e:
            print(f"An error occurred while downloading photos and videos: {e}")
        finally:
            self.driver.quit()

    def scroll_down(self):
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        while True:
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height

    def perform_sentiment_analysis(self, comments):
        results = []
        for comment in comments:
            analysis = TextBlob(comment)
            sentiment = analysis.sentiment.polarity
            results.append({
                "comment": comment,
                "sentiment": sentiment
            })
        return results

    def save_to_spreadsheet(self, data, filename="comments_sentiment.xlsx"):
        df = pd.DataFrame(data)
        df.to_excel(filename, index=False)

    def quit(self):
        self.driver.quit()

class InstagramApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Instagram Scraper")

        self.label = Label(root, text="Enter Instagram Username:")
        self.label.pack()

        self.username_entry = Entry(root)
        self.username_entry.pack()

        self.scrape_button = Button(root, text="Scrape Profile", command=self.scrape_profile)
        self.scrape_button.pack()

        self.download_button = Button(root, text="Download Media", command=self.download_media)
        self.download_button.pack()

        self.contact_button = Button(root, text="Scrape Contact Info", command=self.scrape_contact_info)
        self.contact_button.pack()

        self.followers_button = Button(root, text="Scrape Followers", command=self.scrape_followers)
        self.followers_button.pack()

        self.following_button = Button(root, text="Scrape Following", command=self.scrape_following)
        self.following_button.pack()

        self.sentiment_button = Button(root, text="Analyze Comments Sentiment", command=self.analyze_comments_sentiment)
        self.sentiment_button.pack()

    def scrape_profile(self):
        username = self.username_entry.get()
        if username:
            scraper = InstagramScraper()
            comments = scraper.scrape_profile(username)
            if comments:
                sentiments = scraper.perform_sentiment_analysis(comments)
                scraper.save_to_spreadsheet(sentiments)
                messagebox.showinfo("Success", f"Profile data for {username} has been saved.")
            scraper.quit()
        else:
            messagebox.showerror("Error", "Please enter a username.")

    def download_media(self):
        username = self.username_entry.get()
        if username:
            scraper = InstagramScraper()
            scraper.download_photos_videos(username)
            scraper.download_reels(username)
            scraper.quit()
            messagebox.showinfo("Success", "Media has been downloaded.")
        else:
            messagebox.showerror("Error", "Please enter a username.")

    def scrape_contact_info(self):
        username = self.username_entry.get()
        if username:
            scraper = InstagramScraper()
            contact_info = scraper.scrape_contact_info(username)
            scraper.quit()
            messagebox.showinfo("Contact Info", f"Contact info: {contact_info}")
        else:
            messagebox.showerror("Error", "Please enter a username.")

    def scrape_followers(self):
        username = self.username_entry.get()
        if username:
            scraper = InstagramScraper()
            followers = scraper.scrape_followers_following(username, "followers")
            scraper.quit()
            messagebox.showinfo("Followers", f"Followers: {followers}")
        else:
            messagebox.showerror("Error", "Please enter a username.")

    def scrape_following(self):
        username = self.username_entry.get()
        if username:
            scraper = InstagramScraper()
            following = scraper.scrape_followers_following(username, "following")
            scraper.quit()
            messagebox.showinfo("Following", f"Following: {following}")
        else:
            messagebox.showerror("Error", "Please enter a username.")

    def analyze_comments_sentiment(self):
        username = self.username_entry.get()
        if username:
            scraper = InstagramScraper()
            comments = scraper.scrape_profile(username)
            if comments:
                sentiments = scraper.perform_sentiment_analysis(comments)
                scraper.save_to_spreadsheet(sentiments)
                messagebox.showinfo("Success", f"Sentiment analysis for {username} has been saved.")
            scraper.quit()
        else:
            messagebox.showerror("Error", "Please enter a username.")

if __name__ == "__main__":
    root = Tk()
    app = InstagramApp(root)
    root.mainloop()
