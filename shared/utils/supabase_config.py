import os
from supabase import create_client, Client

# url: str = os.environ.get("SUPABASE_URL")
# key: str = os.environ.get("SUPABASE_KEY")

def connect_supabase():
    SUPABASE_URL="https://pggnbchxenibpicpynwj.supabase.co"
    SUPABASE_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBnZ25iY2h4ZW5pYnBpY3B5bndqIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MDgwMzQ2NjUsImV4cCI6MjAyMzYxMDY2NX0.GrrrI6hLeZfeLzkE-kI4nX-efDJ7KYiPD4hmY-DNRuY"

    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


    # try:
    #     supabase.auth.sign_in_with_password(
    #             credentials={"email": "formanalysis24@gmail.com", "password": "form@n12935"}
    #         )
    #     print("Signed In")

    # except Exception as e:
    #     print("Error signing in:", e)
    #     return        

    return supabase


supabase = connect_supabase()