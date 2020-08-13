#*******************************Imports*************************
import copy
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from werkzeug.security import generate_password_hash, check_password_hash
from flask import session

#*******************************Functions*************************
def equivalent_lists(lst1, lst2) :
    """Tells whether two lists are equivalent i.e they contain the same elements irrespective of the element positions"""

    if(len(lst1) != len(lst2)) :
        return False

    for e in lst1 :
        if(not e in lst2) :
            return False

    return True

def list_contains_list(minor_list, major_list) :
    """Tells whether all the elements of minor_list exist in major_list"""

    for element in minor_list :
        if(not element in major_list) :
            return False

    return True

#*******************************Class*************************
class LoginManager(object) :

    def __init__(self, user_database, table_name ,database_fields, primary_key , uniques, req_login_credentials, fields_to_encrypt=[]) :
        """user_database = path to the database containing user data
            database_fields = names of the fields in the database
            primary_key = the index of the field which acts as the primary key
            uniques = the indices credentials which have to be unique for each user
            req_login_credentials = from the database fields, the indices of the fields manadatory for logging in
            fields_to_encrypt = the indices of the fields to be saved in an encrypted form in the database. Primary key cannot be encrypted"""

        #Initializing
        self.database_name = user_database #The name of the database
        self.table_name = table_name #The name of the table in the database that contains the user login data
        self.primary_key = database_fields[primary_key] #The field in the table that acts as the primary key

        #Saving the credentials which have to be unique for each user
        self.unique_creds = [] #The credentials which have to be unique for each user
        for a in uniques :
            self.unique_creds.append(database_fields[a])

        #Setting up the login system
        self.user_attributes = copy.copy(database_fields) #The attributes that the user has i.e fields in the user database

        #Saving the mandatory login credentials
        self.req_login_credentials = [] #The credentials provided for verifing user and logging him/her in
        for cred in req_login_credentials :
            self.req_login_credentials.append(database_fields[cred])

        #Saving the fields which are to be stored in encrypted form
        self.fields_to_encrypt = [] #The fields to be saved in an encrypted form
        for a in fields_to_encrypt :
            if(database_fields[a] != self.primary_key) :
                self.fields_to_encrypt.append(database_fields[a])
            else :
                raise Exception("Primary Key Cannot be encrypted")


    def register_user(self, user_data) :
        """Adds the user to the database
        user_data = dictionary containing the data to be added to the database. Key = field name"""

        #Checking if all the table fields are present in the provided user data
        user_already_registered = self.user_already_registered(user_data)
        if( not user_already_registered and equivalent_lists(user_data.keys(), self.user_attributes)) :
            #Constructing the sql command
            sql_command = f"INSERT INTO {self.table_name}("

            table_fields = list(user_data.keys())
            for field_index in range(0, len(table_fields) - 1) :
                sql_command += f"{table_fields[field_index]}, "

            sql_command += f"{table_fields[-1]}) VALUES ("

            for data in range(0, len(user_data) - 1) :
                #Checking if the field needs to be encrypted before saving in database
                if(table_fields[data] in self.fields_to_encrypt) :
                    sql_command += f"'{generate_password_hash(user_data[table_fields[data]])}', "
                else :
                    sql_command += f"'{user_data[table_fields[data]]}', "

            #Checking if the field needs to be encrypted before saving in database
            if(table_fields[-1] in self.fields_to_encrypt) :
                sql_command += f"'{generate_password_hash(user_data[table_fields[-1]])}' )"
            else :
                sql_command += f"'{user_data[table_fields[-1]]}' )"

            #Opening a connection to the database
            database_connection = create_engine(self.database_name, echo=True).connect()

            #Adding the user to the database
            database_connection.execute(sql_command) 
            database_connection.close() #Closing the database connection after use

            #Setting the newly registered user as logged in
            session['current_user'] = user_data[self.primary_key]   
        elif (user_already_registered == True) :
            return -1 #Returning failure message
        else :
            raise Exception("Invalid data format")
    
    def number_of_registered_users(self) :
        """Returns the number of users registered in the database"""

        sql_command = f"SELECT COUNT({self.primary_key}) FROM {self.table_name}"

        #Connecting to the database
        database_connection = create_engine(self.database_name, echo=True).connect()

        #Getting and returning the number of users
        sql_result = database_connection.execute(sql_command).first().values()[0]
        database_connection.close() #Closing the database connection
        return sql_result

    def user_already_registered(self, user_data) :
        """Checks whether the user has been already registered"""

        #Constructing the sql command
        sql_command = f"SELECT * FROM {self.table_name} WHERE "
        for unique_cred in self.unique_creds[:-1] :
            sql_command += f"{unique_cred} = '{user_data[unique_cred]}' AND"
        sql_command += f"{self.unique_creds[-1]} = '{user_data[self.unique_creds[-1]]}'"

        #Connecting to the database
        database_connection = create_engine(self.database_name, echo=True).connect()

        #Getting the results
        sql_result = database_connection.execute(sql_command).first()

        #Closing the database connection after use
        database_connection.close()

        return sql_result != None

    def get_current_user(self) :
        """Returns the id of the currently logged user"""

        if("current_user" in session.keys()) :
            return session["current_user"]
        else :
            return None

    def get_user_by_primary_key(self, primary_key) :
        """Returns the user in the database having the given primary key"""

        #Constructing the sql command
        sql_command = f"SELECT * FROM {self.table_name} WHERE {self.primary_key} = '{primary_key}'"

        #Connecting to the database
        database_connection = create_engine(self.database_name, echo=True).connect()

        #Getting the results
        sql_result = database_connection.execute(sql_command).first()

        #Closing the database connection after use
        database_connection.close()

        return sql_result

    def get_user_by_credentials(self, credentials) :
        """Returns the user having the given credentials.
        credentials = dictionary containing the credentials and their values"""

        #Constructing the sql command
        sql_command = f"SELECT * FROM {self.table_name} WHERE "
        creds = list(credentials.keys())
        for cred in creds[:-1] :
            if(not cred in self.fields_to_encrypt) :
                sql_command += f"{cred} = '{credentials[cred]}' AND "
        if (not creds[-1] in self.fields_to_encrypt) :
            sql_command += f"{creds[-1]} = '{credentials[creds[-1]]}'"
        else :
            sql_command = sql_command[:-5] #Removing the trailing " AND "

        #Connecting to the database
        database_connection = create_engine(self.database_name, echo=True).connect()

        #Getting the results
        users = list(database_connection.execute(sql_command))
        database_connection.close() #Closing the connecton after use

        #Checking if users were found
        if(users != None) :
            #Removing the users for whom encrypted credentials do not match
            for user in users :
                if(not self.check_encrypted_creds(credentials, user)) :
                    users.remove(user)

        return users

    def log_user(self, login_credentials) :
        """Logs the given user in
        login_credentials = dictionary containing the login credentials and their values
        return values = {-1 : 'Invalid Credentials', -2 : 'No user found', -3 : 'Wrong credentials', 0 : 'Success' }"""

        #Checking if the required credentials are provided
        if(not equivalent_lists(login_credentials.keys(), self.req_login_credentials)) :
            return -1

        #Connecting to the database
        database_connection = create_engine(self.database_name, echo=True).connect()

        #Checking if user exists
        sql_command = f"SELECT * FROM {self.table_name} WHERE "
        creds = list(login_credentials.keys())
        for cred in creds[:-1] :
            if(not cred in self.fields_to_encrypt) :
                sql_command += f"{cred} = '{login_credentials[cred]}' AND "
        if(not creds[-1] in self.fields_to_encrypt) :
            sql_command += f"{creds[-1]} = '{login_credentials[creds[-1]]}'"
        else :
            sql_command = sql_command[:-5] #Removing the trailing " AND "

        #Getting the user with the credentials
        user = list(database_connection.execute(sql_command))
        if user == None :
            return -2 #No such user was found

        #Closing the database connection after use
        database_connection.close()
        
        #Checking if the user's encrypted credentials match
        if(self.check_encrypted_creds(login_credentials, user[0])) :
            #Creating the user's session
            session['current_user'] = user[0][self.user_attributes.index(self.primary_key)]
            return 0 #Returning success message
        else :
            return -3 #Wrong Credentials

        
    def check_encrypted_creds(self, credentials, stored_creds) :
        """Checks if the encrypted credentials match"""

        creds = list(credentials.keys())
        for cred in creds :
            if(cred in self.fields_to_encrypt) :
                cred_index = self.user_attributes.index(cred)
                if(not check_password_hash(stored_creds[cred_index], credentials[cred])) :
                    return False
                
        return True
            
    def log_user_out(self) :
        """Logs out the currently logged user"""

        session['current_user'] = None

    def update_user_credentials(self, primary_key, new_user_credentials) :
        """Updates or changes the user credentials
        primary_key = Primary key for the user in database
        new_user_credentials = dictionary containing the credentials to update and their respective new values
        return values = {-1 : User does not exist , -2 : User attributes does not contain the credentials to be updated, 0 : Credentials were successfully updated} """

        #Checking if user with given primary key exists
        if(not self.check_if_user_exists(primary_key)) :
            return -1

        #Checking if the provided credentials are valid
        creds_to_update = list(new_user_credentials)
        if(not list_contains_list(creds_to_update, self.user_attributes)) :
            return -2

        #Connecting to the database
        database_connection = create_engine(self.database_name, echo=True).connect()

        #Constructing the sql command
        sql_command = f"UPDATE {self.table_name} SET "
        for cred in creds_to_update[:-1] :
            #Checking if the credential is to be hashed before storing in database
            if(cred in self.fields_to_encrypt) :
                sql_command += f"{cred} = '{generate_password_hash(new_user_credentials[cred])}', "
            else :
                sql_command += f"{cred} = '{new_user_credentials[cred]}', "
        if(creds_to_update[-1] in self.fields_to_encrypt) :
            sql_command += f"{creds_to_update[-1]} = '{generate_password_hash(new_user_credentials[creds_to_update[-1]])}' WHERE {self.primary_key} = '{primary_key}'"
        else :
            sql_command += f"{creds_to_update[-1]} = '{new_user_credentials[creds_to_update[-1]]}' WHERE {self.primary_key} = '{primary_key}'"

        #Updating the credentials stored in the database
        database_connection.execute(sql_command)

        #Closing the database connection after use
        database_connection.close()

        #Returning success message
        return 0
        
    def check_if_user_exists(self, primary_key) :
        """Checks if a user with the given primary key exists in the database"""

        #Connecting to the database
        database_connection = create_engine(self.database_name, echo=True).connect()

        #Constructing the sql command
        sql_command = f"SELECT * FROM {self.table_name} WHERE {self.primary_key} = '{primary_key}'"

        #Checking for user
        sql_res = list(database_connection.execute(sql_command))

        #Closing the database connection after use
        database_connection.close()

        return len(sql_res) != 0

    def delete_user(self, primary_key) :
        """Deletes the given user from the database
        return values = {-1: User does not exits, 0: User profile deleted}"""

        #Checking if a user with the given primary key exists
        if(not self.check_if_user_exists(primary_key)) :
            return -1

        #Connecting to the database
        database_connection = create_engine(self.database_name, echo=True).connect()

        #Constructing the sql command
        sql_command = f"DELETE FROM {self.table_name} WHERE {self.primary_key} = '{primary_key}' "

        #Deleting the user
        database_connection.execute(sql_command)

        #Signing out the user if he was signed in
        if(self.get_current_user() == primary_key) :
            self.log_user_out()

        #Closing the database connection after use
        database_connection.close()

        #Returning success message
        return 0


