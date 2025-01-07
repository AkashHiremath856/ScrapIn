from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time


class get_profile_detail:

    def __init__(self, driver, profile):

        self.driver_ = driver

        self.driver_.get(profile)

        WebDriverWait(self.driver_, 45).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.pv-profile-body-wrapper"))
            )
        
        time.sleep(5)
        
        soup = BeautifulSoup(self.driver_.page_source, 'html.parser')
        buttons = soup.find_all('button')
        for button in buttons:
            button_text = button.find('span', class_='artdeco-button__text')
            if button_text and 'Close your conversation' in button_text.get_text():
                print('Found a conversation open')
                self.driver_.execute_script(f"document.getElementById('{button.get('id')}').click();")
                self.driver_.get(profile)

    # ---------------------------Profile name-----------------
    def get_profile_name(self):
        name_ = None
        try:
            div_selector = "div.pv-top-card__non-self-photo-wrapper"
            image_element = self.driver_.find_element(
                By.CSS_SELECTOR, f"{div_selector} img"
            )

            image_title = image_element.get_attribute("title")
            if image_title != None:
                name_ = image_title
                return name_
        except:
            pass

        try:
            name_from_url = self.driver_.current_url.split("/in/")[1].split("-")[:-1]
            name = " ".join(name_from_url).title()
            if name == None or name == "":
                name = self.driver_.current_url.split("/")[-2]
            return name

        except Exception as e:
            print("Could not retrieve the name")
            open(r"errors_logs.txt", "a").write("Could not retrieve the name")

    # ------------------------------------ Check premium-------------------
    def check_premium_membership(self):
        # Get the page source and parse it with BeautifulSoup
        page_source = self.driver_.page_source
        soup = BeautifulSoup(page_source, "html.parser")

        # Search for the premium badge using the class name and visually hidden text
        premium_badge = soup.find("span", class_="pv-member-badge--for-top-card")

        # Check for the visually hidden text that confirms premium membership
        if premium_badge:
            premium_text = premium_badge.find("span", class_="visually-hidden")
            if premium_text and "premium account" in premium_text.text.lower():
                return True

        return False

    # -----------------------------------------------Get location-----------------------------

    def get_location(self):
        location_text = ""

        try:
            # Wait for the span element to be present
            WebDriverWait(self.driver_, 30).until(
                EC.presence_of_element_located(
                    (
                        By.CSS_SELECTOR,
                        "span.text-body-small.inline.t-black--light.break-words",
                    )
                )
            )

            # Locate the span element
            location_element = self.driver_.find_element(
                By.CSS_SELECTOR,
                "span.text-body-small.inline.t-black--light.break-words",
            )

            # Get the text inside the span
            location_text = location_element.text.strip()

        except Exception as e:
            print("Error occurred while getting location text:", e)

        return location_text

    # ---------------------------------------- Get recent activity in days----------------------
    def get_recent_activity(self, time_str):
        time_str=time_str.replace('d',' d').replace('w',' w').replace('mo',' mo').replace('y',' y').split()
        number = int(time_str[0]) 
        unit = time_str[1]         

        if unit == "d":
            return number
        elif unit == "mo":
            total_days = number * 30
            return total_days
        elif unit == "w":
            total_days = number * 7
            return total_days
        elif unit == "y":
            total_days = number * 365
            return total_days


    # -------------------------------click_comments_and_get_activity---------------------------------
    def get_user_activities(self):         
        activity_text = "An Year Ago"
        recent_comments = "An Year Ago"

        try:

            div_element = WebDriverWait(self.driver_, 10).until(EC.visibility_of_element_located((By.CSS_SELECTOR, 'div.pvs-header__top-container--no-stack')))

            self.driver_.execute_script("arguments[0].scrollIntoView(true);", div_element)

            WebDriverWait(self.driver_, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".scaffold-finite-scroll__content")))

            soup = BeautifulSoup(self.driver_.page_source, 'html.parser')

            activity_link = soup.find('a', class_='app-aware-link feed-mini-update-optional-navigation-context-wrapper')

            if activity_link:
                activity_text = activity_link.get("aria-label")

                if activity_text:
                    activity_text = activity_text.split(" • ")[-1]
            
            soup = BeautifulSoup(self.driver_.page_source, 'html.parser')
            button_to_click = soup.find('button', id='content-collection-pill-1')

            if button_to_click:
                WebDriverWait(self.driver_, 10).until(EC.element_to_be_clickable((By.ID, 'content-collection-pill-1')))
                self.driver_.execute_script("document.getElementById('content-collection-pill-1').click()")

                new_comments_div = WebDriverWait(self.driver_, 5).until(
                    EC.presence_of_element_located(
                        (
                            By.CSS_SELECTOR,
                            "div.pt1.ph4.t-12.t-black--light span.feed-mini-update-contextual-description__text",
                        )
                    )
                )

                span = new_comments_div.find_element(
                    By.CSS_SELECTOR, "span[aria-hidden='true']"
                )

                if span:
                    recent_comments = span.text.split(" • ")[-1 ]

            if 'h' in activity_text:
                self.driver_.back()
                return f"{activity_text.replace('h',' Hours Ago')}"
            if 'h' in recent_comments:
                self.driver_.back()
                return f"{recent_comments.replace('h',' Hours Ago')}"
            if activity_text!="An Year Ago" and recent_comments!="An Year Ago":
                self.driver_.back()
                return f'{min(self.get_recent_activity(activity_text),self.get_recent_activity(recent_comments))} days ago'
            if activity_text!="An Year Ago" and recent_comments=="An Year Ago":
                self.driver_.back()
                return f'{activity_text} days ago'
            if activity_text=="An Year Ago" and recent_comments!="An Year Ago":
                self.driver_.back()
                return f'{recent_comments} days ago'
            else:
                self.driver_.back()
                return "An Year Ago"
        
        except:
            self.driver_.back()
            return "An Year Ago"

    # --------------------------------Add Connection-----------------------
    def sent_invite(self, connect_note=None):
        if connect_note is None:

            try:
                # Wait for the modal to be present
                WebDriverWait(self.driver_, 15).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'div.artdeco-modal.send-invite'))
                )

                send_button = WebDriverWait(self.driver_, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'button[aria-label="Send invitation"]'))
                )


                if send_button:
                    send_button.click()
                    print("Invitation sent without a note successfully.")
                else:
                    print("Button not found")
            
            except:
                print('Failed to send invite')

    # ---------------------------Send message----------------------------
    def sent_message(self, message_note='Hello',subject=None):
        try:
            # Wait for the subject input field to be present
            subject_input = WebDriverWait(self.driver_, 20).until(
                EC.presence_of_element_located(
                    (By.XPATH, "//input[@placeholder='Subject (optional)']")
                )
            )

            # Fill the subject
            if subject:
                subject_input.send_keys(subject)
            else:
                uname=self.get_profile_name().split()
                subject_input.send_keys(f"Hi, {' '.join(uname[:2]) if len(uname)>1 else ' '.join(uname)}!")

            message_box = WebDriverWait(self.driver_, 20).until(
                EC.presence_of_element_located(
                    (
                        By.XPATH,
                        "//div[@contenteditable='true' and @aria-label='Write a message…']",
                    )
                )
            )

            # Fill the message
            message_box.send_keys(message_note)

            # Wait for the send button to be clickable
            send_button = WebDriverWait(self.driver_, 20).until(
                EC.element_to_be_clickable(
                    (
                        By.XPATH,
                        "//button[contains(@class, 'msg-form__send-btn') and contains(@class, 'artdeco-button')]",
                    )
                )
            )

            send_button.click()

            print("Message sent successfully.")

            return True

        except:
            print("Failed to send message")
            open(r"errors_logs.txt", "a").write("Failed to send message")
            return True

    # ----------------------Check message button------------------------
    def list_all_buttons(self, message=False, message_note=None,connection=False,subject=None):
        buttons_list = []
        msg_sent = False
        name_=None

        try:
            WebDriverWait(self.driver_, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.pv-top-card__non-self-photo-wrapper"))
            )
            div_selector = "div.pv-top-card__non-self-photo-wrapper"
            image_element = self.driver_.find_element(
                By.CSS_SELECTOR, f"{div_selector} img"
            )

            image_title = image_element.get_attribute("title")
            if image_title != None:
                name_ = image_title
                name_=name_.split(',')[0] if ',' in name_ else name_
            
        except:
            print('No name found in list btns')

    
        #-----------------------------Connect btn---------------------------
        
        soup = BeautifulSoup(self.driver_.page_source, 'html.parser')

        if name_ and soup.find("button", {"aria-label": f"Invite {name_} to connect"}):
            connect_button = soup.find("button", {"aria-label": f"Invite {name_} to connect"})

            if connect_button:
                    btn_id=connect_button.get("id")
                    prev_url=self.driver_.current_url
                    self.driver_.execute_script(f"document.getElementById('{btn_id}').click();")
                    if prev_url==self.driver_.current_url:
                        buttons_list.append("connect")
                        if connection:
                            self.sent_invite()
                            print('Connect invite sent')
                        else:
                            soup = BeautifulSoup(self.driver_.page_source, 'html.parser')
                            dismiss_button = soup.find('button', {'aria-label': 'Dismiss'})
                            if dismiss_button:
                                button_id = dismiss_button.get('id')
                                self.driver_.execute_script(f"document.getElementById('{button_id}').click();")
                    else:
                        self.driver_.back()  


        #---------------------Already invited---------------------
        elif name_ and soup.find("button", {"aria-label": f"Pending, click to withdraw invitation sent to {name_}"}):
            buttons_list.append('Invited')    

        #------------------------------more btn--------------------------
        else:
                soup = BeautifulSoup(self.driver_.page_source, "html.parser")
                more_button = soup.find(
                    "button", attrs={"aria-label":'More actions'}
                )
                if more_button:
                    button_id = more_button.get('id')  
                    self.driver_.execute_script(f"document.getElementById('{button_id}').click();")

                #------------------------------After more--------------------------
                    soup = BeautifulSoup(self.driver_.page_source, "html.parser")
                    time.sleep(2)
                    connect_button = soup.find_all(
                        "div", attrs={"aria-label": lambda x: x and f'Invite {name_}' in x})
                    
                    if connect_button!=[]:
                        connect_button=connect_button[0]

                        if connect_button:
                            button_id = connect_button.get('id')
                            self.driver_.execute_script(f"document.getElementById('{button_id}').click();")
                            prev_url=self.driver_.current_url
                            if prev_url==self.driver_.current_url:
                                buttons_list.append("connect")
                                if connection:
                                    self.sent_invite()
                                    print('Connect invite sent')
                                else:
                                    soup = BeautifulSoup(self.driver_.page_source, 'html.parser')
                                    dismiss_button = soup.find('button', {'aria-label': 'Dismiss'})
                                    if dismiss_button:
                                        button_id = dismiss_button.get('id')
                                        self.driver_.execute_script(f"document.getElementById('{button_id}').click();")
                            else:
                                self.driver_.back()          
                else:
                        print('No more btn found')


        # ------------------------------Free message---------------------------------
        WebDriverWait(self.driver_, 10).until(
            EC.presence_of_element_located(
                (By.XPATH, "//button[contains(@aria-label, 'Message')]")
            )
        )
        soup = BeautifulSoup(self.driver_.page_source, "html.parser")

        message_button = soup.find(
            "button", attrs={"aria-label": lambda x: x and "Message" in x}
        )

        if message_button and connection==False:
                aria_label=message_button.get("aria-label")
                button=self.driver_.find_element(By.XPATH, f'//button[@aria-label="{aria_label}"]')
                self.driver_.execute_script("""
                    var element = arguments[0];
                    var mouseEvent = document.createEvent('MouseEvents');
                    mouseEvent.initMouseEvent('mousedown', true, true, window, 0, 0, 0, 0, 0, false, false, false, false, 0, null);
                    element.dispatchEvent(mouseEvent);

                    mouseEvent.initMouseEvent('mouseup', true, true, window, 0, 0, 0, 0, 0, false, false, false, false, 0, null);
                    element.dispatchEvent(mouseEvent);

                    mouseEvent.initMouseEvent('click', true, true, window, 0, 0, 0, 0, 0, false, false, false, false, 0, null);
                    element.dispatchEvent(mouseEvent);
                """, button)

                time.sleep(3)
                soup = BeautifulSoup(self.driver_.page_source, 'html.parser')
                free_message_section = soup.find("section", class_="msg-inmail-credits-display")
                if free_message_section:
                    paragraph = free_message_section.find("p")
                    if paragraph and "Free message" in paragraph.get_text():
                        buttons_list.append('message')
                        if message and message_note:
                            msg_sent=self.sent_message(message_note,subject)
                        else:
                            self.driver_.find_element(By.XPATH, "//button[.//span[text()='Close your draft conversation']]").click()
                else:
                    soup = BeautifulSoup(self.driver_.page_source, 'html.parser')
                    buttons = soup.find_all('button')
                    for button in buttons:
                        button_text = button.find('span', class_='artdeco-button__text')
                        if button_text and 'Close your conversation' in button_text.get_text():
                            print('Found a conversation open')
                            self.driver_.execute_script(f"document.getElementById('{button.get('id')}').click();")
                            msg_sent=True
        

        has_connect = str(any("connect" in b.lower() for b in buttons_list))
        has_message = str(any("message" in b.lower() for b in buttons_list))
        has_invited='Invited' if any('invited' in b.lower() for b in buttons_list) else False
        msg_sent=str(msg_sent)

        if has_connect=='False':
            has_connect=has_invited if has_connect=='False' and has_invited=='Invited' else 'False'

        return has_connect, has_message, msg_sent

    # ----------------------------------------Get profile pic------------------------------------
    def get_profile_pic(self):
        try:
            WebDriverWait(self.driver_, 10).until(EC.visibility_of_element_located((By.CSS_SELECTOR, "div.pv-top-card__non-self-photo-wrapper")))
            div_selector = "div.pv-top-card__non-self-photo-wrapper"
            image_element = self.driver_.find_element(
                By.CSS_SELECTOR, f"{div_selector} img"
            )

            # Extract the 'src' attribute of the image
            image_src = image_element.get_attribute("src")

            return image_src
        except:
            print("Error occured while retriving profile pic")
            open(r"errors_logs.txt", "a").write(
                "Error occured while retriving profile pic"
            )
            return None

    # ---------------------Get followers and connections---------------------------

    def get_followers_and_connections(self):
        followers_count = "0 followers"
        connections_count = "0 connections"

        try:
            # Wait for the main container or any identifiable parent to load fully
            WebDriverWait(self.driver_, 60).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )

            # Use JavaScript to find text for followers and connections
            followers_script = """
            let elements = document.querySelectorAll("li");
            for (let el of elements) {
                if (el.innerText.toLowerCase().includes("followers")) {
                    return el.innerText;
                }
            }
            return  "0 followers";
            """

            connections_script = """
            let elements = document.querySelectorAll("li");
            for (let el of elements) {
                if (el.innerText.toLowerCase().includes("connections")) {
                    return el.innerText;
                }
            }
            return "0 connections";
            """

            # Execute the JavaScript and get text content
            followers_text = self.driver_.execute_script(followers_script)
            connections_text = self.driver_.execute_script(connections_script)

            # Extract numbers from the text if found
            if followers_text:
                followers_count = (
                    f"{''.join(filter(str.isdigit, followers_text))} followers"
                )
                print(f"Followers found: {followers_count}")  # Debug log

            if connections_text:
                connections_count = (
                    f"{''.join(filter(str.isdigit, connections_text))} connections"
                )
                print(f"Connections found: {connections_count}")  # Debug log

            return '0 followers' if int(followers_count.split()[0])>=100000 else followers_count, connections_count

        except Exception as e:
            print("Error occurred while getting followers and connections:", e)
            with open(r"errors_logs.txt", "a") as log_file:
                log_file.write(
                    f"Error occurred while getting followers and connections: {e}\n"
                )
            return followers_count, connections_count
