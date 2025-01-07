from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from modules.profile_detail import get_profile_detail
from selenium.webdriver.support import expected_conditions as EC
from modules.store import get_datetime, logs,db_interactions
import os
import pandas as pd
import warnings
import random
from selenium.webdriver.common.action_chains import ActionChains
from bs4 import BeautifulSoup
import time

warnings.filterwarnings('ignore')

class get_profile:

    def __init__(
        self,
        driver,
        st,
        company,
        user_id,
        min_sleep=2,
        max_sleep=5,
    ):
        self.max_sleep = max_sleep
        self.min_sleep = min_sleep
        self.user_id=user_id

        self.o=db_interactions(user_id)

        self.company = company
        self.st = st

        self.associated_members=0

        self.driver=driver            

        self.driver.get(self.company)
         
        date, time_d = get_datetime().split()

        os.makedirs(".logs", exist_ok=True)

        open(r"errors_logs.txt", "a").write(f"\nDate - {date} Time - {time_d} - ")

    # ---------------------Next btn---------------------
    def nxt_btn(self):
        try:
            # Next btn
            next_button = WebDriverWait(self.driver, 30).until(
                EC.element_to_be_clickable(
                    (By.CSS_SELECTOR, "button[aria-label='Next']")
                )
            )
            next_button.click()
             
        except:
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            buttons = soup.find_all('button')
            for button in buttons:
                button_text = button.find('span', class_='artdeco-button__text')
                if button_text and 'Close your conversation' in button_text.get_text():
                    print('Found a conversation open')
                    self.driver.execute_script(f'document.getElementById("{button.get('id')}").click();')

            print("Error clicking next button")
            open(r"errors_logs.txt", "a").write("Error clicking next button")

    # --------------- Show more---------------
    def show_more(self):
        try:
            # Wait for the "Show more" button to be clickable
            show_more_button = WebDriverWait(self.driver, 30).until(
                EC.element_to_be_clickable(
                    (
                        By.XPATH,
                        "//button[contains(@class, 'org-people__show-more-button') and @aria-label='Show more people filters']",
                    )
                )
            )

            show_more_button.click()
            return "scrolled"

        except:
            open(r"errors_logs.txt", "a").write("Error while clicking more button")
            print("Error while clicking more button")
        
    # ------------------------------Filter Location------------------------
    def click_location(self, location_name="United States"):
        try:
            self.driver.execute_script(f"window.scrollBy(0, 20);")
            # Wait for the specific div to be present
            region_div = WebDriverWait(self.driver, 50).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "div.org-people-bar-graph-module__geo-region")
                )
            )

            # Find all button elements within that div
            button_elements = region_div.find_elements(
                By.CSS_SELECTOR, "button.org-people-bar-graph-element"
            )

            # Loop through each button to find and click on the specified location
            for button in button_elements:
                span = button.find_element(
                    By.CSS_SELECTOR, "span.org-people-bar-graph-element__category"
                )
                if (
                    span.text.lower() == location_name.lower()
                ):  # Check if it matches the desired location
                    button.click()  # Click the button
                    print(f"Selected Region as: {location_name}")
                    return  # Exit the method after clicking

            print(f"{location_name} button not found.")

        except Exception as e:
            print(f"Error locating elements in click_location")
            open(r"errors_logs.txt", "a").write(
                "Error locating elements in locations"
            )

        time_ = random.randint(self.min_sleep, self.max_sleep)
         
        time.sleep(time_)

    # ------------------------------- GoTo-------------------
    def check_title_and_click_next(self, title_):
        try:
            # Wait for the title element to be present
            title_element = WebDriverWait(self.driver, 30).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "div.insight-container__title h3")
                )
            )

            # Get the title text
            title_text = title_element.text

            if title_text != title_ or title_text == "":
                self.nxt_btn()
                self.check_title_and_click_next(title_)
            else:
                time_ = random.randint(self.min_sleep, self.max_sleep)
                 
                time.sleep(time_)

        except:
            print(f"Error during title check or clicking the 'Next' button")
            open(r"errors_logs.txt", "a").write(
                "Error during title check or clicking the 'Next' button"
            )

    # -------------------------------------- Professions List -----------------
    def get_specific_job_categories(self):
        try:
            # Wait for the buttons to be present
            buttons = WebDriverWait(self.driver, 20).until(
                EC.presence_of_all_elements_located(
                    (By.CSS_SELECTOR, "button.org-people-bar-graph-element")
                )
            )

            job_categories = []
            for button in buttons:
                category = button.find_element(
                    By.CSS_SELECTOR, "span.org-people-bar-graph-element__category"
                ).text
                job_categories.append(category)

            return job_categories

        except:
            print(f"Error locating job categories")
            open(r"errors_logs.txt", "a").write("Error locating job categories")
            return []

    # -----------------------------------Select department--------------------------
    def click_profession_button(self, profession):
        try:
            # Wait for the profession buttons to be present
            buttons = WebDriverWait(self.driver, 30).until(
                EC.presence_of_all_elements_located(
                    (By.CSS_SELECTOR, "button.org-people-bar-graph-element")
                )
            )

            # Loop through each button and check for the profession
            for button in buttons:
                # Get the category text from the button
                category_text = button.find_element(
                    By.CSS_SELECTOR, "span.org-people-bar-graph-element__category"
                ).text

                # print(category_text)
                # Check if the category matches the provided profession
                if category_text.lower() == profession.lower():
                    # Click the matching button
                    button.click()
                    print("Selected Profession as: ", profession.upper())

                    return True  # Return True if a match is found and clicked

            return False  # Return False if no match is found

        except:
            print(f"Error clicking profession button")
            open(r"errors_logs.txt", "a").write("Error clicking profession button")
            return False  # Return False on error

    # ----------------------------------Members count---------------------------
    def get_associated_members_count(self):
        try:
            members_header = WebDriverWait(self.driver, 40).until(
                EC.presence_of_element_located(
                    (
                        By.CSS_SELECTOR,
                        "div.org-people__header-spacing-carousel h2",
                    )
                )
            )

            # Extract and return the text (associated members count)
            associated_members_count = members_header.text

            self.associated_members= int(associated_members_count.split()[0].replace(",", ""))
            return self.associated_members
        
        except Exception as e:
            print(f"Error on get_associated_members_count")
            open(r"errors_logs.txt", "a").write(
                "Error on get_associated_members_count"
            )
            return None

    # -----------------------------------------Select profile----------------------
    def extract_profiles_and_button_status(
        self,
        company_name,
        dept,
        max_profiles=5,
        message=False,
        message_note=None,
        total_members=100,
    ):
        names = []
        followers_ = []
        connects_ = []
        premiums = []
        rec_activities = []
        connect_btn = []
        message_btn = []
        locations = []
        msgs_sent = []
        profile_pics = []

        connect_or_message_count = 0
        no_connect_or_message_count = 0
        links = []
        scroll_count = 0

        db_data=[k['Profile_URL']  for k in self.o.select_all()]

        element=WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located(
                    (
                        By.CSS_SELECTOR,
                        "li.org-people-profile-card__profile-card-spacing",
                    )
                )
            )

        ActionChains(self.driver).move_to_element(element).perform()

        while connect_or_message_count <= max_profiles:

            try:
                
                WebDriverWait(self.driver, 20).until(
                    EC.presence_of_element_located(
                        (
                            By.CSS_SELECTOR,
                            "li.org-people-profile-card__profile-card-spacing",
                        )
                    )
                )
                
                profile_cards = self.driver.find_elements(
                    By.CSS_SELECTOR, "li.org-people-profile-card__profile-card-spacing"
                )

                for card in profile_cards:
                    profile_url = None
                    if scroll_count % 9 == 0:
                        r_scroll = 180 + random.randint(self.min_sleep, self.max_sleep)
                        self.driver.execute_script(f"window.scrollBy(0, {r_scroll});")
                        time.sleep(0.75)


                    WebDriverWait(self.driver, 30).until(
                    EC.presence_of_element_located(
                        (By.CSS_SELECTOR, ".artdeco-entity-lockup__title .ember-view")
                    )
                    )

                    # Extract profile name
                    profile_name = card.find_element(
                        By.CSS_SELECTOR, ".artdeco-entity-lockup__title .ember-view"
                    ).text.strip()


                    if profile_name and profile_name == "LinkedIn Member":
                        no_connect_or_message_count += 1
                        continue
                    
                    else:
                        profile_url_element = card.find_element(By.CSS_SELECTOR, "a.link-without-visited-state")
                        profile_url = profile_url_element.get_attribute("href")
                        profile_url = profile_url.split("?")[0]

                  
                        if profile_url and (profile_url not in links and profile_url not in db_data):
                            print(f"Profile Name: {profile_name}, Profile URL: {profile_url}")
                            obj = get_profile_detail(self.driver,profile_url)

                            links.append(profile_url)

                            name=obj.get_profile_name()
                            names.append(name)
                            print('Profile name: ',name)

                            profile_pics.append(obj.get_profile_pic())

                            location = obj.get_location()
                            locations.append(location)
                            print('Location: ',location)

                            followers_count, connections_count = (
                                obj.get_followers_and_connections()
                            )

                            followers_.append(followers_count)
                            connects_.append(connections_count)

                            premium=obj.check_premium_membership()
                            premiums.append(premium)

                            c_btn, m_btn, msg_sent = obj.list_all_buttons(
                                message, message_note
                            )

                            msgs_sent.append(msg_sent)
                            connect_btn.append(c_btn)
                            message_btn.append(m_btn)

                            if msg_sent==True:
                                self.o.update_message_status(profile_url)  

                            print('Buttons list: ',c_btn, m_btn, msg_sent)

                            act = obj.get_user_activities()
                            rec_activities.append(act)

                            print('Recent activity: ',act)

                            connect_or_message_count += 1

                            print(f'Got open profiles: {connect_or_message_count} of {max_profiles}')

                        # Check
                        if (
                            connect_or_message_count >= max_profiles
                            or connect_or_message_count + no_connect_or_message_count
                            >= total_members
                        ):
                            break


                    scroll_count = no_connect_or_message_count + connect_or_message_count

                if (
                    connect_or_message_count >= max_profiles
                    or connect_or_message_count + no_connect_or_message_count
                    >= total_members
                ):
                    print(f'Checked {total_members} of total {self.associated_members} associated members')
                    break
            
            except Exception as e:
                continue
            
        ## ------------------------------------------- Saving data user_profile-------------------

        date, time_ = get_datetime().split()

        ## ------------------ Saving data company_profile----------------------------

        user_data = pd.DataFrame(
            {
                "Date": [date+' '+time_ for _ in range(len(names))],
                "Name": names,
                "Profile_Pic_URL": profile_pics,
                "Location": locations,
                "Has_Premium": premiums,
                "Company":[company_name for _ in range(len(names))],
                "Department": [dept for _ in range(len(names))],
                "Connect_Available": connect_btn,
                "Free_Message": message_btn,
                "Message_Sent": msgs_sent,
                "Profile_URL": links,
                "Recent_Activity": rec_activities,
                "Followers": followers_,
                "Connections": connects_,
            }
        )

        self.o.insert_data_db(user_data)

        et = time.time()

        logs(self.st, et, date, time_, company_name, max_profiles, run=True)