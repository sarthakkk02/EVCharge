# EVCharge – Phase 4

Phase 4 extends the working Phase 3 project with:
- My Bookings history
- Booking status (Confirmed / Cancelled)
- Cancel Booking and automatic slot release
- Admin Dashboard
- User / station / booking statistics
- Add and delete charging stations
- Admin recent-booking table
- Responsive UI improvements

## Run on Windows

Open PowerShell in this folder:

```powershell
pip install -r requirements.txt
python app.py
```

Open:
http://127.0.0.1:5001

## Demo Admin Account

Email: `admin@evcharge.com`
Password: `Admin@123`

Use this only for the local mini-project/demo. Change the credentials and secret key for any real deployment.

## User flow

Register/Login → Dashboard → Find Stations → Book → My Bookings → Cancel if needed.

## Admin flow

Login with demo admin → Admin Dashboard → View statistics → Add/Delete stations → View recent bookings.
