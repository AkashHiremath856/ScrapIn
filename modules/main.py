from modules.user_selection import get_profile
import time

import undetected_chromedriver as uc
import json
# from profile_detail import get_profile_detail
from selenium_stealth import stealth
import undetected_chromedriver as uc
import json


# ---------------------------------------Get Data--------------------------------------------
def get_data(
    driver,
    company,
    dept,
    region,
    max_profiles,
    message,
    message_note,
    user_id,
):
    st = time.time()
    company_name = company.split("/")[company.split("/").index("company") + 1].upper()
    obj = get_profile(
        driver,
        st,
        company + "/people/",
        user_id
    )
    obj.show_more()
    obj.check_title_and_click_next("Where they studied")
    obj.click_profession_button(dept)
    total_members = obj.get_associated_members_count()

    # Get User Details
    obj.extract_profiles_and_button_status(
        company_name,
        dept,
        region,
        max_profiles,
        message,
        message_note,
        total_members,
    )
        
# ------------------------------To run tests--------------------------

if __name__ == "__main__":

    options = uc.ChromeOptions()
    options.headless = False
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')

    driver = uc.Chrome(options=options)

    stealth(
    driver,
    languages=["en-US", "en"],
    vendor="Google Inc.",
    platform="Win32",
    webgl_vendor="Intel Inc.",
    renderer="Intel Iris OpenGL Engine",
    fix_hairline=True,
    )

    print('Started chrome')
    
    with open(f'chrome_data/user_2p7sSefBqYSAVSAfeAZuqpSpSV4', 'r') as file:
        cookies_data = json.load(file)

    driver.get('https://www.linkedin.com/')

    if cookies_data:
            for cookie in cookies_data:
                if cookie['domain'].startswith("."):
                    cookie['domain'] = cookie['domain'][1:]
                if cookie['domain'] == "linkedin.com":
                    cookie['domain'] = "www.linkedin.com"

                if "www.linkedin.com" in cookie['domain']:
                    cookie.pop('secure', None)
                    cookie.pop('httpOnly', None)
                    cookie.pop('expiration', None)

                    try:
                        driver.add_cookie(cookie)
                    except Exception as e:
                        print(f"Failed to add cookie")


    # ----------------------------Get User profiles---------------------

    url = "https://www.linkedin.com/company/randstad"
    dept = "Human Resources"
    region = "United states"
    max_profile = 2
    message = False
    message_note = ""

    get_data(
        None,
        url,
        dept,
        region,
        max_profile,
        message,
        message_note,
        user_id='user_2p7sSefBqYSAVSAfeAZuqpSpSV4'
    )


    # -----------------------User selection-------------------------

    # obj = get_profile_detail(driver,
    #     "https://www.linkedin.com/in/pratibha-ranjan-5a9392172/"
    # )
    # print(obj.list_all_buttons())
