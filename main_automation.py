import os
import random
import string
import json
import time
from datetime import datetime
from playwright.sync_api import sync_playwright, Page
from playwright_stealth import stealth_sync
from queue import Queue
import threading
from typing import Dict
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('casino_automation.log'),
        logging.StreamHandler()
    ]
)

class CasinoAutomation:
    def __init__(self):
        self.blacklisted_sites = [
            "Prive Casino",
            "Fast Slots Casino", # Cloudflare protected site
            "Casino Extra", # Cloudflare protected site
            "spinsino",
            "Jinxcasino",
            "Slottio",
            "Casineia",
            "Gamblii",
            "Gxmble",
            "Winstler",
            "Seven Casino",
            "Palm Casino",
            "Mad Casino",
            "Lucki Casino",
            "Spintowin",
            "Luckzie",
            "Casmiro",
            "Jokersino",
            "Spintime",
            "Slothive",
        ]
        
        self.country_codes = {
            "Netherlands": "nl",
            "France": "fr",
            "Sweden": "se",
            "United Kingdom": "gb"
        }
        
        self.urls = {
            "United Kingdom": {
                "newhorrizon": "https://newhorrizon.eu/",
            },
            "Netherlands": {
                "onlinecasinosspelen": "https://nl.onlinecasinosspelen.com/",
                "casinojager": "https://www.casinojager.com/casinos/",
                "topcasinosites": "https://topcasinosites.eu/biz-best-casinos/",
                "1337games": "https://www.1337games.io/online-casinos/zonder-cruks/",
                "superbigwin": "https://www.superbigwin.nu/casino-zonder-cruks/",
                "unlockedcasinos": "https://unlockedcasinos.com/",
            },
            "France": {
                "alliance": "https://www.alliance-francaise-des-designers.org/",
                "fr_jeux": "https://fr.jeux.fm/",
                "lucky_7": "https://lucky-7-bonus.fr/",
                "joueraucasino": "https://www.joueraucasino.com/casinos-en-ligne/jeux.ca",
            },
            "Sweden": {
                "topcasinoslistings": "https://topcasinoslistings.com/",
                "internationalcasino": "https://internationalcasino.io/",
                "internationalcasinos": "https://internationalcasinos.com/",
                "hugovegas": "https://hugovegas.com/foreign-casinos",
                "casinoquest": "https://casinoquest.bet/se/?transfer=1",
                "yournextbigwin": "https://yournextbigwin.com/se/",
            },
        }
        self.image_folder = os.path.join(os.path.dirname(__file__), "static", "Images")
        os.makedirs(self.image_folder, exist_ok=True)
        self.stats_file = os.path.join(os.path.dirname(__file__), "data", "stats.json")
        self.task_queue = Queue()
        self.active_threads = []
        self.running = True
        self.stats_lock = threading.Lock()
        self.ensure_stats_file_exists()

    def ensure_stats_file_exists(self):
        """Ensure the stats file exists and has proper structure."""
        os.makedirs(os.path.dirname(self.stats_file), exist_ok=True)
        if not os.path.exists(self.stats_file):
            with open(self.stats_file, 'w') as f:
                json.dump({"clicks": {}, "history": [], "Screenshot": {}}, f, indent=2)

    def update_stats(self, casino_name: str, affiliate_name: str, image_path: str = None):
        """Thread-safe update of statistics."""
        with self.stats_lock:
            try:
                with open(self.stats_file, 'r') as f:
                    stats = json.load(f)
                
                stats["clicks"][casino_name] = stats["clicks"].get(casino_name, 0) + 1
                
                # Include screenshot in history entry
                history_entry = {
                    "affiliate": affiliate_name,
                    "casino": casino_name,
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                if image_path:
                    stats["Screenshot"][casino_name] = image_path
                
                stats["history"].append(history_entry)
                
                with open(self.stats_file, 'w') as f:
                    json.dump(stats, f, indent=2)
                
                logging.info(f"Stats updated for {casino_name}")
            except Exception as e:
                logging.error(f"Error updating stats: {e}")

    def configure_browser(self, country: str) -> Dict:
        """Configure browser settings including proxy."""
        random_session = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
        country_code = self.country_codes.get(country, "nl")
        
        return {
            "proxy": {
                "server": "residential-ww.catproxies.com:16666",
                "username": f"xopgtkstyrlikxz127239-zone-resi-region-{country_code}-session-{random_session}-sesTime-15",
                "password": "zngwzvmanv"
            },
            "headless": True,
        }

    def process_casino_site(self, country: str, site_name: str, url: str):
        """Process a single casino site."""
        logging.info(f"Processing {site_name} for {country}")
        browser_config = self.configure_browser(country)
        
        try:
            with sync_playwright() as p:
                browser = p.firefox.launch(**browser_config)
                context = browser.new_context(
                    viewport={'width': 390, 'height': 844},
                    user_agent='Mozilla/5.0 (iPhone; CPU iPhone OS 14_7_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Mobile/15E148 Safari/604.1'
                )
                
                stealth_sync(context)
                page = context.new_page()
                page.set_default_navigation_timeout(300000)
                # Navigate to the site
                if "lucky_7" in site_name:
                    page.goto(url, wait_until="load", timeout=60000000)
                else:
                    page.goto(url, wait_until="networkidle", timeout=60000000)
                # Handle cookie consent
                self.handle_cookie_consent(page)
                
                # Process the site based on the site name
                handler_method = getattr(self, f"handle_{site_name}", None)
                if handler_method:
                    selected_casino = handler_method(page)
                    if selected_casino:
                        image_filename = f"{selected_casino}.png"
                        # Store the relative path
                        relative_image_path = os.path.join("static", "Images", image_filename)
                        self.update_stats(selected_casino, site_name, relative_image_path)
                else:
                    logging.warning(f"No handler found for {site_name}")
                
                # Clean up
                browser.close()
                
        except Exception as e:
            logging.error(f"Error processing {site_name}: {e}")

    def handle_cookie_consent(self, page: Page):
        """Handle cookie consent dialogs."""
        try:
            accept_button = page.get_by_role("button", name="Accept all")
            if accept_button.is_visible(timeout=3000):
                accept_button.click()
                page.wait_for_timeout(1000)
        except Exception:
            logging.info("No cookie dialog or already accepted")

    def worker(self):
        """Worker thread to process tasks from the queue."""
        while self.running:
            try:
                task = self.task_queue.get(timeout=1)
                if task:
                    country, site_name, url = task
                    self.process_casino_site(country, site_name, url)
                self.task_queue.task_done()
            except self.task_queue.qsize() == 0:
                continue
            except Exception as e:
                logging.error(f"Worker error: {e}")

    def start(self, num_threads: int = 3):
        """Start the automation with specified number of threads."""
        logging.info(f"Starting automation with {num_threads} threads")
        
        # Create worker threads
        self.active_threads = []
        for _ in range(num_threads):
            thread = threading.Thread(target=self.worker)
            thread.daemon = True
            thread.start()
            self.active_threads.append(thread)
        
        # Add tasks to queue
        for country, sites in self.urls.items():
            for site_name, url in sites.items():
                self.task_queue.put((country, site_name, url))
        
        # Wait for all tasks to complete
        self.task_queue.join()

    def stop(self):
        """Stop the automation gracefully."""
        self.running = False
        for thread in self.active_threads:
            thread.join()
        logging.info("Automation stopped")

    def weighted_random_choice(self, items):
        """
        Choose a random item from a list with linearly increasing weights. The first item has weight 1, the second 2, etc. 
        Items at the beginning of the list are more likely to be chosen.

        Args:
            items (list): List of items to choose from

        Returns:
            object: The randomly chosen item
        """
        weights = [i + 1 for i in range(len(items))]  # Weights increase linearly with index
        total_weight = sum(weights)
        rand_num = random.uniform(0, total_weight)
        cumulative_weight = 0
        for i, item in enumerate(items):
            cumulative_weight += weights[i]
            if rand_num <= cumulative_weight:
                return item
        return items[-1]
    
    # ================NETHERLANDS================
    def handle_casinojager(self, page: Page):
        """Find and click a random signup button on the page excluding blacklisted sites."""

        page.wait_for_selector('[id="result-container"]', timeout=300000)
        #[data-action="more-casinos"]
        more_casinos_element = page.locator('[data-action="more-casinos"]')
        total_pages = page.locator('[data-action="more-casinos"]').get_attribute("data-total-pages")
        next_page_elements = page.locator('[data-action="more-casinos"]').get_attribute("data-next-page")
        
        while total_pages != next_page_elements:
            try:
                more_casinos_element = page.locator('[data-action="more-casinos"]')
                more_casinos_element.click()
                page.locator('[data-action="more-casinos"]').wait_for(5000)
                total_pages = page.locator('[data-action="more-casinos"]').get_attribute("data-total-pages")
                next_page_elements = page.locator('[data-action="more-casinos"]').get_attribute("data-next-page")
            except:
                break
        signup_elements = page.locator('.hentry.casino > div:last-child a').all()

        print("Available signup buttons on the page:", end="")
        for element in signup_elements:
            offer_name = element.get_attribute("data-operator")
            if offer_name in self.blacklisted_sites:
                print(f"\033[91m{offer_name}\033[0m", end=", ")
            else:
                print(f"\033[92m{offer_name}\033[0m", end=", ")
        print()

        filtered_elements = []
        casino_names = []

        for element in signup_elements:
            casino_name = element.get_attribute("data-operator")
            if casino_name not in self.blacklisted_sites:
                filtered_elements.append(element)
                casino_names.append(casino_name)

        if not filtered_elements:
            raise Exception("No suitable signup buttons found")

        # Choose a random casino
        random_signup_button = self.weighted_random_choice(filtered_elements)
        selected_casino = casino_names[filtered_elements.index(random_signup_button)]

        print(f"Selected casino: {selected_casino}")
        random_signup_button.click(force=True)
        try:
            with page.context.expect_page(timeout=60000) as new_page_info:
                pass  # This block will execute if a new page is created
            new_page = new_page_info.value
            print("New tab opened, waiting for it to load...")
            new_page.wait_for_load_state("networkidle", timeout=120000)
            page.close()  # Close the original page
            page = new_page  # Switch to the new page
            print("New tab loaded.")
        except TimeoutError:
            # No new tab, assume same-tab navigation
            print("No new tab opened, waiting for same-tab navigation...")
            page.wait_for_load_state("networkidle", timeout=120000)
            print("Same tab loaded.")
        except Exception as e:
            print(f"Error waiting for navigation: {e}")
            
        # Update statistics
        screenshot_bytes = page.screenshot(timeout=600000)
        image_filename = f"{selected_casino}.png"
        image_path = os.path.join(self.image_folder, image_filename)
        with open(image_path, "wb") as f:
            f.write(screenshot_bytes)
        #self.update_stats(selected_casino, "casinojager")
        return selected_casino
    
    def handle_topcasinosites(self, page: Page):
        """Find and click a random signup button on the page excluding blacklisted sites."""

        page.wait_for_selector('[class*="campaign__voting_list"]', timeout=300000)
        
        signup_elements = page.locator('[data-offer-name*=" "]').all()

        print("Available signup buttons on the page:", end="")
        for element in signup_elements:
            offer_name = element.get_attribute("data-offer-name")
            if offer_name in self.blacklisted_sites:
                print(f"\033[91m{offer_name}\033[0m", end=", ")
            else:
                print(f"\033[92m{offer_name}\033[0m", end=", ")
        print()

        filtered_elements = []
        casino_names = []

        for element in signup_elements:
            casino_name = element.get_attribute("data-offer-name")
            if casino_name not in self.blacklisted_sites:
                filtered_elements.append(element.locator('a').last)
                casino_names.append(casino_name)

        if not filtered_elements:
            raise Exception("No suitable signup buttons found")

        # Choose a random casino
        random_signup_button = self.weighted_random_choice(filtered_elements)
        selected_casino = casino_names[filtered_elements.index(random_signup_button)]

        print(f"Selected casino: {selected_casino}")
        random_signup_button.click(force=True)
        try:
            with page.context.expect_page(timeout=60000) as new_page_info:
                pass  # This block will execute if a new page is created
            new_page = new_page_info.value
            print("New tab opened, waiting for it to load...")
            new_page.wait_for_load_state("networkidle", timeout=120000)
            page.close()  # Close the original page
            page = new_page  # Switch to the new page
            print("New tab loaded.")
        except TimeoutError:
            # No new tab, assume same-tab navigation
            print("No new tab opened, waiting for same-tab navigation...")
            page.wait_for_load_state("networkidle", timeout=120000)
            print("Same tab loaded.")
        except Exception as e:
            print(f"Error waiting for navigation: {e}")

        # Update statistics
        screenshot_bytes = page.screenshot(timeout=600000)
        image_filename = f"{selected_casino}.png"
        image_path = os.path.join(self.image_folder, image_filename)
        with open(image_path, "wb") as f:
            f.write(screenshot_bytes)
        #self.update_stats(selected_casino, "topcasinosites")
        return selected_casino

    def handle_1337games(self, page: Page):
        """Find and click a random signup button on the page excluding blacklisted sites."""

        page.locator('a[class*="play play"]').first.wait_for(timeout=300000)
        
        signup_elements = page.locator('a[class*="play play"]').all()
        
        print("Available signup buttons on the page:", end="")
        for element in signup_elements:
            offer_name = element.get_attribute("href").split("/")[-1].strip()
            if offer_name in self.blacklisted_sites:
                print(f"\033[91m{offer_name}\033[0m", end=", ")
            else:
                print(f"\033[92m{offer_name}\033[0m", end=", ")
        print()

        filtered_elements = []
        casino_names = []

        for element in signup_elements:
            #href="https://www.1337games.io/go/nyxbetscruks"
            casino_name = element.get_attribute("href").split("/")[-1].strip()
            if casino_name not in self.blacklisted_sites:
                filtered_elements.append(element)
                casino_names.append(casino_name)

        if not filtered_elements:
            raise Exception("No suitable signup buttons found")

        # Choose a random casino
        random_signup_button = self.weighted_random_choice(filtered_elements)
        selected_casino = casino_names[filtered_elements.index(random_signup_button)]

        print(f"Selected casino: {selected_casino}")
        random_signup_button.click(force=True)
        try:
            with page.context.expect_page(timeout=60000) as new_page_info:
                pass  # This block will execute if a new page is created
            new_page = new_page_info.value
            print("New tab opened, waiting for it to load...")
            new_page.wait_for_load_state("networkidle", timeout=120000)
            page.close()  # Close the original page
            page = new_page  # Switch to the new page
            print("New tab loaded.")
        except TimeoutError:
            # No new tab, assume same-tab navigation
            print("No new tab opened, waiting for same-tab navigation...")
            page.wait_for_load_state("networkidle", timeout=120000)
            print("Same tab loaded.")
        except Exception as e:
            print(f"Error waiting for navigation: {e}")

        # Update statistics
        screenshot_bytes = page.screenshot(timeout=600000)
        image_filename = f"{selected_casino}.png"
        image_path = os.path.join(self.image_folder, image_filename)
        with open(image_path, "wb") as f:
            f.write(screenshot_bytes)
        #self.update_stats(selected_casino, "1337games")
        return selected_casino
    
    def handle_superbigwin(self, page: Page):
        """Find and click a random signup button on the page excluding blacklisted sites."""

        page.locator('[data-component="CTA List"]').first.wait_for(timeout=300000)
        
        signup_elements = page.locator('[data-component="CTA List"]').all()

        print("Available signup buttons on the page:", end="")
        for element in signup_elements:
            offer_name = element.get_attribute("href").split("/")[-1].strip()
            if offer_name in self.blacklisted_sites:
                print(f"\033[91m{offer_name}\033[0m", end=", ")
            else:
                print(f"\033[92m{offer_name}\033[0m", end=", ")
        print()

        filtered_elements = []
        casino_names = []

        for element in signup_elements:
            casino_name = element.get_attribute("href").split("/")[-1].strip()
            if casino_name not in self.blacklisted_sites:
                filtered_elements.append(element)
                casino_names.append(casino_name)

        if not filtered_elements:
            raise Exception("No suitable signup buttons found")

        # Choose a random casino
        random_signup_button = self.weighted_random_choice(filtered_elements)
        selected_casino = casino_names[filtered_elements.index(random_signup_button)]

        print(f"Selected casino: {selected_casino}")
        random_signup_button.click(force=True)
        try:
            with page.context.expect_page(timeout=60000) as new_page_info:
                pass  # This block will execute if a new page is created
            new_page = new_page_info.value
            print("New tab opened, waiting for it to load...")
            new_page.wait_for_load_state("networkidle", timeout=120000)
            page.close()  # Close the original page
            page = new_page  # Switch to the new page
            print("New tab loaded.")
        except TimeoutError:
            # No new tab, assume same-tab navigation
            print("No new tab opened, waiting for same-tab navigation...")
            page.wait_for_load_state("networkidle", timeout=120000)
            print("Same tab loaded.")
        except Exception as e:
            print(f"Error waiting for navigation: {e}")

        # Update statistics
        screenshot_bytes = page.screenshot(timeout=600000)
        image_filename = f"{selected_casino}.png"
        image_path = os.path.join(self.image_folder, image_filename)
        with open(image_path, "wb") as f:
            f.write(screenshot_bytes)
        #self.update_stats(selected_casino, "superbigwin")
        return selected_casino
    
    def handle_onlinecasinosspelen(self, page: Page):
        """Find and click a random signup button on the page excluding blacklisted sites."""

        page.wait_for_selector('[class="toplist-container"]', timeout=3000000)
        signup_elements = page.locator('[class="toplist-container"] tr').all()

        print("Available signup buttons on the page:", end="")
        for element in signup_elements:
            offer_name = element.locator("a").first.inner_text().strip()
            if offer_name in self.blacklisted_sites:
                print(f"\033[91m{offer_name}\033[0m", end=", ")
            else:
                print(f"\033[92m{offer_name}\033[0m", end=", ")
        print()

        filtered_elements = []
        casino_names = []

        for element in signup_elements:
            casino_name = element.locator("a").first.inner_text().strip()
            if casino_name not in self.blacklisted_sites:
                filtered_elements.append(element.locator("a").last)
                casino_names.append(casino_name)

        if not filtered_elements:
            raise Exception("No suitable signup buttons found")

        # Choose a random casino
        random_signup_button = self.weighted_random_choice(filtered_elements)
        selected_casino = casino_names[filtered_elements.index(random_signup_button)]
        
        print(f"Selected casino: {selected_casino}")
        random_signup_button.click(force=True)
        try:
            with page.context.expect_page(timeout=60000) as new_page_info:
                pass  # This block will execute if a new page is created
            new_page = new_page_info.value
            print("New tab opened, waiting for it to load...")
            new_page.wait_for_load_state("networkidle", timeout=120000)
            page.close()  # Close the original page
            page = new_page  # Switch to the new page
            print("New tab loaded.")
        except TimeoutError:
            # No new tab, assume same-tab navigation
            print("No new tab opened, waiting for same-tab navigation...")
            page.wait_for_load_state("networkidle", timeout=120000)
            print("Same tab loaded.")
        except Exception as e:
            print(f"Error waiting for navigation: {e}")

        #page.pause()
        # Update statistics
        screenshot_bytes = page.screenshot(timeout=600000)
        image_filename = f"{selected_casino}.png"
        image_path = os.path.join(self.image_folder, image_filename)
        with open(image_path, "wb") as f:
            f.write(screenshot_bytes)
        #self.update_stats(selected_casino, "onlinecasinosspelen")
        return selected_casino
    
    
    def handle_unlockedcasinos(self, page: Page):
        """Find and click a random signup button on the page excluding blacklisted sites."""

        page.wait_for_selector('[class="oxy-dynamic-list"]', timeout=300000)
        
        signup_elements = page.locator('[class="oxy-dynamic-list"] [class="ct-new-columns"]').all()

        print("Available signup buttons on the page:", end="")
        for element in signup_elements:
            offer_name = element.locator('span[class="ct-span"]').first.inner_text().strip()
            if offer_name in self.blacklisted_sites:
                print(f"\033[91m{offer_name}\033[0m", end=", ")
            else:
                print(f"\033[92m{offer_name}\033[0m", end=", ")
        print()

        filtered_elements = []
        casino_names = []

        for element in signup_elements:
            casino_name = element.locator('span[class="ct-span"]').first.inner_text().strip()
            if casino_name not in self.blacklisted_sites:
                filtered_elements.append(element.locator('[data-id*="link_button"]'))
                casino_names.append(casino_name)

        if not filtered_elements:
            raise Exception("No suitable signup buttons found")

        # Choose a random casino
        random_signup_button = self.weighted_random_choice(filtered_elements)
        selected_casino = casino_names[filtered_elements.index(random_signup_button)]

        print(f"Selected casino: {selected_casino}")
        random_signup_button.click(force=True)
        try:
            with page.context.expect_page(timeout=60000) as new_page_info:
                pass  # This block will execute if a new page is created
            new_page = new_page_info.value
            print("New tab opened, waiting for it to load...")
            new_page.wait_for_load_state("load", timeout=120000)
            page.close()  # Close the original page
            page = new_page  # Switch to the new page
            print("New tab loaded.")
        except TimeoutError:
            # No new tab, assume same-tab navigation
            print("No new tab opened, waiting for same-tab navigation...")
            page.wait_for_load_state("load", timeout=120000)
            print("Same tab loaded.")
        except Exception as e:
            print(f"Error waiting for navigation: {e}")
            
        # Update statistics
        screenshot_bytes = page.screenshot(timeout=600000)
        image_filename = f"{selected_casino}.png"
        image_path = os.path.join(self.image_folder, image_filename)
        with open(image_path, "wb") as f:
            f.write(screenshot_bytes)
        #self.update_stats(selected_casino, "casinojager")
        return selected_casino
    
    #===============UNITED KINGDOM================
    def handle_newhorrizon(self, page: Page):
        """Find and click a random signup button on the page excluding blacklisted sites."""
        
        page.wait_for_selector('div[data-offer-name] a[class="toplist-poker-compact__offer-cta-btn"]', timeout=300000)
        signup_elements = page.locator('div[data-offer-name]').all()
        
        print("Available signup buttons on the page:", end="")
        for element in signup_elements:
            offer_name = element.get_attribute("data-offer-name")
            if offer_name in self.blacklisted_sites:
                print(f"\033[91m{offer_name}\033[0m", end=", ")
            else:
                print(f"\033[92m{offer_name}\033[0m", end=", ")
        print()
        
        filtered_elements = []
        casino_names = []
        
        for element in signup_elements:
            casino_name = element.get_attribute("data-offer-name")
            if casino_name not in self.blacklisted_sites:
                filtered_elements.append(element.locator('a[class="toplist-poker-compact__offer-cta-btn"]'))
                casino_names.append(casino_name)
        
        if not filtered_elements:
            raise Exception("No suitable signup buttons found")
            
        # Choose a random casino
        random_signup_button = self.weighted_random_choice(filtered_elements)
        selected_casino = casino_names[filtered_elements.index(random_signup_button)]
        
        print(f"Selected casino: {selected_casino}")
        random_signup_button.click(force=True)
        try:
            with page.context.expect_page(timeout=60000) as new_page_info:
                pass  # This block will execute if a new page is created
            new_page = new_page_info.value
            print("New tab opened, waiting for it to load...")
            new_page.wait_for_load_state("networkidle", timeout=120000)
            page.close()  # Close the original page
            page = new_page  # Switch to the new page
            print("New tab loaded.")
        except TimeoutError:
            # No new tab, assume same-tab navigation
            print("No new tab opened, waiting for same-tab navigation...")
            page.wait_for_load_state("networkidle", timeout=120000)
            print("Same tab loaded.")
        except Exception as e:
            print(f"Error waiting for navigation: {e}")
        
        # Update statistics
        screenshot_bytes = page.screenshot(timeout=600000)
        image_filename = f"{selected_casino}.png"
        image_path = os.path.join(self.image_folder, image_filename)
        with open(image_path, "wb") as f:
            f.write(screenshot_bytes)
        #self.update_stats(selected_casino, "newhorrizon")
        return selected_casino
    
    #===============FRANCE================
    def handle_alliance(self, page: Page):
        """Find and click a random signup button on the page excluding blacklisted sites."""
        
        page.wait_for_selector('[class="toplist-poker-compact__offers"]', timeout=300000)
        signup_elements = page.locator('[class="toplist-poker-compact__offers"] [data-offer-name*=" "]').all()
        
        print("Available signup buttons on the page:", end="")
        for element in signup_elements:
            offer_name = element.get_attribute("data-offer-name")
            if offer_name in self.blacklisted_sites:
                print(f"\033[91m{offer_name}\033[0m", end=", ")
            else:
                print(f"\033[92m{offer_name}\033[0m", end=", ")
        print()
        
        filtered_elements = []
        casino_names = []
        
        for element in signup_elements:
            casino_name = element.get_attribute("data-offer-name")
            if casino_name not in self.blacklisted_sites:
                filtered_elements.append(element.locator('a[class="toplist-poker-compact__offer-cta-btn"]'))
                casino_names.append(casino_name)
        
        if not filtered_elements:
            raise Exception("No suitable signup buttons found")
            
        # Choose a random casino
        random_signup_button = self.weighted_random_choice(filtered_elements)
        selected_casino = casino_names[filtered_elements.index(random_signup_button)]
        
        print(f"Selected casino: {selected_casino}")
        random_signup_button.click(force=True)
        try:
            with page.context.expect_page(timeout=60000) as new_page_info:
                pass  # This block will execute if a new page is created
            new_page = new_page_info.value
            print("New tab opened, waiting for it to load...")
            new_page.wait_for_load_state("networkidle", timeout=120000)
            page.close()  # Close the original page
            page = new_page  # Switch to the new page
            print("New tab loaded.")
        except TimeoutError:
            # No new tab, assume same-tab navigation
            print("No new tab opened, waiting for same-tab navigation...")
            page.wait_for_load_state("networkidle", timeout=120000)
            print("Same tab loaded.")
        except Exception as e:
            print(f"Error waiting for navigation: {e}")
        
        # Update statistics
        screenshot_bytes = page.screenshot(timeout=600000)
        image_filename = f"{selected_casino}.png"
        image_path = os.path.join(self.image_folder, image_filename)
        with open(image_path, "wb") as f:
            f.write(screenshot_bytes)
        #self.update_stats(selected_casino, "newhorrizon")
        return selected_casino
    
    def handle_fr_jeux(self, page: Page):
        """Find and click a random signup button on the page excluding blacklisted sites."""
        
        page.wait_for_selector('[class="c-brand-table js-filtered-item "]', timeout=300000)
        more_button = page.locator('button[class="c-brand-table__more-btn js-more-brand o-action-btn o-active"]').all()
        if more_button:
            more_button[0].click()
        
        signup_elements = page.locator('[class="c-brand-table-item"]').all()
        
        print("Available signup buttons on the page:", end="")
        for element in signup_elements:
            offer_name = element.locator('[class="c-brand-table-item__name"]').inner_text().strip()
            if offer_name in self.blacklisted_sites:
                print(f"\033[91m{offer_name}\033[0m", end=", ")
            else:
                print(f"\033[92m{offer_name}\033[0m", end=", ")
        print()
        
        filtered_elements = []
        casino_names = []
        
        for element in signup_elements:
            casino_name = element.locator('[class="c-brand-table-item__name"]').inner_text().strip()
            if casino_name not in self.blacklisted_sites:
                filtered_elements.append(element.locator('[class="c-brand-table-item__button"] > a[class="o-play-btn"]'))
                casino_names.append(casino_name)
        
        if not filtered_elements:
            raise Exception("No suitable signup buttons found")
            
        # Choose a random casino
        random_signup_button = self.weighted_random_choice(filtered_elements)
        selected_casino = casino_names[filtered_elements.index(random_signup_button)]
        
        print(f"Selected casino: {selected_casino}")
        random_signup_button.click(force=True)
        try:
            with page.context.expect_page(timeout=60000) as new_page_info:
                pass  # This block will execute if a new page is created
            new_page = new_page_info.value
            print("New tab opened, waiting for it to load...")
            new_page.wait_for_load_state("networkidle", timeout=120000)
            page.close()  # Close the original page
            page = new_page  # Switch to the new page
            print("New tab loaded.")
        except TimeoutError:
            # No new tab, assume same-tab navigation
            print("No new tab opened, waiting for same-tab navigation...")
            page.wait_for_load_state("networkidle", timeout=120000)
            print("Same tab loaded.")
        except Exception as e:
            print(f"Error waiting for navigation: {e}")
        
        # Update statistics
        screenshot_bytes = page.screenshot(timeout=600000)
        image_filename = f"{selected_casino}.png"
        image_path = os.path.join(self.image_folder, image_filename)
        with open(image_path, "wb") as f:
            f.write(screenshot_bytes)
        #self.update_stats(selected_casino, "newhorrizon")
        return selected_casino
    
    def handle_lucky_7(self, page: Page):
        """Find and click a random signup button on the page excluding blacklisted sites."""
        
        page.wait_for_selector('[id="acceptCookies"]', timeout=300000)
        accept_cookies_button = page.locator('[id="acceptCookies"]')
        if accept_cookies_button:
            accept_cookies_button.click()
        page.locator('//a[@rel="noopener noreferrer" and  not(@title="Récupère ton bonus") and @type="internal"]').first.wait_for(timeout=300000)
        #ignore the first one 
        signup_elements = page.locator('//a[@rel="noopener noreferrer" and  not(@title="Récupère ton bonus") and @type="internal"]').all()
        
        print("Available signup buttons on the page:", end="")
        for element in signup_elements:
            offer_name = element.get_attribute("title")
            if offer_name in self.blacklisted_sites:
                print(f"\033[91m{offer_name}\033[0m", end=", ")
            else:
                print(f"\033[92m{offer_name}\033[0m", end=", ")
        print()
        
        filtered_elements = []
        casino_names = []
        
        for element in signup_elements:
            casino_name = element.get_attribute("title")
            if casino_name not in self.blacklisted_sites:
                filtered_elements.append(element)
                casino_names.append(casino_name)
        
        if not filtered_elements:
            raise Exception("No suitable signup buttons found")
            
        # Choose a random casino
        random_signup_button = self.weighted_random_choice(filtered_elements)
        selected_casino = casino_names[filtered_elements.index(random_signup_button)]
        
        print(f"Selected casino: {selected_casino}")
        random_signup_button.click(force=True)
        try:
            with page.context.expect_page(timeout=60000) as new_page_info:
                pass  # This block will execute if a new page is created
            new_page = new_page_info.value
            print("New tab opened, waiting for it to load...")
            new_page.wait_for_load_state("networkidle", timeout=120000)
            page.close()  # Close the original page
            page = new_page  # Switch to the new page
            print("New tab loaded.")
        except TimeoutError:
            # No new tab, assume same-tab navigation
            print("No new tab opened, waiting for same-tab navigation...")
            page.wait_for_load_state("networkidle", timeout=120000)
            print("Same tab loaded.")
        except Exception as e:
            print(f"Error waiting for navigation: {e}")
        
        # Update statistics
        screenshot_bytes = page.screenshot(timeout=600000)
        image_filename = f"{selected_casino}.png"
        image_path = os.path.join(self.image_folder, image_filename)
        with open(image_path, "wb") as f:
            f.write(screenshot_bytes)
        #self.update_stats(selected_casino, "newhorrizon")
        return selected_casino
    
    def handle_joueraucasino(self, page: Page):
        """Find and click a random signup button on the page excluding blacklisted sites."""
        
        page.wait_for_selector('[class="et_pb_text_inner"]', timeout=300000)
        #ignore the first one 
        signup_elements = page.locator('[class="jac-casino-item"]').all()
        
        print("Available signup buttons on the page:", end="")
        for element in signup_elements:
            offer_name = element.locator('a[data-bg-image]').get_attribute("title")
            if offer_name in self.blacklisted_sites:
                print(f"\033[91m{offer_name}\033[0m", end=", ")
            else:
                print(f"\033[92m{offer_name}\033[0m", end=", ")
        print()
        
        filtered_elements = []
        casino_names = []
        
        for element in signup_elements:
            casino_name = element.locator('a[data-bg-image]').get_attribute("title")
            if casino_name not in self.blacklisted_sites:
                filtered_elements.append(element.locator('[class="jac-cta-btn"]'))
                casino_names.append(casino_name)
        
        if not filtered_elements:
            raise Exception("No suitable signup buttons found")
            
        # Choose a random casino
        random_signup_button = self.weighted_random_choice(filtered_elements)
        selected_casino = casino_names[filtered_elements.index(random_signup_button)]
        
        print(f"Selected casino: {selected_casino}")
        random_signup_button.click(force=True)
        try:
            with page.context.expect_page(timeout=60000) as new_page_info:
                pass  # This block will execute if a new page is created
            new_page = new_page_info.value
            print("New tab opened, waiting for it to load...")
            new_page.wait_for_load_state("networkidle", timeout=120000)
            page.close()  # Close the original page
            page = new_page  # Switch to the new page
            print("New tab loaded.")
        except TimeoutError:
            # No new tab, assume same-tab navigation
            print("No new tab opened, waiting for same-tab navigation...")
            page.wait_for_load_state("networkidle", timeout=120000)
            print("Same tab loaded.")
        except Exception as e:
            print(f"Error waiting for navigation: {e}")
        
        # Update statistics
        screenshot_bytes = page.screenshot(timeout=600000)
        image_filename = f"{selected_casino}.png"
        image_path = os.path.join(self.image_folder, image_filename)
        with open(image_path, "wb") as f:
            f.write(screenshot_bytes)
        #self.update_stats(selected_casino, "newhorrizon")
        return selected_casino
    
    #===============SWEDEN================
    def handle_topcasinoslistings(self, page: Page):
        """Find and click a random signup button on the page excluding blacklisted sites."""
        
        page.wait_for_selector('[class="cards"]', timeout=300000)
        #ignore the first one 
        signup_elements = page.locator('[class="card casinoitem"]').all()
        
        print("Available signup buttons on the page:", end="")
        for element in signup_elements:
            offer_name = element.locator('[class="title"]').inner_text().strip()
            if offer_name in self.blacklisted_sites:
                print(f"\033[91m{offer_name}\033[0m", end=", ")
            else:
                print(f"\033[92m{offer_name}\033[0m", end=", ")
        print()
        
        filtered_elements = []
        casino_names = []
        
        for element in signup_elements:
            casino_name = element.locator('[class="title"]').inner_text().strip()
            if casino_name not in self.blacklisted_sites:
                filtered_elements.append(element.locator('[class="card__btn"] a'))
                casino_names.append(casino_name)
        
        if not filtered_elements:
            raise Exception("No suitable signup buttons found")
            
        # Choose a random casino
        random_signup_button = self.weighted_random_choice(filtered_elements)
        selected_casino = casino_names[filtered_elements.index(random_signup_button)]
        
        print(f"Selected casino: {selected_casino}")
        random_signup_button.click(force=True)
        try:
            with page.context.expect_page(timeout=60000) as new_page_info:
                pass  # This block will execute if a new page is created
            new_page = new_page_info.value
            print("New tab opened, waiting for it to load...")
            new_page.wait_for_load_state("networkidle", timeout=120000)
            page.close()  # Close the original page
            page = new_page  # Switch to the new page
            print("New tab loaded.")
        except TimeoutError:
            # No new tab, assume same-tab navigation
            print("No new tab opened, waiting for same-tab navigation...")
            page.wait_for_load_state("networkidle", timeout=120000)
            print("Same tab loaded.")
        except Exception as e:
            print(f"Error waiting for navigation: {e}")
        
        # Update statistics
        screenshot_bytes = page.screenshot(timeout=600000)
        image_filename = f"{selected_casino}.png"
        image_path = os.path.join(self.image_folder, image_filename)
        with open(image_path, "wb") as f:
            f.write(screenshot_bytes)
        #self.update_stats(selected_casino, "newhorrizon")
        return selected_casino
    
    def handle_internationalcasino(self, page: Page):
        """Find and click a random signup button on the page excluding blacklisted sites."""
        
        page.wait_for_selector('[class="casino-list"]', timeout=300000)
        #ignore the first one 
        signup_elements = page.locator('[class="casino-list"] [class="casino "]').all()
        
        print("Available signup buttons on the page:", end="")
        for element in signup_elements:
            offer_name = element.locator('[class="casino__name"]').inner_text().strip()
            if offer_name in self.blacklisted_sites:
                print(f"\033[91m{offer_name}\033[0m", end=", ")
            else:
                print(f"\033[92m{offer_name}\033[0m", end=", ")
        print()
        
        filtered_elements = []
        casino_names = []
        
        for element in signup_elements:
            casino_name = element.locator('[class="casino__name"]').inner_text().strip()
            if casino_name not in self.blacklisted_sites:
                filtered_elements.append(element.locator('a[class="btn btn_green"]'))
                casino_names.append(casino_name)
        
        if not filtered_elements:
            raise Exception("No suitable signup buttons found")
            
        # Choose a random casino
        random_signup_button = self.weighted_random_choice(filtered_elements)
        selected_casino = casino_names[filtered_elements.index(random_signup_button)]
        
        print(f"Selected casino: {selected_casino}")
        random_signup_button.click(force=True)
        try:
            with page.context.expect_page(timeout=60000) as new_page_info:
                pass  # This block will execute if a new page is created
            new_page = new_page_info.value
            print("New tab opened, waiting for it to load...")
            new_page.wait_for_load_state("networkidle", timeout=120000)
            page.close()  # Close the original page
            page = new_page  # Switch to the new page
            print("New tab loaded.")
        except TimeoutError:
            # No new tab, assume same-tab navigation
            print("No new tab opened, waiting for same-tab navigation...")
            page.wait_for_load_state("networkidle", timeout=120000)
            print("Same tab loaded.")
        except Exception as e:
            print(f"Error waiting for navigation: {e}")
        
        # Update statistics
        screenshot_bytes = page.screenshot(timeout=600000)
        image_filename = f"{selected_casino}.png"
        image_path = os.path.join(self.image_folder, image_filename)
        with open(image_path, "wb") as f:
            f.write(screenshot_bytes)
        #self.update_stats(selected_casino, "newhorrizon")
        return selected_casino
    
    def handle_internationalcasinos(self, page: Page):
        """Find and click a random signup button on the page excluding blacklisted sites."""
        
        page.wait_for_selector('[class="row-striping row-hover"]', timeout=300000)
        #ignore the first one 
        signup_elements = page.locator('[class="row-striping row-hover"] tr').all()
        
        print("Available signup buttons on the page:", end="")
        for element in signup_elements:
            offer_name = element.locator('[data-th="Rating"] strong').inner_text().split("\n")[0].strip()
            if offer_name in self.blacklisted_sites:
                print(f"\033[91m{offer_name}\033[0m", end=", ")
            else:
                print(f"\033[92m{offer_name}\033[0m", end=", ")
        print()
        
        filtered_elements = []
        casino_names = []
        
        for element in signup_elements:
            casino_name = element.locator('[data-th="Rating"] strong').inner_text().split("\n")[0].strip()
            if casino_name not in self.blacklisted_sites:
                filtered_elements.append(element.locator('[data-th="Play Now"] a'))
                casino_names.append(casino_name)
        
        if not filtered_elements:
            raise Exception("No suitable signup buttons found")
            
        # Choose a random casino
        random_signup_button = self.weighted_random_choice(filtered_elements)
        selected_casino = casino_names[filtered_elements.index(random_signup_button)]
        
        print(f"Selected casino: {selected_casino}")
        random_signup_button.click(force=True)
        try:
            with page.context.expect_page(timeout=60000) as new_page_info:
                pass  # This block will execute if a new page is created
            new_page = new_page_info.value
            print("New tab opened, waiting for it to load...")
            new_page.wait_for_load_state("networkidle", timeout=120000)
            page.close()  # Close the original page
            page = new_page  # Switch to the new page
            print("New tab loaded.")
        except TimeoutError:
            # No new tab, assume same-tab navigation
            print("No new tab opened, waiting for same-tab navigation...")
            page.wait_for_load_state("networkidle", timeout=120000)
            print("Same tab loaded.")
        except Exception as e:
            print(f"Error waiting for navigation: {e}")
        
        # Update statistics
        screenshot_bytes = page.screenshot(timeout=600000)
        image_filename = f"{selected_casino}.png"
        image_path = os.path.join(self.image_folder, image_filename)
        with open(image_path, "wb") as f:
            f.write(screenshot_bytes)
        #self.update_stats(selected_casino, "newhorrizon")
        return selected_casino
    
    def handle_hugovegas(self, page: Page):
        """Find and click a random signup button on the page excluding blacklisted sites."""
        
        page.wait_for_selector('[id="main"]', timeout=300000)
        #ignore the first one 
        signup_elements = page.locator('a[class*="play-now-button thirstylink"]').all()
        
        print("Available signup buttons on the page:", end="")
        for element in signup_elements:
            offer_name = element.get_attribute("title")
            if offer_name in self.blacklisted_sites:
                print(f"\033[91m{offer_name}\033[0m", end=", ")
            else:
                print(f"\033[92m{offer_name}\033[0m", end=", ")
        print()
        
        filtered_elements = []
        casino_names = []
        
        for element in signup_elements:
            casino_name = element.get_attribute("title")
            if casino_name not in self.blacklisted_sites:
                filtered_elements.append(element)
                casino_names.append(casino_name)
        
        if not filtered_elements:
            raise Exception("No suitable signup buttons found")
            
        # Choose a random casino
        random_signup_button = self.weighted_random_choice(filtered_elements)
        selected_casino = casino_names[filtered_elements.index(random_signup_button)]
        
        print(f"Selected casino: {selected_casino}")
        random_signup_button.click(force=True)
        try:
            with page.context.expect_page(timeout=60000) as new_page_info:
                pass  # This block will execute if a new page is created
            new_page = new_page_info.value
            print("New tab opened, waiting for it to load...")
            new_page.wait_for_load_state("networkidle", timeout=120000)
            page.close()  # Close the original page
            page = new_page  # Switch to the new page
            print("New tab loaded.")
        except TimeoutError:
            # No new tab, assume same-tab navigation
            print("No new tab opened, waiting for same-tab navigation...")
            page.wait_for_load_state("networkidle", timeout=120000)
            print("Same tab loaded.")
        except Exception as e:
            print(f"Error waiting for navigation: {e}")
        
        # Update statistics
        screenshot_bytes = page.screenshot(timeout=600000)
        image_filename = f"{selected_casino}.png"
        image_path = os.path.join(self.image_folder, image_filename)
        with open(image_path, "wb") as f:
            f.write(screenshot_bytes)
        #self.update_stats(selected_casino, "newhorrizon")
        return selected_casino
    
    def handle_casinoquest(self, page: Page):
        """Find and click a random signup button on the page excluding blacklisted sites."""
        
        page.wait_for_selector('[class="casino-page-v4__title"]', timeout=300000)
        more = page.locator('//div[contains(text(), "View More +")]').all()
        if more:
            more[0].click(timeout=300000)
        #ignore the first one 
        signup_elements = page.locator('[data-offer-name*=" "]').all()
        
        print("Available signup buttons on the page:", end="")
        for element in signup_elements:
            offer_name = element.get_attribute("data-offer-name")
            if offer_name in self.blacklisted_sites:
                print(f"\033[91m{offer_name}\033[0m", end=", ")
            else:
                print(f"\033[92m{offer_name}\033[0m", end=", ")
        print()
        
        filtered_elements = []
        casino_names = []
        
        for element in signup_elements:
            casino_name = element.get_attribute("data-offer-name")
            if casino_name not in self.blacklisted_sites:
                filtered_elements.append(element.locator('a').last)
                casino_names.append(casino_name)
        
        if not filtered_elements:
            raise Exception("No suitable signup buttons found")
            
        # Choose a random casino
        random_signup_button = self.weighted_random_choice(filtered_elements)
        selected_casino = casino_names[filtered_elements.index(random_signup_button)]
        
        print(f"Selected casino: {selected_casino}")
        random_signup_button.click(force=True)
        try:
            with page.context.expect_page(timeout=60000) as new_page_info:
                pass  # This block will execute if a new page is created
            new_page = new_page_info.value
            print("New tab opened, waiting for it to load...")
            new_page.wait_for_load_state("networkidle", timeout=120000)
            page.close()  # Close the original page
            page = new_page  # Switch to the new page
            print("New tab loaded.")
        except TimeoutError:
            # No new tab, assume same-tab navigation
            print("No new tab opened, waiting for same-tab navigation...")
            page.wait_for_load_state("networkidle", timeout=120000)
            print("Same tab loaded.")
        except Exception as e:
            print(f"Error waiting for navigation: {e}")
        
        # Update statistics
        screenshot_bytes = page.screenshot(timeout=600000)
        image_filename = f"{selected_casino}.png"
        image_path = os.path.join(self.image_folder, image_filename)
        with open(image_path, "wb") as f:
            f.write(screenshot_bytes)
        #self.update_stats(selected_casino, "newhorrizon")
        return selected_casino
    
    def handle_yournextbigwin(self, page: Page):
        """Find and click a random signup button on the page excluding blacklisted sites."""
        
        page.wait_for_selector('[class="site-logo__image"]', timeout=300000)
        more = page.locator('//div[contains(text(), "More Results +")]').all()
        if more:
            more[0].click(timeout=300000)
        #ignore the first one 
        signup_elements = page.locator('[data-offer-name*=" "]').all()
        
        print("Available signup buttons on the page:", end="")
        for element in signup_elements:
            offer_name = element.get_attribute("data-offer-name")
            if offer_name in self.blacklisted_sites:
                print(f"\033[91m{offer_name}\033[0m", end=", ")
            else:
                print(f"\033[92m{offer_name}\033[0m", end=", ")
        print()
        
        filtered_elements = []
        casino_names = []
        
        for element in signup_elements:
            casino_name = element.get_attribute("data-offer-name")
            if casino_name not in self.blacklisted_sites:
                filtered_elements.append(element.locator('a').last)
                casino_names.append(casino_name)
        
        if not filtered_elements:
            raise Exception("No suitable signup buttons found")
            
        # Choose a random casino
        random_signup_button = self.weighted_random_choice(filtered_elements)
        selected_casino = casino_names[filtered_elements.index(random_signup_button)]
        
        print(f"Selected casino: {selected_casino}")
        random_signup_button.click(force=True)
        try:
            with page.context.expect_page(timeout=60000) as new_page_info:
                pass  # This block will execute if a new page is created
            new_page = new_page_info.value
            print("New tab opened, waiting for it to load...")
            new_page.wait_for_load_state("networkidle", timeout=120000)
            page.close()  # Close the original page
            page = new_page  # Switch to the new page
            print("New tab loaded.")
        except TimeoutError:
            # No new tab, assume same-tab navigation
            print("No new tab opened, waiting for same-tab navigation...")
            page.wait_for_load_state("networkidle", timeout=120000)
            print("Same tab loaded.")
        except Exception as e:
            print(f"Error waiting for navigation: {e}")
        
        # Update statistics
        screenshot_bytes = page.screenshot(timeout=600000)
        image_filename = f"{selected_casino}.png"
        image_path = os.path.join(self.image_folder, image_filename)
        with open(image_path, "wb") as f:
            f.write(screenshot_bytes)
        #self.update_stats(selected_casino, "newhorrizon")
        return selected_casino
    
    def main(self, run_once=True, num_threads=3):
        """Main function to run the automation."""
        while self.running:
            automation = CasinoAutomation()
            try:
                automation.start(num_threads=3)
                if run_once:
                    break
                for _ in range(30):  # 30 second wait, checking every second if we should stop
                    if not self.running:
                        break
                    time.sleep(1)
            except KeyboardInterrupt:
                logging.info("Received keyboard interrupt, stopping...")
                automation.stop()
            except Exception as e:
                logging.error(f"Main error: {e}")
                automation.stop()
