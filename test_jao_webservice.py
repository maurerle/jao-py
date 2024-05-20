from jao import JaoAPIClient
from datetime import datetime, timedelta

client = JaoAPIClient("1ba7533c-e5d1-4fc1-8c28-cf51d77c91f6")
auction_details = client.query_auction_details("CH-DE", 
                datetime(2019,12,31,1), "Yearly")

auction_details = client.query_auction_details("CH-DE", 
                datetime(2019,12,31,5), "Daily")

bids = client.query_auction_bids_by_id("CH-DE-Y-BASE-------190101-01")
horizons = client.query_auction_horizons()
corridors = client.query_auction_corridors()
assert horizons
assert corridors
auction_stats = client.query_auction_stats(datetime(2019,1,1), datetime(2019,12,1), "CH-DE", "Daily")

auction_details = client.query_auction_details_by_month("CH-DE", 
                datetime(2019,1,1), "Daily")

# throws 400
auction_details = client.query_auction_details_by_month("CH-DE", 
                datetime(2019,1,1), "Yearly")

# works
auction_details = client.query_auction_details("CH-DE", 
                datetime(2021,12,31), "Yearly")


auction_details = client.query_auction_details("CH-DE", 
                datetime(2019,12,31,2), "Daily")


auction_stats = client.query_auction_stats(datetime(2019,1,1), datetime(2019,12,1), "CH-DE", "Daily")


auction_stats = client.query_auction_stats_months(datetime(2019,1,2), datetime(2019,12,1)-timedelta(days=1), "CH-DE", "Quarterly")

date_from = datetime(2019,1,18)
date_to = datetime(2019,12,1)
import dateutil.rrule as rr
starts = list(rr.rrule(rr.MONTHLY, bymonthday=1, dtstart=date_from, until=date_to,))
starts.insert(0, date_from)
if starts[-1] != date_to:
    starts.append(date_to)
starts

for i in range(len(starts)-1):
    print(starts[i], starts[i+1])