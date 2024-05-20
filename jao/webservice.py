import requests
import pandas as pd
from datetime import timedelta, date
from calendar import monthrange
from dateutil.relativedelta import relativedelta
from typing import Union


class JaoAPIClient:
    # https://www.jao.eu/page-api/market-data

    BASEURL = "https://api.jao.eu/OWSMP/"

    def __init__(self, api_key):
        self.s = requests.Session()
        self.s.headers.update({
            'user-agent': 'jao-py (github.com/fboerman/jao-py)',
            'AUTH_API_KEY': api_key
        })

    def query_auction_corridors(self):
        r = self.s.get(self.BASEURL + 'getcorridors')
        r.raise_for_status()
        return [x['value'] for x in r.json()]

    def query_auction_horizons(self):
        r = self.s.get(self.BASEURL + 'gethorizons')
        r.raise_for_status()
        return [x['value'] for x in r.json()]

    def query_auction_details(self, corridor: str, date_from: date, date_to: date, horizon: str, shadow_auctions_only: bool = False) -> dict:
        """
        get the auction data for a specified corridor. gives basically everything but the bids themselves

        :param shadow_auctions_only: wether to only retrieve shadow auction results
        :param corridor: string of a valid jao corridor from query_corridors
        :param month: datetime.date object for the month you want the auction data of
        :param horizon: string object for the horizon you want the auction data of
        :return:
        """
        # prepare the specific input arguments needed, start day the day before the months begin
        # end date the last day of the month

        if horizon == "Monthly":
            month_begin = query_date.replace(day=1)
            month_end = query_date.replace(day=monthrange(query_date.year, query_date.month)[1])
            r = self.s.get(self.BASEURL + 'getauctions', params={
                'corridor': corridor,
                'fromdate': (month_begin - timedelta(days=1)).strftime("%Y-%m-%d"),
                'horizon': horizon,
                'todate': month_end.strftime("%Y-%m-%d"),
                'shadow': int(shadow_auctions_only)
            })
        elif horizon == 'Yearly':
            r = self.s.get(self.BASEURL + 'getauctions', params={
                'corridor': corridor,
                'fromdate': f"{date_from.year-1}-12-31",
                'horizon': horizon,
                'shadow': int(shadow_auctions_only)
            })
        else:
            r = self.s.get(self.BASEURL + 'getauctions', params={
                'corridor': corridor,
                'fromdate': date_from.strftime("%Y-%m-%d-%H:%M:%S"),
                'todate': date_to.strftime("%Y-%m-%d"),
                'horizon': horizon,
                'shadow': int(shadow_auctions_only)
            })

        # improves error feedback a lot
        if r.status_code >= 400 and not r.reason:
            r.reason = r.text
        r.raise_for_status()

        data = r.json()
        # prettify the results to only show the first products and results
        res = {x["identification"]: x["results"] for x in data}
        ps = {x["identification"]: x["products"] for x in data}
        products = pd.DataFrame()
        for ident, auction_products in ps.items():
            df = pd.DataFrame(auction_products)
            df["id"] = ident
            products = pd.concat([products, df])

        results = pd.DataFrame()
        for ident, auction_results in res.items():
            df = pd.DataFrame(auction_results)
            df["id"] = ident
            results = pd.concat([results, df])

        del data['results']
        del data['products']

        return data, products, results

    def query_auction_details_by_month(self, corridor: str, query_date: date, horizon="Monthly", shadow_auctions_only: bool = False) -> dict:
        data = self.query_auction_details(corridor, date_from=query_date, date_to=query_date+relativedelta(month=1), horizon=horizon, shadow_auctions_only=shadow_auctions_only)
        return data

    def query_auction_bids_by_month(self, corridor: str, month: date, as_dict: bool = False) -> Union[pd.DataFrame, dict]:
        """
        wrapper function to construct the auction id since its predictable and
          pass it on to the query function for the bids

        :param corridor: string of a valid jao corridor from query_corridors
        :param month: datetime.date object for the month you want the auction bids of
        :param as_dict: boolean wether the result needs to be returned as a dictionary instead of a dataframe
        :return:
        """

        return self.query_auction_bids_by_id(month.strftime(f"{corridor}-M-BASE-------%y%m01-01"), as_dict=as_dict)

    def query_curtailments_by_month(self, corridor: str, month: date, as_dict: bool = False) -> Union[pd.DataFrame, list]:
        month_begin = month.replace(day=1)
        month_end = month.replace(day=monthrange(month.year, month.month)[1])
        r = self.s.get(self.BASEURL + 'getcurtailment', params={
            'corridor': corridor,
            'fromdate': (month_begin - timedelta(days=1)).strftime("%Y-%m-%d"),
            'todate': month_end.strftime("%Y-%m-%d"),
        })

        r.raise_for_status()
        if as_dict:
            return r.json()
        else:
            df = pd.DataFrame(r.json())
            df['curtailmentPeriodStart'] = pd.to_datetime(df['curtailmentPeriodStart'])\
                    .dt.tz_convert('europe/amsterdam')
            df['curtailmentPeriodStop'] = pd.to_datetime(df['curtailmentPeriodStop'])\
                    .dt.tz_convert('europe/amsterdam')
            return df

    def query_auction_bids_by_id(self, auction_id: str, as_dict: bool = False) -> Union[pd.DataFrame, list]:
        r = self.s.get(self.BASEURL + "getbids", params={
            'auctionid': auction_id
        })

        r.raise_for_status()

        if as_dict:
            return r.json()
        else:
            return pd.DataFrame(r.json())

    def query_auction_stats(self, date_from: date, date_to: date, corridor: str, horizon: str = 'Monthly') -> pd.DataFrame:
        """
        gets the following statistics for the give range of months (included both ends) in a dataframe:
        id
        corridor
        month
        auction start
        auction ended
        offered capacity (MW)
        ATC (MW)
        allocated capacity (MW)
        resold capacity (MW)
        requested capacity (MW)
        price (EUR/MW)
        non allocated capacity (MW)
        in this order

        :param date_from: datetime.date object of start month
        :param date_from: datetime.date object of end month
        :param corridor: string of a valid jao corridor from query_corridors
        :param horizon: string of a valid jao horizon from query_horizons
        :return:
        """
        data = []
        pbar = None
        try:
            from tqdm import tqdm
            pbar = tqdm(total=(date_to - date_from).total_seconds()/3600)
        except ImportError:
            pass
        import dateutil.rrule as rr
        starts = list(rr.rrule(rr.MONTHLY, bymonthday=1, dtstart=date_from, until=date_to))
        starts.insert(0, date_from)
        if starts[-1] != date_to:
            starts.append(date_to)
        all_data = pd.DataFrame()
        all_products = pd.DataFrame()
        all_results = pd.DataFrame()
        for i in range(len(starts) - 1):
            from_date = starts[i]
            to_date = starts[i+1]
            data, products, results = self.query_auction_details(corridor=corridor, date_from=from_date, date_to=to_date, horizon=horizon)
            # todo extract date from auction ID
            delta = relativedelta(months=1)
            # can query at max 31 days
            if pbar:
                secs = (m + delta - m).total_seconds()
                pbar.update(secs/3600)
            m += delta
            all_data = pd.concat([all_data, data])
            all_products = pd.concat([all_products, products])
            all_results = pd.concat([all_results, results])
        return all_data, all_products, all_results

    def query_auction_stats_months(self, month_from: date, month_to: date, corridor: str, horizon: str = 'Monthly') -> pd.DataFrame:
        month_from = month_from.replace(day=1)

        return self.query_auction_stats(month_from, month_to, corridor, horizon)