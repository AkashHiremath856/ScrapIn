from quart import Quart, request, abort,render_template,jsonify,redirect,url_for,redirect, session,send_from_directory,Response
from quart_cors import cors
import pandas as pd
from modules.user_selection import get_profile
import os
import re
from selenium_stealth import stealth
import undetected_chromedriver as uc
from modules.profile_detail import get_profile_detail
from modules.store import db_interactions,insert_users,get_admin_data,get_driver_path
import json
from dotenv import load_dotenv
from clerk_backend_api import Clerk
import time
from datetime import timedelta
import secrets
from quart_session import Session
import redis.asyncio as redis
from collections import defaultdict
import asyncio

app = Quart(__name__)
app = cors(app)
load_dotenv()

os.makedirs('.logs',exist_ok=True)
os.makedirs('archives',exist_ok=True)

user_data=None

#--------------------Session------------------------

app.secret_key = secrets.token_hex(16)  
app.config['SESSION_TYPE'] = 'redis'  
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)
app.config['SESSION_REDIS'] = redis.from_url("redis://localhost:6379")

# Initialize session
Session(app)
#----------------------------Clerk----------------------
clerk = Clerk(bearer_auth=os.environ['clerk_api'])

# Authentication function (async)
async def authenticate_user(email, password):
    try:
        user_res = await clerk.users.list_async(email_address=[email])

        if user_res and len(user_res) > 0:
            global user_data

            user = user_res[0]
            user_id = user.id

            verify_res = await clerk.users.verify_password_async(user_id=user_id, password=password)

            if verify_res and verify_res.verified:
                org_res = [org['organization'] for org in clerk.organization_memberships.get_all().model_dump()['data'] if org['public_user_data']['user_id']==user_id]
                org_res=org_res[0]
                res = clerk.organization_memberships.list(organization_id=org_res['id']).model_dump()['data']
                org_name=res[0]['organization']['name']
                res=[r['role_name'] for r in res if r['public_user_data']['user_id']==user_id]
                res=res[0]
                

                user_data = {
                    "id": user_id,
                    "email": user.email_addresses[0].email_address,
                    "first_name": user.first_name or "N/A",
                    "email_verified": user.email_addresses[0].verification.status == "verified",
                    'org': org_res['id'],
                    'admin': 'true' if res == 'Admin' else 'false',
                    'org_name':org_name
                }
                return {"authenticated": True, "user": user_data}
            else:
                return {"authenticated": False, "message": "Invalid password"}
        else:
            return {"authenticated": False, "message": "User not found"}

    except Exception as e:
        return {"authenticated": False, "error": e}


#----------------------------- Login--------------------------------
@app.route('/login', methods=['GET', 'POST'])
async def login():
    if request.method == 'POST':
        email = (await request.form)['email']
        password = (await request.form)['password']

        try:
            result = await authenticate_user(email, password)
        except RuntimeError as e:
            print(f"Runtime error during authentication: {str(e)}")

        if result.get("authenticated"):
            session['user'] = user_data 
            return redirect(url_for('index'))
        else:
            try:
                error_body = str(json.loads(result['error'].body)['errors'][0]['code']).replace('_',' ')
            except:
                error_body=result['message']
            return jsonify({'message': error_body}), 401
        
    return await render_template('logout.html')

#---------------------------Get cookies------------------
@app.route('/cookies', methods=['POST'])
async def cookies():
    cookies_data = await request.get_json()

    if cookies_data:
        session['cookies']=cookies_data
        return jsonify({"message": "Cookies saved successful"}), 200

    return jsonify({"message": "Internal server error saving cookies"}), 500

#-------------------------------Logout----------------------------
@app.route('/logout')
async def logout():
    session.pop('user', None)
    session.clear()
    return redirect(url_for('index'))

#------------------------------Admin------------------
@app.route('/admin',methods=['GET'])
async def admin():
    global data
    global name

    if 'user' not in session:
        return redirect(url_for('login'))
    
    user = session.get('user')
    data,members,data_count,name,region_count,company_count=get_admin_data(user['id'])
    return await render_template('admin.html',user_data={'data':data,'members':members,'data_count':data_count,'name':name,'user_data':user,'region_count':region_count,'company_count':company_count},show_nav_tabs=False)

#---------------------------Download admin csv-----------
@app.route('/download/<filename>')
async def download_file(filename,download=True):
    if 'user' not in session:
        return redirect(url_for('login'))
    
    columns = [
    "Date", "Name", "Profile_Pic_URL", "Location", "Has_Premium", "Connect_Available", "Free_Message", "Message_Sent", 
    "Profile_URL", "Recent Activity", "Followers", "Connections", "Company", "Department"
    ]

    if 'download_'in filename:
        data,members,data_count,name,region_count,company_count=get_admin_data(session.get('user')['id'])
        filename=filename.replace('download_','')
        for member in data:
            if member==filename:
                filename=name[member]+'_'+member
                pd.DataFrame(data[member],columns=columns).to_csv(f'archives/{filename}.csv',index=False)

        
        filename=filename+'.csv'
        file_path = os.path.join('archives', filename)
        if os.path.exists(file_path):
            if download:
                return await send_from_directory('archives', filename, as_attachment=True)
            else:
                return jsonify({"message": "Only saved file!"}), 404
        return jsonify({"error": "File not found"}), 404

    else:
        o = db_interactions(session.get('user')['id'])
        data = o.select_all()
        filename=session.get('user')["first_name"]+'_'+session.get('user')['id']
        pd.DataFrame(data,columns=columns).to_csv(f'archives/{filename}.csv',index=False)
        filename=filename+'.csv'
        file_path = os.path.join('archives', filename)
        if os.path.exists(file_path):
            return await send_from_directory('archives', filename, as_attachment=True)
        return redirect(url_for('index'))
    
#----------------------------Transfer-------------------------
@app.route('/transfer/<filename>')
async def transfer_file(filename):
    if 'user' not in session:
        return redirect(url_for('login'))

    columns = [
    "Date", "Name", "Profile_Pic_URL", "Location", "Has_Premium", "Connect_Available", "Free_Message", "Message_Sent", 
    "Profile_URL", "Recent_Activity", "Followers", "Connections", "Company", "Department"
    ]

    filename=filename.replace('transfer_','')
    data,members,data_count,name,region_count,company_count=get_admin_data(session.get('user')['id'])
    for member in data:
        if member==filename:
            filename=name[member]+'_'+member
            pd.DataFrame(data[member],columns=columns).to_csv(f'archives/{filename}.csv',index=False)

    filename=filename+'.csv'
    file_path = os.path.join('archives', filename)
    if os.path.exists(file_path):
        o = db_interactions(session.get('user')['id'])
        o.insert_data_db(df=pd.read_csv(file_path))
        return jsonify({"message": "Data Transferred successfully"}), 200
    return redirect(url_for('admin'))


#-----------------------------Get selenium driver-------------------------------------
def get_driver():
    options = uc.ChromeOptions()
    options.headless = True
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')

    driver = uc.Chrome(options=options,driver_executable_path=get_driver_path())

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
    
    if session['cookies']:

        driver.get('https://www.linkedin.com/')

        for cookie in session['cookies']:
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
        
        driver.get('https://www.linkedin.com/feed/')
        while driver.execute_script('return document.readyState') != 'complete':
            time.sleep(0.5)

        if driver.current_url!='https://www.linkedin.com/feed/':
            print(f"Failed to find cookie, Please login")
            return None
    else:
        print(f"Failed to get cookies file")
        return None
                    
    print('Logged in sucessfully')
    return driver

#---------------------------------Root----------------------------------(Auto invite set to 100 days )
@app.route('/')
async def index():
    unique_values=None
    if 'user' not in session:
        return redirect(url_for('login'))
    
    else:
        user=session.get('user')
        if user:
            insert_users(user)

        o = db_interactions(session.get('user')['id'])

        if o.insert_data_db():
            data = o.select_all()
            unique_values = defaultdict(list)
            for user_item in data:
                for filter_key, filter_label in {
                    'Name': 'name-filter',
                    'Location': 'location-filter',
                    'Date': 'date-filter',
                    'Company': 'company-filter',
                    'Department': 'department-filter',
                    'Has_Premium': 'premium-filter',
                    'Connect_Available': 'connect-filter',
                    'Free_Message': 'freeMessage-filter',
                    'Message_Sent': 'messageSent-filter',
                    'Recent_Activity': 'recentActivity-filter'
                }.items():
                    if user_item[filter_key] not in unique_values[filter_label]:
                        unique_values[filter_label].append(user_item[filter_key])
        else:
            data = None

        connects_list = o.send_connect(sent_diff=100)
        if connects_list != []:
            driver = get_driver()

            if driver:

                for url in connects_list:
                    profile = get_profile_detail(driver, url)
                    profile.list_all_buttons(connection=True)
                    print('Connect sent to ', url)

                driver.close()

            else:
                return abort(500,description="Failed to send invite")
        
        return await render_template('popup.html', user_data={'data': None if data==[] else data, 'user_data': user,'unique_values':unique_values}, show_nav_tabs=True)


#---------------------------------------------Progress text-----------------------------------
log_queue = asyncio.Queue()


@app.route("/stream-logs")
async def stream_logs():
    """Stream logs from the log queue."""
    async def log_stream():
        try:
            while True:
                log = await log_queue.get()
                if log == "done":
                    yield f"data: {log}\n\n"
                    break
                yield f"data: {log}\n\n"
        except asyncio.CancelledError:
            print("Log stream canceled.")
            return

    return Response(log_stream(), content_type="text/event-stream")

#-------------------------------------------------Send message-----------------------------------
@app.route('/send-message', methods=['POST'])
async def send_message():
    if 'user' not in session:
        return redirect(url_for('login'))

    form = await request.json
    subject=form.get('subject')
    message = form.get('message')
    profile_urls = form.get('profileUrls', [])

    if not message or not profile_urls:
        print('Message and profile URLs are required')
        return jsonify({'error': 'Message and profile URLs are required'}), 400
    
    driver = get_driver()

    if driver:
        await log_queue.put("Logged in sucessfully")
        await asyncio.sleep(1) 

        for url in profile_urls:
            await log_queue.put(f"Sending message to: {url}")
            await asyncio.sleep(1) 
            profile=get_profile_detail(driver,url)
            has_connect, has_message, msg_sent=profile.list_all_buttons(message=True,message_note=str(message),subject=subject)
            if msg_sent:
                print('Done sending message to ',url)
                o=db_interactions(session.get('user')['id'])
                o.update_message_status(url)

        driver.close()
    
    else:
        return abort(500,description="Please login to your linkedin")

    if msg_sent:
        return jsonify({'success': 'Message sent!'}),200
    else:
        return abort(500,description="Failed to send message")
    

#----------------------------------------------------Rename for excel-----------------------------------------------
def sanitize_sheet_name(name):
    if len(name) > 32:
        name = name[:31]
    return re.sub(r'[\\/*?:"<>|]', "_", name)

#----------------------------------------Main fun-----------------------------------------------------
@app.route("/upload-file", methods=["POST"])
async def upload_file():
    if 'user' not in session:
        return redirect(url_for('login'))
    
    await log_queue.put("Starting processing...")
    await asyncio.sleep(1) 
    
    try:
        driver = get_driver()
        if driver is None:
            await log_queue.put("done")
            await asyncio.sleep(1) 
            return jsonify({"message": "Please login to your LinkedIn"}), 500
        
        await log_queue.put("Starting fetching...")
        await asyncio.sleep(1)
                
        form = await request.form
        url = form.get('url')
        department = form.get("department")
        max_profiles = int(form.get("max_profiles"))
        message = form.get("message")
        message_note = form.get("message_note")
        location = form.get("location")
                
        message = False if message == "false" else True
        message_note = None if message_note == "" else message_note
        
        st = time.time()
        company_name = url.split("/")[url.split("/").index("company") + 1].upper()
        obj = get_profile(
            driver,
            st,
            url + "/people/",
            session.get('user')['id']
        )
        print(f"Redirecting to :{url}")
        await log_queue.put(f"Redirecting to :{url}")
        await asyncio.sleep(1)

        obj.show_more()
        obj.click_location(location)

        await log_queue.put(f"Selected Region: {location}")
        await asyncio.sleep(1)

        obj.check_title_and_click_next("Where they studied")
        obj.click_profession_button(department)

        await log_queue.put(f"Selected Department: {department}")
        await asyncio.sleep(1) 
        total_members = obj.get_associated_members_count()

        await log_queue.put(f"Getting Profiles")
        await asyncio.sleep(1) 
        obj.extract_profiles_and_button_status(
            company_name,
            department,
            max_profiles,
            message,
            message_note,
            total_members
        )

        driver.close()
        await log_queue.put("Scrapped data successfully")
        await asyncio.sleep(1)
        await log_queue.put("done")
        return jsonify({"message": "Scrapped data successfully"}), 200

    except Exception as e:
        err_msg = f"Error processing file: {e}"
        await log_queue.put('Error encountered contact dev')
        await asyncio.sleep(1) 
        await log_queue.put("done")
        open(r"errors_logs.txt", "a").write(err_msg)
        return jsonify({"message": "An error occurred. Please contact support."}), 500