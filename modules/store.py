import datetime
import libsql_experimental as libsql
import pandas as pd
import os
from collections import Counter
from webdriver_manager.chrome import ChromeDriverManager


def get_datetime():
    date = datetime.datetime.now().strftime("%Y-%m-%d")
    time = datetime.datetime.now().strftime("%H:%M:%S")
    return date+' '+time

# ---------------------------------Logs--------------------------------------------
def logs(s, e, date, time_, company_name, max_profiles, run=False):

    if run:
        # logs
        minutes, seconds = divmod(e - s, 60)
        log = f"{date} {time_} Time taken to get {max_profiles} User's Profile Details from {company_name} is : {minutes} minutes {round(seconds,3)} seconds\n"
        print(log)
        open(".logs/logs.txt", "a").write(log)


#----------------------------------------------Create and Insert into DB---------------------------------------

class db_interactions:
    def __init__(self,db_name):
        self.db_dir = './archives'
        self.db_file = f'{db_name}.db'

        if not os.path.exists(self.db_dir):
            os.makedirs(self.db_dir)

        self.conn = libsql.connect(os.path.join(self.db_dir, self.db_file))
        self.cursor = self.conn.cursor()

        # Create the table for user profiles if it doesn't already exist
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS users_profile (
                Date TEXT,
                Name TEXT,
                Profile_Pic_URL TEXT,
                Location TEXT,
                Has_Premium TEXT,
                Connect_Available TEXT,
                Free_Message TEXT,
                Message_Sent TEXT,
                Profile_URL TEXT PRIMARY KEY,
                Recent_Activity TEXT,
                Followers INTEGER,
                Connections INTEGER,
                Company TEXT,
                Department TEXT
            )
        ''')


    #------------------------------Insert data---------------------------------

    def insert_data_db(self,df=None):                

        if isinstance(df,pd.DataFrame):
            # Insert rows into the database
            for _, row in df.iterrows():
                try:
                    self.cursor.execute('''
                        INSERT OR REPLACE INTO users_profile (
                            Date, Name, Profile_Pic_URL, Location, Has_Premium, 
                            Connect_Available, Free_Message, Message_Sent, Profile_URL, 
                            Recent_Activity, Followers, Connections, Company, Department
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        row['Date'], row['Name'], row['Profile_Pic_URL'], row['Location'], str(row['Has_Premium']),
                        str(row['Connect_Available']), str(row['Free_Message']), str(row['Message_Sent']),
                        row['Profile_URL'],row['Recent_Activity'], row['Followers'], row['Connections'], row['Company'], row['Department']
                    ))
                except:
                    # Skip if Profile_URL already exists (Primary Key constraint)
                    print(f"Skipping {row['Profile_URL']} as it already exists in the database.")

            # Commit the transaction for this sheet
            self.conn.commit()

            print("Data inserted successfully in SQLite database.")

        return True


    #--------------------------------Update db--------------------------------

    def update_message_status(self,profile_url):
        try:

            # Get today's date in the required format
            today_date = datetime.datetime.now().strftime('%Y-%m-%d')

            # SQL query to update Date and Message_Sent for a given Profile_URL
            sql_query = '''
                UPDATE users_profile
                SET Date = ?, Message_Sent = ?
                WHERE Profile_URL = ?
            '''
            self.cursor.execute(sql_query, (today_date, 'True', profile_url))
                
            # Commit changes
            self.conn.commit()


        except Exception as e:
            print(f"An error occurred: {e}")

    #-----------------------------------Get all data from db--------------------------
    def select_all(self):
        
        self.cursor.execute("SELECT * FROM users_profile")
        rows = self.cursor.fetchall()

        # Step 4: Prepare the data for output
        columns = ['Date', 'Name', 'Profile_Pic_URL', 'Location', 'Has_Premium', 
                'Connect_Available', 'Free_Message', 'Message_Sent', 'Profile_URL', 
                'Recent_Activity', 'Followers', 'Connections', 'Company', 'Department']
        data = pd.DataFrame(rows, columns=columns)


        return data.to_dict(orient='records')
    
    #----------------------------------------------------Send connection--------------------------------

    def send_connect(self,sent_diff=3):

        # Create the table for user profiles if it doesn't already exist
        self.cursor.execute(''' select * from users_profile ''')

        date_now = datetime.datetime.strptime(datetime.datetime.now().strftime("%Y-%m-%d"), "%Y-%m-%d").date()

        to_connect=[]

        for row in self.cursor.fetchall():
            url=row[8]

            date=pd.to_datetime(row[0].split()[0],format='%Y-%m-%d').date()

            date_diff = (date_now - date).days

            if row[5]=='True' and date_diff >= sent_diff and row[7]=='True':
                to_connect.append(url)
                sql_query = '''
                    UPDATE users_profile
                    SET Date = ?, Connect_Available = ?
                    WHERE Profile_URL = ?
                '''
                self.cursor.execute(sql_query, (str(date_now), 'Invite Sent', url))

                self.conn.commit()
                    
        return to_connect

#----------------------------------------------------Insert users--------------------------------

def insert_users(user_data):
    conn = libsql.connect(os.path.join('archives', 'users_db.db'))
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users_db (
            user_id TEXT PRIMARY KEY,
            org TEXT,
            admin TEXT,
            name TEXT
            )
            ''')
            
    cursor.execute('''INSERT OR REPLACE INTO users_db 
                (user_id, org, admin,name) VALUES (?, ?, ?, ?)
                ''', (user_data['id'], user_data['org'], user_data['admin'],user_data['first_name']))


    conn.commit()

#------------------------Admin data--------------------------------------

def get_admin_data(user_id):
    conn = libsql.connect(os.path.join('archives', 'users_db.db'))
    cursor = conn.cursor()
    admin_org=None

    cursor.execute(f'select * from users_db')

    users_db=[row for row in cursor.fetchall()]

    name={}

    # Get org
    for user in users_db:
        name[user[0]]=user[3]
        if user[0]==user_id and user[2]=='true':
            admin_org=user[1]


    # Get db of user 
    org_mem=[]
    for user in users_db:
        if user[1]==admin_org:
            org_mem.append(user[0])



    # Loops through profiles
    datas={}

    for mem in org_mem:
        conn = libsql.connect(os.path.join('archives', f'{mem}.db'))
        cursor = conn.cursor()

        cursor.execute(f'select * from users_profile')

        data=[row for row in cursor.fetchall()]

        if data!=[]:
            datas[mem]=data


    counts=0
    company_count=[]
    region_count=[]

    for member,data in datas.items():
        for d in data:
            region_count.append(d[3])
            company_count.append(d[-2])
            counts+=1


    return datas,len(datas),counts,name,Counter(region_count).items(),Counter(company_count).items()


#-------------------------Download driver------------------

def get_driver_path():

    directory = os.path.expanduser('~/.wdm/drivers/chromedriver/linux64/131.0.6778.85/chromedriver-linux64/')
    if os.path.isdir(directory):
        return directory+'/chromedriver'

    else:
        manager=manager=ChromeDriverManager(driver_version=os.popen('google-chrome --version').read().split()[2])
        chrome_driver_path=manager.install()
        return chrome_driver_path