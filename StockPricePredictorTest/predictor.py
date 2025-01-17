# %%
import yfinance as yf
import numpy as np
import matplotlib.pyplot as plt
import requests
import pandas as pd
import re
import json
from datetime import datetime, timedelta
import statsmodels.api as sm
from arch import arch_model
import math
import random

pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)


def filter_values(ticker):
        try:
            tickerData = yf.Ticker(ticker)
            data = tickerData.info
            dataEbitda = 1/data['enterpriseToEbitda']
            dataRoe = data['returnOnEquity']
            revG = data['revenueGrowth']
            if((not np.isnan(dataEbitda)) and (not np.isnan(dataRoe)) and (not np.isnan(revG))):
                if dataRoe>0 and dataEbitda>0: 
                    return dataRoe, dataEbitda, revG
                
            return np.nan, np.nan, np.nan
            

        except Exception as e:
            print(f'Insufficient data on {ticker}')
            return np.nan, np.nan, np.nan

df_stonks = pd.read_csv('StockList.csv')
finalTickers = dict()
#sectors = ['Basic Materials','Consumer Discretionary','Consumer Staples','Energy','Finance','Health Care','Industrials','Miscellaneous','Real Estate','Technology','Telecommunications','Utilities']
sectors = ['Basic Materials']
for sector in sectors:
    print(f'Working on the {sector} sector')
    df_sector = df_stonks.loc[df_stonks['Sector']==sector]
    stock_tickers = df_sector['Symbol']
    roes = dict()
    evebits = dict()
    revGs = dict()
    for ticker in stock_tickers:
        print(f'Analyzing: {ticker}')
        roe, evebit, revG = filter_values(ticker)
        print(f'{ticker}: {roe} {evebit} {revG}')
        if not np.isnan(roe):
            roes[ticker] = roe
        if not np.isnan(evebit):
            evebits[ticker] = evebit
        if not np.isnan(revG):
            revGs[ticker] = revG



    


    mean_roe = np.mean(list(roes.values()))
    std_roe = np.std(list(roes.values()))
    mean_evebits = np.mean(list(evebits.values()))
    std_evebits = np.std(list(evebits.values()))
    mean_rev = np.mean(list(revGs.values()))
    std_rev = np.std(list(revGs.values()))

    roe_mult = mean_evebits/mean_roe
    rev_mult = mean_evebits/mean_rev
    


    file_path = 'StockList_Filtered.csv'
    val_score = dict()

    for stock, roe in roes.items():
        val_score[stock] = roe*roe_mult + evebits[stock] + revGs[stock]*rev_mult

    mean_score = np.mean(list(val_score.values()))
    std_score = np.std(list(val_score.values()))

    for stock, roe in roes.items():
        if val_score[stock]>(mean_score+std_score):
            df_filtered = df_stonks[df_stonks['Symbol'] == stock]
            sec = df_filtered['Sector'].iloc[0]

            finalTickers[stock] = sec

            print(f'{stock} passed')

        else:
            print(f'{stock} failed')

print(f'Filtered Securities: {finalTickers}')







def findSectors(sector):
    stocks = set()
    for key,value in finalTickers.items():
        if value==sector:
            stocks.add(key)
    return stocks


def find_weights(stock_tag):
    
    print(f'Analyzing {stock_tag}')

    ticker = stock_tag
    no_data = False
    ##
    
    def get_financial_ratios(ticker):
        nonlocal no_data
        try:
            url = f'https://eodhd.com/api/fundamentals/{ticker}.US?api_token=6585ff62ed55e1.74792166&fmt=json'
            response = requests.get(url)
            data = (response.json())
            data_string = json.dumps(data, indent=4)
            with open('StockData.txt', 'w') as file:
                file.write(data_string)
        except Exception as e:
            print(f'Could not analyze the following ticker: {ticker}')
            no_data = True
    
    if no_data:
        nothing  = dict()
        empty_df = pd.DataFrame()
        return nothing, empty_df

    data = get_financial_ratios(ticker)


    file_path = 'StockData.txt'



    with open(file_path, 'r') as file:
        file_content = file.read()
    try:
    ### ADD HERE
        def get_financial_ratios(ticker):
            url = f'https://eodhd.com/api/fundamentals/{ticker}.US?api_token=6585ff62ed55e1.74792166&fmt=json'
            response = requests.get(url)
            data = (response.json())
            data_string = json.dumps(data, indent=4)

            # Write the JSON string to a file
            with open('StockData.txt', 'w') as file:
                file.write(data_string)


        data = get_financial_ratios(ticker)


        file_path = 'StockData.txt'

        with open(file_path, 'r') as file:
            file_content = file.read()

        file_content = file_content.replace("'", '"')

        #################################### EPS

        earnings_section_pattern = re.compile(r'"Earnings": \{"History": \{')

        eps_actual_pattern = re.compile(r'"epsActual": ([-+]?\d*\.\d+|None)')

        eps_data = dict()

        earnings_section_start = None
        for i, line in enumerate(file_content.split('\n')):
            if earnings_section_pattern.search(line):
                earnings_section_start = i
                break

        for line in file_content.split('\n')[earnings_section_start:]:
            if 'reportDate' in line:
                report_date = re.search(r'"reportDate": "(\d{4}-\d{2}-\d{2})"', line).group(1)

            eps_actual_match = eps_actual_pattern.search(line)
            if eps_actual_match:
                eps_actual = eps_actual_match.group(1)
                if eps_actual == 'None':
                    eps_actual = None
                else:
                    eps_actual = float(eps_actual)

                eps_data[report_date] = eps_actual

        ####################################### EBITDA


        def extract_quarterly_ebitda(contents, skipped_lines=0):

            contents = contents.replace("'", '"')

            relevant_contents = "\n".join(contents.splitlines()[skipped_lines:])

            pattern = r'"filing_date": "(\d{4}-\d{2}-\d{2})".*?"ebitda": "(\d+.\d+)"'

            # Extracting EBITDA values
            matches = re.findall(pattern, relevant_contents, re.DOTALL)

            ebitda_dict = {filing_date: float(ebitda) for filing_date, ebitda in matches}
            return ebitda_dict

        file_path = 'StockData.txt'
        with open(file_path, 'r') as file:
            contents = file.read()

        ebitda_values = extract_quarterly_ebitda(contents)

        ########################################## net debt

        def extract_net_debt(contents, skipped_lines=0):
            contents = contents.replace("'", '"')

            start_index = contents.find('"Financials": {')
            if start_index == -1:
                return {}  

            relevant_contents = "\n".join(contents[start_index:].splitlines()[skipped_lines:])

            pattern = r'"filing_date": "(\d{4}-\d{2}-\d{2})".*?"netDebt": "(\d+.\d+|null)"'

            matches = re.findall(pattern, relevant_contents, re.DOTALL)

            net_debt_dict = {filing_date: (float(net_debt) if net_debt != 'null' else None) for filing_date, net_debt in matches}
            return net_debt_dict


        file_path = 'StockData.txt'
        with open(file_path, 'r') as file:
            contents = file.read()

        net_debt_values = extract_net_debt(contents)

        ######################################## BOOK VALUE

        def extract_net_debt(contents, skipped_lines=0):
            contents = contents.replace("'", '"')

            start_index = contents.find('"Financials": {')
            if start_index == -1:
                return {}  

            relevant_contents = "\n".join(contents[start_index:].splitlines()[skipped_lines:])

            pattern = r'"filing_date": "(\d{4}-\d{2}-\d{2})".*?"totalStockholderEquity": "(\d+.\d+|null)"'

            matches = re.findall(pattern, relevant_contents, re.DOTALL)

            book_value_dict = {filing_date: (float(net_debt) if net_debt != 'null' else None) for filing_date, net_debt in matches}
            return book_value_dict


        file_path = 'StockData.txt'
        with open(file_path, 'r') as file:
            contents = file.read()

        book_values = extract_net_debt(contents)

        ################################### NET INCOME

        def extract_net_debt(contents, skipped_lines=0):
            contents = contents.replace("'", '"')

            start_index = contents.find('"Cash_Flow": {')
            if start_index == -1:
                return {}  

            relevant_contents = "\n".join(contents[start_index:].splitlines()[skipped_lines:])

            pattern = r'"filing_date": "(\d{4}-\d{2}-\d{2})".*?"netIncome": "(\d+.\d+|null)"'

            matches = re.findall(pattern, relevant_contents, re.DOTALL)

            book_value_dict = {filing_date: (float(net_debt) if net_debt != 'null' else None) for filing_date, net_debt in matches}
            return book_value_dict


        file_path = 'StockData.txt'
        with open(file_path, 'r') as file:
            contents = file.read()

        net_income = extract_net_debt(contents)    

        roe = dict()
        dates = net_income.keys()
        dates = sorted(list(dates))
        count = 0
        for date in dates:
            if count>2:
                if book_values[date] is not None and book_values[date]!=0:
                    roe[date] = (net_income[dates[count]]+net_income[dates[count-1]]+net_income[dates[count-2]]+net_income[dates[count-3]])/(book_values[dates[count]]+book_values[dates[count-1]]+book_values[dates[count-2]]+book_values[dates[count-3]])

            count+=1




        ########################################### Price/Market Cap calculations

        def extract_net_debt(contents, skipped_lines=0):
            contents = contents.replace("'", '"')

            start_index = contents.find('"Financials": {')
            if start_index == -1:
                return {}  

            relevant_contents = "\n".join(contents[start_index:].splitlines()[skipped_lines:])

            pattern = r'"filing_date": "(\d{4}-\d{2}-\d{2})".*?"commonStockSharesOutstanding": "(\d+.\d+|null)"'

            matches = re.findall(pattern, relevant_contents, re.DOTALL)

            outstanding_shares = {filing_date: (float(net_debt) if net_debt != 'null' else None) for filing_date, net_debt in matches}
            return outstanding_shares


        file_path = 'StockData.txt'
        with open(file_path, 'r') as file:
            contents = file.read()

        num_outstanding_shares = extract_net_debt(contents)


        dates = list(num_outstanding_shares.keys())
        start_date = min(dates)
        end_date = max(dates)
        end_date = datetime.strptime(end_date, '%Y-%m-%d') + pd.DateOffset(months=1)
        end_date_str = end_date.strftime('%Y-%m-%d')
        data = yf.download(ticker, start=start_date, end=end_date)

        data.index = data.index.strftime('%Y-%m-%d')

        share_prices = {date: data.at[date, 'Close'] if date in data.index else None for date in dates}
        all_dates = pd.date_range(start=start_date, end=end_date_str, freq='D').strftime('%Y-%m-%d')
        total_prices = {date: data.at[date, 'Close'] if date in data.index else None for date in all_dates}
        market_caps = {}

        for date, shares in num_outstanding_shares.items():
            if date in share_prices and shares is not None and share_prices[date] is not None:
                market_caps[date] = share_prices[date] * shares


        ########################################### ENTERPRISE VALUES, EV/EBITDA, P/B, P/E 

        enterpriseValues = {}

        for date, mCaps in market_caps.items():
            try:
                if mCaps is not None and net_debt_values[date] is not None:
                    enterpriseValues[date] = mCaps + net_debt_values[date]
            except KeyError:
                pass
        evtoEbitda = {}

        ev_dates = sorted(list(enterpriseValues.keys()))
        count = 0
        for date in ev_dates:
            if count>2:
                try:
                    current_ebit_sum = ebitda_values[ev_dates[count]] + ebitda_values[ev_dates[count-1]] + ebitda_values[ev_dates[count-2]] + ebitda_values[ev_dates[count-3]]
                    if ebitda_values[date] is not None:
                        evtoEbitda[date] = current_ebit_sum/enterpriseValues[date]             
                except KeyError:
                    pass
            count+=1
            

        pricetoBook = {}

        for date, bookValue in book_values.items():
            try:
                if bookValue is not None and total_prices[date] is not None:
                    pricetoBook[date] = bookValue/(total_prices[date]*num_outstanding_shares[date])
            except KeyError:
                pass

        pricetoEarnings = {}

        eps_dates = sorted(list(eps_data.keys()))
        count = 0
        for date in eps_dates:
            
            if count > 2:
                try:
                    current_eps_sum = eps_data[eps_dates[count]] + eps_data[eps_dates[count-1]] + eps_data[eps_dates[count-2]] + eps_data[eps_dates[count-3]]
                    if total_prices[date] is not None:
                        pricetoEarnings[date] = current_eps_sum/total_prices[date] 
                except KeyError as e:
                    pass

            count += 1


        ######################################## REVENUE GROWTH 
        def extract_quarterly_rev(contents, skipped_lines=0):
            start_index = contents.find('"Income_Statement": {')
            if start_index == -1:
                return {} 
            quarterly_start_index = contents.find('"quarterly": {', start_index)
            if quarterly_start_index == -1:
                return {}  
            yearly_start_index = contents.find('"yearly": {', start_index)
            if yearly_start_index == -1:
                yearly_start_index = None
            relevant_contents = "\n".join(contents[quarterly_start_index:yearly_start_index].splitlines()[skipped_lines:])
            pattern = r'"filing_date": "(\d{4}-\d{2}-\d{2})".*?"totalRevenue": "(\d+.\d+)"'
            matches = re.findall(pattern, relevant_contents, re.DOTALL)

            rev_dict = {filing_date: (float(revenue) if revenue != 'null' else None) for filing_date, revenue in matches}
            return rev_dict


        file_path = 'StockData.txt'
        with open(file_path, 'r') as file:
            contents = file.read()

        revenue_values = extract_quarterly_rev(contents)

        date_list = sorted(revenue_values.keys())

        revenue_growth = dict()

        for i in range(1, len(date_list)):
            current_date = date_list[i]
            previous_date = date_list[i-1]
            current_revenue = revenue_values[current_date]
            previous_revenue = revenue_values[previous_date]
            if(previous_revenue != 0):
                growth = (current_revenue - previous_revenue)/previous_revenue
                revenue_growth[current_date] = growth

        revenue_growth_ttm = dict()

        for i in range(4, len(date_list)):
            current_date = date_list[i]
            previous_date = date_list[i-4]
            current_revenue = revenue_values[current_date]
            previous_revenue = revenue_values[previous_date]
            if(previous_revenue != 0):
                growth = (current_revenue - previous_revenue)/previous_revenue
                revenue_growth_ttm[current_date] = growth

        evtoEbitda_ttm = dict()
        date_list = sorted(evtoEbitda.keys())

        for i in range(4, len(date_list)):
            current_date = date_list[i]
            previous_date = date_list[i-4]
            current_revenue = evtoEbitda[current_date]
            previous_revenue = evtoEbitda[previous_date]
            if(previous_revenue != 0):
                growth = (current_revenue - previous_revenue)/previous_revenue
                evtoEbitda_ttm[current_date] = growth

        pricetoBook_ttm = dict()
        date_list = sorted(pricetoBook.keys())

        for i in range(4, len(date_list)):
            current_date = date_list[i]
            previous_date = date_list[i-4]
            current_revenue = pricetoBook[current_date]
            previous_revenue = pricetoBook[previous_date]
            if(previous_revenue != 0):
                growth = (current_revenue - previous_revenue)/previous_revenue
                pricetoBook_ttm[current_date] = growth

        pricetoEarnings_ttm = dict()
        date_list = sorted(pricetoEarnings.keys())

        for i in range(4, len(date_list)):
            current_date = date_list[i]
            previous_date = date_list[i-4]
            current_revenue = pricetoEarnings[current_date]
            previous_revenue = pricetoEarnings[previous_date]
            if(previous_revenue != 0):
                growth = (current_revenue - previous_revenue)/previous_revenue
                pricetoEarnings_ttm[current_date] = growth

        eps_growth = dict()
        date_list2 = sorted(eps_data.keys())
        for i in range(1, (len(date_list2))):
            current_eps = eps_data[date_list2[i]]
            previous_eps = eps_data[date_list2[i-1]]
            if(previous_eps != 0):
                growth = ((current_eps)/previous_eps)**4
                eps_growth[date_list2[i]] = growth

        pe_growth = dict()
        for date, peRatio in pricetoEarnings.items():
            try:
                if peRatio is not None and eps_growth[date] is not None and eps_growth[date]!=0:
                    pe_growth[date] = peRatio/eps_growth[date]
            except KeyError:
                pass

        pe_growth_ttm = dict()
        date_list2 = sorted(pe_growth.keys())
        for i in range(4, (len(date_list2))):
            current_eps = pe_growth[date_list2[i]]
            previous_eps = pe_growth[date_list2[i-4]]
            if(previous_eps != 0):
                growth = (current_eps)/previous_eps
                pe_growth_ttm[date_list2[i]] = -1*growth

        quarterly_returns = dict()
        for i in range(0, (len(date_list))):
            if i<(len(date_list)-1):
                current_price = total_prices[date_list[i]]
                future_price = total_prices[date_list[i+1]]
                if(current_price != 0):
                    growth = (future_price - current_price)/current_price
                    quarterly_returns[date_list[i]] = growth  

        yearly_returns = dict()
        for i in range(0, (len(date_list))):
            if i<(len(date_list)-4):
                current_price = total_prices[date_list[i]]
                future_price = total_prices[date_list[i+4]]
                if current_price!=0:
                    growth = (future_price - current_price)/current_price
                    yearly_returns[date_list[i]] = growth
            elif i<(len(date_list)-2):
                current_price = total_prices[date_list[i]]
                future_price = total_prices[date_list[(len(date_list)-1)]]
                if current_price!=0:
                    growth = (future_price - current_price)/current_price
                    yearly_returns[date_list[i]] = growth

        ##################################### MERGE ALL METRICS

        def find_values_within_range(df, column_name, value_df):
            for index, row in df.iterrows():
                mask = (value_df['Date'] >= row['Start_Period']) & (value_df['Date'] <= row['End_Period'])
                values_within_range = value_df[mask][column_name].values

                if len(values_within_range) > 0:
                    df.at[index, column_name] = values_within_range[0]  

        df_eps = pd.DataFrame(list(eps_data.items()), columns=['Date', 'EPS'])
        df_eps['Date'] = pd.to_datetime(df_eps['Date'])

        def create_df_from_dict(data_dict, column_name):
            df = pd.DataFrame(list(data_dict.items()), columns=['Date', column_name])
            df['Date'] = pd.to_datetime(df['Date'])
            return df

        df_priceEarnings = create_df_from_dict(pricetoEarnings, 'Price_to_Earnings')
        df_priceEarnings_ttm = create_df_from_dict(pricetoEarnings_ttm, 'Price_to_Earnings_TTM')
        df_priceBook = create_df_from_dict(pricetoBook, 'Price_to_Book')
        df_priceBook_ttm = create_df_from_dict(pricetoBook_ttm, 'Price_to_Book_TTM')
        df_evEbitda = create_df_from_dict(evtoEbitda, 'EV_to_EBITDA')
        df_evEbitda_ttm = create_df_from_dict(evtoEbitda_ttm, 'EV_to_EBITDA_TTM')
        df_revenueGrowth = create_df_from_dict(revenue_growth, 'Revenue_Growth')
        df_revenueGrowth_ttm = create_df_from_dict(revenue_growth_ttm, 'Revenue_Growth_TTM')
        df_priceEarningsGrowth = create_df_from_dict(pe_growth, 'PE_to_Growth')
        df_priceEarningsGrowth_ttm = create_df_from_dict(pe_growth_ttm, 'PE_to_Growth_TTM')
        df_roe = create_df_from_dict(roe, 'ROE')
        df_quarterlyReturns = create_df_from_dict(quarterly_returns, 'Quarterly_Returns')
        df_yearlyReturns = create_df_from_dict(yearly_returns, 'Yearly_Returns')


        additional_columns = ['Price_to_Earnings', 'Price_to_Earnings_TTM', 'Price_to_Book', 'Price_to_Book_TTM', 'EV_to_EBITDA', 'EV_to_EBITDA_TTM', 'Revenue_Growth', 'Revenue_Growth_TTM', 'PE_to_Growth', 'PE_to_Growth_TTM', 'ROE','Quarterly_Returns', 'Yearly_Returns']
        for col in additional_columns:
            df_eps[col] = np.nan

        df_eps['Start_Period'] = df_eps['Date'] - pd.DateOffset(months=1)
        df_eps['End_Period'] = df_eps['Date'] + pd.DateOffset(months=1)

        dataframes_to_merge = [df_priceEarnings, df_priceEarnings_ttm, df_priceBook, df_priceBook_ttm,
                            df_evEbitda, df_evEbitda_ttm, df_revenueGrowth, df_revenueGrowth_ttm, df_priceEarningsGrowth, df_priceEarningsGrowth_ttm, df_roe, df_quarterlyReturns, df_yearlyReturns]

        for df in dataframes_to_merge:
            column_name = df.columns[1]
            find_values_within_range(df_eps, column_name, df)

        df_final = df_eps.drop(['Start_Period', 'End_Period'], axis=1).fillna(np.nan)


        ################################################### OLS REGRESSION FOR COMPOSITE METRIC


        independent_vars = ['EPS','Price_to_Earnings', 'Price_to_Book', 'EV_to_EBITDA', 'Revenue_Growth_TTM', 'PE_to_Growth_TTM','ROE']

        dependent_var = 'Yearly_Returns'

        df_analysis = df_final.dropna(subset=independent_vars + [dependent_var])

        X = df_analysis[independent_vars]
        y = df_analysis[dependent_var]

        if len(X)==0 or len(y)==0:
            dependent_var = 'Quarterly_Returns'
            df_analysis = df_final.dropna(subset=independent_vars + [dependent_var])
            X = df_analysis[independent_vars]
            y = df_analysis[dependent_var]


        X = sm.add_constant(X)

        model = sm.OLS(y, X)

        results = model.fit()

        print(results.summary())

        final_weights = np.array(results.params)

        #print(results.summary())
        ####### ADD HERE
        final_weights = np.array(results.params)
        print(f'Successfully Analyzed {ticker}')
        return final_weights, df_final
    
    except Exception as e:
        print(f'Unable to calculate KPI for {ticker}')
        nothing  = dict()
        empty_df = pd.DataFrame()
        return nothing, empty_df

    


def calculate_sector_averages(sectors):
    sector_averages = {}
    stock_weights = dict()
    for sector in sectors:
        print(f'Evaluating stocks in the {sector} sector')
        stocks = findSectors(sector)
        total_weights = dict()
        total_weights['EPS'] = 0
        total_weights['P/E'] = 0
        total_weights['P/B'] = 0
        total_weights['EV/EBITDA'] = 0
        total_weights['RevGrowth'] = 0
        total_weights['PEG'] = 0
        numWeights = 0
        for stock in stocks:
            numWeights+=1
            temp_weight, df_nah = find_weights(stock)
            if(len(temp_weight)>0):
                total_weights['EPS'] += temp_weight[0]
                total_weights['P/E'] += temp_weight[1]
                total_weights['P/B'] += temp_weight[2]
                total_weights['EV/EBITDA'] += temp_weight[3]
                total_weights['RevGrowth'] += temp_weight[4]
                total_weights['PEG'] += temp_weight[5]
        total_weights['EPS'] /= numWeights
        total_weights['P/E'] /= numWeights
        total_weights['P/B'] /= numWeights
        total_weights['EV/EBITDA'] /= numWeights
        total_weights['RevGrowth'] /= numWeights
        total_weights['PEG'] /= numWeights

        for stock in stocks:
            temp_weight, df_use = find_weights(stock)
            if(len(temp_weight)>0):
                current_values = df_use.iloc[0].tolist()
                kpi = (current_values[1]*total_weights['EPS'] + current_values[2]*total_weights['P/E'] + current_values[3]*total_weights['P/B'] + current_values[4]*total_weights['EV/EBITDA'] + current_values[5]*total_weights['RevGrowth'] + current_values[6]*total_weights['PEG'])
                stock_weights[stock] = kpi

        kpi_values = list(stock_weights.values())
        mean_kpi = np.mean(kpi_values)
        std_kpi = np.std(kpi_values)
        sector_averages = {mean_kpi, std_kpi}
        print(f'Averages for {sector}: {sector_averages}')
        print(f'Indicator Coefficiencts for the {sector} sector:')
        for indicator, kpiX in total_weights.items():
            print(f'{indicator}: {kpiX}')

    return stock_weights

################################## QUANTITATIVE ANALYSIS

def quantAnalysis(ticker):
    
    tag = str(ticker)
    symbols_to_remove = ["(", ")", "'", ","]
    for symbol in symbols_to_remove:
        tag = tag.replace(symbol, "")

    tag = tag.upper()
    print(f'Quantitative Analysis: {tag}')
    num_simulations = random.randint(50, 300)

    numWeeks = 10
    df = yf.download(tag, '2023-09-01', '2023-12-13')

    # GET 252-D MA IV30

    #url = f'https://marketchameleon.com/Overview/{tag}/IV/'
    #print(f'Please access the folowing link: {url}')

    # EIV = input('Once there, locate the 252-Day HV mean which can be found in the following format: 252 day HV (type this value) mean. Then type this value in: ')

    """
    try:
        EIV_numeric = float(EIV)
        expectedIV = EIV_numeric / 100
        print("The expected IV is:", expectedIV)
    except ValueError:
        print("Invalid input. Please enter a numeric value.")

    """



    
    pd.set_option('display.max_rows', None)
    pd.set_option('display.max_columns', None)


    priceData = df['Close']
    volatilityData = df['Volume']
    returns = np.diff(priceData) / priceData[:-1]

    ### GARCH

    model = arch_model(returns, vol='Garch', p=1, q=1)
    results = model.fit()
    numDataPoints = len(priceData)

    #print(results.summary())
    scale = np.mean(volatilityData)**1.2
    volatility = np.sqrt(results.conditional_volatility**2)

    """
    plt.figure(figsize=(10, 6))
    plt.plot(volatilityData.index, volatilityData, label='Real Volatility')
    plt.plot(returns.index, volatility * scale, label='Model Volatility')
    """
    forecast_steps = 100
    forecasted_volatility = []

    current_volatility = results.conditional_volatility.iloc[-1]
    mu = np.mean(returns)
    omega = results.params['omega']
    alpha = results.params['alpha[1]']
    beta = results.params['beta[1]']

    for _ in range(forecast_steps):
        current_volatility = np.sqrt(omega + alpha * (returns[-1] - mu)**2 + beta * current_volatility**2)
        forecasted_volatility.append(current_volatility)

    forecasted_volatility = np.array(forecasted_volatility) * scale
    forecasted_dates = pd.date_range(start=returns.index[-1], periods=forecast_steps + 1, freq='B')[1:]
    """
    plt.plot(forecasted_dates, forecasted_volatility, label=f'Forecasted Volatility ({forecast_steps} steps)')
    plt.title(f'GARCH(1,1) Volatility Model - {tag.upper()}')
    plt.xlabel('Date')
    plt.ylabel('Volatility')
    plt.legend()
    plt.show()
    """

    # BLACK SCHOLES (IV)



    options_data = yf.Ticker(tag).options
    options_prices = {}
    for expiration_date in options_data:
        options_chain = yf.Ticker(tag).option_chain(expiration_date)
        call_prices = options_chain.calls
        put_prices = options_chain.puts
        options_prices[expiration_date] = {
            'calls': call_prices,
            'puts': put_prices
        }
    option_data_call = []
    option_data_put = []
    for expiration_date, option_prices in options_prices.items():
        if 'calls' in option_prices and 'puts' in option_prices:
            call_data = option_prices['calls']
            put_data = option_prices['puts']

            call_data['expiration_date'] = expiration_date
            put_data['expiration_date'] = expiration_date

            option_data_call.append(call_data)
            option_data_put.append(put_data)

    options_df_call = pd.concat(option_data_call, ignore_index=True)
    options_df_put = pd.concat(option_data_put, ignore_index=True)

    options_df_call = options_df_call.sort_values(by=['expiration_date', 'strike'])
    options_df_put = options_df_put.sort_values(by=['expiration_date', 'strike'])

    atmRange = priceData[-1]



    def find_closest_friday_one_months_from_now(numWeeks):
        current_date = datetime.now()
        four_months_later = current_date + timedelta(days=(numWeeks*7))
        days_until_friday = (4 - four_months_later.weekday() + 7) % 7
        closest_friday = four_months_later + timedelta(days=days_until_friday)
        return closest_friday

    expiration_date = find_closest_friday_one_months_from_now(numWeeks)
    expiration_date = str(expiration_date)[0:10]
    atmPrice = -1

    for strikeP in options_df_call['strike']:
        if (strikeP > (atmRange-2.5)) & (strikeP < (atmRange+10)):
            atmPrice = strikeP
    garchForecast = forecasted_volatility[numWeeks*7]/scale
    iv = options_df_call.loc[(options_df_call['expiration_date']==expiration_date) & (options_df_call['strike']==atmPrice)]['impliedVolatility']
    if iv.size == 0:
        finalVolatility = garchForecast
    else:
        lamma = 0.2
        finalVolatility = lamma*garchForecast + (1-lamma)*iv/10


    # GEOMETRIC BROWNIAN MOTION

    seven_days_ago = datetime.today() - timedelta(days=7)
    curPri = yf.download(tag, start=seven_days_ago, end=datetime.today())
    currentPrice = curPri['Adj Close'][-1]

    num_steps = numWeeks*7  
    average_model_prices = np.zeros(num_steps+1)
    average_model_prices[0] = currentPrice

    def simulate_gbm(S0, r, sigma_combined, T, num_simulations, num_steps):
        dt = T / num_steps
        stock_prices = np.zeros((num_simulations, num_steps + 1))
        stock_prices[:, 0] = S0

        for i in range(1, num_steps + 1):
            Z = np.random.standard_normal(num_simulations)
            count = 0
            for j in range(num_simulations):
                stock_prices[j, i] = stock_prices[j, i - 1] * np.exp((r - 0.5 * sigma_combined**2) * dt + sigma_combined * np.sqrt(dt) * Z[j])
                count+=stock_prices[j, i]
            count = count/num_simulations
            average_model_prices[i]=(count)
        return stock_prices

    def plot_simulation(stock_prices, T):
        num_simulations, num_steps = stock_prices.shape
        time_steps  = []

        for i in range(num_steps):
            time_steps.append(i)
        
        plt.figure(figsize=(10, 6))
        for i in range(num_simulations):
            plt.plot(time_steps, stock_prices[i, :], lw=1, alpha=0.6)
        plt.plot(time_steps, average_model_prices, label='Average Price Forecast')
        plt.title(f'Simulation of {tag} Prices')
        plt.xlabel('Number of Days')
        plt.ylabel(f'{tag} Price (USD)')
        plt.legend()
        plt.show()



    mu = np.diff(priceData) / priceData[:-1]
    drift = np.mean(mu)



    S0_value = currentPrice 

    sigma_combined = finalVolatility  
    r = drift
    T = 1.0     

    S0 = np.full((num_simulations,), S0_value)


    simulated_stock_prices = simulate_gbm(S0, r, sigma_combined, T, num_simulations, num_steps)
    plot_simulation(simulated_stock_prices, T)

    time_steps  = []

    for i in range(num_steps+1):
        time_steps.append(i)

    """
    plt.plot(time_steps, average_model_prices, label = 'Average Predicted Price')
    plt.xlabel('Number of Days')
    plt.ylabel(f'{tag} Price (USD)')
    plt.title('Average Model Price Prediction')
    plt.show()
    """

    predicted_returns = (simulated_stock_prices[-1]-simulated_stock_prices[0])/simulated_stock_prices[0]
    return predicted_returns


############ MAIN CODE

df = pd.read_csv('StockList.csv')
stock_ratio_map = {}



targetSharesUnder = list()
targetSharesOver = list()

stock_weights = calculate_sector_averages(sectors)
stock_weights = {k: v for k, v in stock_weights.items() if not math.isnan(v)}
kpis = list(stock_weights.values())
mean = np.mean(kpis)
std = np.std(kpis)
targetSharesUnder = list()
targetSharesOver = list()
for stock, kpiX in stock_weights.items():
    if(kpiX>=(mean+(2*std))):
        targetSharesUnder.append(stock)
    elif (kpiX<=(mean-std)):
        targetSharesOver.append(stock)

def custom_sort_key(stock):
    return stock_weights.get(stock, 0)  

sorted_stocks = sorted(targetSharesUnder, key=custom_sort_key)


print(f'Selected Shares: {sorted_stocks}')

final_prices = dict()

for stock in sorted_stocks:
    final_prices[stock] = quantAnalysis(stock)
    print(f'Predicted Returns for {stock}: {final_prices[stock]}')






















# %%
#SMCI GOOGLE AMAZON MICROSOFT AND NOT NVDA



import yfinance as yf
ticker = yf.Ticker('AAPL')
data = ticker.info
data['revenueGrowth']











# %%


#################################### KPI TEST




import yfinance as yf
import numpy as np
import matplotlib.pyplot as plt
import requests
import pandas as pd
import re
import json
from datetime import datetime, timedelta
import statsmodels.api as sm
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)

ticker = 'CHPT'



def get_financial_ratios(ticker):
    url = f'https://eodhd.com/api/fundamentals/{ticker}.US?api_token=6585ff62ed55e1.74792166&fmt=json'
    response = requests.get(url)
    data = (response.json())
    data_string = json.dumps(data, indent=4)

    # Write the JSON string to a file
    with open('StockData.txt', 'w') as file:
        file.write(data_string)


data = get_financial_ratios(ticker)


file_path = 'StockData.txt'

with open(file_path, 'r') as file:
    file_content = file.read()

file_content = file_content.replace("'", '"')

#################################### EPS

earnings_section_pattern = re.compile(r'"Earnings": \{"History": \{')

eps_actual_pattern = re.compile(r'"epsActual": ([-+]?\d*\.\d+|None)')

eps_data = dict()

earnings_section_start = None
for i, line in enumerate(file_content.split('\n')):
    if earnings_section_pattern.search(line):
        earnings_section_start = i
        break

for line in file_content.split('\n')[earnings_section_start:]:
    if 'reportDate' in line:
        report_date = re.search(r'"reportDate": "(\d{4}-\d{2}-\d{2})"', line).group(1)

    eps_actual_match = eps_actual_pattern.search(line)
    if eps_actual_match:
        eps_actual = eps_actual_match.group(1)
        if eps_actual == 'None':
            eps_actual = None
        else:
            eps_actual = float(eps_actual)

        eps_data[report_date] = eps_actual

####################################### EBITDA


def extract_quarterly_ebitda(contents, skipped_lines=0):

    contents = contents.replace("'", '"')

    relevant_contents = "\n".join(contents.splitlines()[skipped_lines:])

    pattern = r'"filing_date": "(\d{4}-\d{2}-\d{2})".*?"ebitda": "(\d+.\d+)"'

    # Extracting EBITDA values
    matches = re.findall(pattern, relevant_contents, re.DOTALL)

    ebitda_dict = {filing_date: float(ebitda) for filing_date, ebitda in matches}
    return ebitda_dict

file_path = 'StockData.txt'
with open(file_path, 'r') as file:
    contents = file.read()

ebitda_values = extract_quarterly_ebitda(contents)

########################################## net debt

def extract_net_debt(contents, skipped_lines=0):
    contents = contents.replace("'", '"')

    start_index = contents.find('"Financials": {')
    if start_index == -1:
        return {}  

    relevant_contents = "\n".join(contents[start_index:].splitlines()[skipped_lines:])

    pattern = r'"filing_date": "(\d{4}-\d{2}-\d{2})".*?"netDebt": "(\d+.\d+|null)"'

    matches = re.findall(pattern, relevant_contents, re.DOTALL)

    net_debt_dict = {filing_date: (float(net_debt) if net_debt != 'null' else None) for filing_date, net_debt in matches}
    return net_debt_dict


file_path = 'StockData.txt'
with open(file_path, 'r') as file:
    contents = file.read()

net_debt_values = extract_net_debt(contents)

######################################## BOOK VALUE

def extract_net_debt(contents, skipped_lines=0):
    contents = contents.replace("'", '"')

    start_index = contents.find('"Financials": {')
    if start_index == -1:
        return {}  

    relevant_contents = "\n".join(contents[start_index:].splitlines()[skipped_lines:])

    pattern = r'"filing_date": "(\d{4}-\d{2}-\d{2})".*?"totalStockholderEquity": "(\d+.\d+|null)"'

    matches = re.findall(pattern, relevant_contents, re.DOTALL)

    book_value_dict = {filing_date: (float(net_debt) if net_debt != 'null' else None) for filing_date, net_debt in matches}
    return book_value_dict


file_path = 'StockData.txt'
with open(file_path, 'r') as file:
    contents = file.read()

book_values = extract_net_debt(contents)

################################### NET INCOME

def extract_net_debt(contents, skipped_lines=0):
    contents = contents.replace("'", '"')

    start_index = contents.find('"Cash_Flow": {')
    if start_index == -1:
        return {}  

    relevant_contents = "\n".join(contents[start_index:].splitlines()[skipped_lines:])

    pattern = r'"filing_date": "(\d{4}-\d{2}-\d{2})".*?"netIncome": "(\d+.\d+|null)"'

    matches = re.findall(pattern, relevant_contents, re.DOTALL)

    book_value_dict = {filing_date: (float(net_debt) if net_debt != 'null' else None) for filing_date, net_debt in matches}
    return book_value_dict


file_path = 'StockData.txt'
with open(file_path, 'r') as file:
    contents = file.read()

net_income = extract_net_debt(contents)    

roe = dict()
dates = net_income.keys()
dates = sorted(list(dates))
count = 0
for date in dates:
    if count>2:

        try:
            roe[date] = (net_income[dates[count]]+net_income[dates[count-1]]+net_income[dates[count-2]]+net_income[dates[count-3]])/(book_values[dates[count]]+book_values[dates[count-1]]+book_values[dates[count-2]]+book_values[dates[count-3]])
        except Exception as e:
            pass
    count+=1




########################################### Price/Market Cap calculations

def extract_net_debt(contents, skipped_lines=0):
    contents = contents.replace("'", '"')

    start_index = contents.find('"Financials": {')
    if start_index == -1:
        return {}  

    relevant_contents = "\n".join(contents[start_index:].splitlines()[skipped_lines:])

    pattern = r'"filing_date": "(\d{4}-\d{2}-\d{2})".*?"commonStockSharesOutstanding": "(\d+.\d+|null)"'

    matches = re.findall(pattern, relevant_contents, re.DOTALL)

    outstanding_shares = {filing_date: (float(net_debt) if net_debt != 'null' else None) for filing_date, net_debt in matches}
    return outstanding_shares


file_path = 'StockData.txt'
with open(file_path, 'r') as file:
    contents = file.read()

num_outstanding_shares = extract_net_debt(contents)


dates = list(num_outstanding_shares.keys())
start_date = min(dates)
end_date = max(dates)
end_date = datetime.strptime(end_date, '%Y-%m-%d') + pd.DateOffset(months=1)
end_date_str = end_date.strftime('%Y-%m-%d')
data = yf.download(ticker, start=start_date, end=end_date)

data.index = data.index.strftime('%Y-%m-%d')

share_prices = {date: data.at[date, 'Close'] if date in data.index else None for date in dates}
all_dates = pd.date_range(start=start_date, end=end_date_str, freq='D').strftime('%Y-%m-%d')
total_prices = {date: data.at[date, 'Close'] if date in data.index else None for date in all_dates}
market_caps = {}

for date, shares in num_outstanding_shares.items():
    if date in share_prices and shares is not None and share_prices[date] is not None:
        market_caps[date] = share_prices[date] * shares


########################################### ENTERPRISE VALUES, EV/EBITDA, P/B, P/E 

enterpriseValues = {}

for date, mCaps in market_caps.items():
    try:
        if mCaps is not None and net_debt_values[date] is not None:
            enterpriseValues[date] = mCaps + net_debt_values[date]
    except KeyError:
        pass
evtoEbitda = {}

ev_dates = sorted(list(enterpriseValues.keys()))
count = 0
for date in ev_dates:
    if count>2:
        try:
            current_ebit_sum = ebitda_values[ev_dates[count]] + ebitda_values[ev_dates[count-1]] + ebitda_values[ev_dates[count-2]] + ebitda_values[ev_dates[count-3]]
            if ebitda_values[date] is not None:
                evtoEbitda[date] = current_ebit_sum/enterpriseValues[date]             
        except KeyError:
            pass
    count+=1
    

pricetoBook = {}

for date, bookValue in book_values.items():
    try:
        if bookValue is not None and total_prices[date] is not None:
            pricetoBook[date] = bookValue/(total_prices[date]*num_outstanding_shares[date])
    except KeyError:
        pass

pricetoEarnings = {}

eps_dates = sorted(list(eps_data.keys()))
count = 0
for date in eps_dates:
    
    if count > 2:
        try:
            current_eps_sum = eps_data[eps_dates[count]] + eps_data[eps_dates[count-1]] + eps_data[eps_dates[count-2]] + eps_data[eps_dates[count-3]]
            if total_prices[date] is not None:
                pricetoEarnings[date] = current_eps_sum/total_prices[date] 
        except KeyError as e:
            pass

    count += 1


######################################## REVENUE GROWTH 
def extract_quarterly_rev(contents, skipped_lines=0):
    start_index = contents.find('"Income_Statement": {')
    if start_index == -1:
        return {} 
    quarterly_start_index = contents.find('"quarterly": {', start_index)
    if quarterly_start_index == -1:
        return {}  
    yearly_start_index = contents.find('"yearly": {', start_index)
    if yearly_start_index == -1:
        yearly_start_index = None
    relevant_contents = "\n".join(contents[quarterly_start_index:yearly_start_index].splitlines()[skipped_lines:])
    pattern = r'"filing_date": "(\d{4}-\d{2}-\d{2})".*?"totalRevenue": "(\d+.\d+)"'
    matches = re.findall(pattern, relevant_contents, re.DOTALL)

    rev_dict = {filing_date: (float(revenue) if revenue != 'null' else None) for filing_date, revenue in matches}
    return rev_dict


file_path = 'StockData.txt'
with open(file_path, 'r') as file:
    contents = file.read()

revenue_values = extract_quarterly_rev(contents)

date_list = sorted(revenue_values.keys())

revenue_growth = dict()

for i in range(1, len(date_list)):
    current_date = date_list[i]
    previous_date = date_list[i-1]
    current_revenue = revenue_values[current_date]
    previous_revenue = revenue_values[previous_date]
    if(previous_revenue != 0):
        growth = (current_revenue - previous_revenue)/previous_revenue
        revenue_growth[current_date] = growth

revenue_growth_ttm = dict()

for i in range(4, len(date_list)):
    current_date = date_list[i]
    previous_date = date_list[i-4]
    current_revenue = revenue_values[current_date]
    previous_revenue = revenue_values[previous_date]
    if(previous_revenue != 0):
        growth = (current_revenue - previous_revenue)/previous_revenue
        revenue_growth_ttm[current_date] = growth

evtoEbitda_ttm = dict()
date_list = sorted(evtoEbitda.keys())

for i in range(4, len(date_list)):
    current_date = date_list[i]
    previous_date = date_list[i-4]
    current_revenue = evtoEbitda[current_date]
    previous_revenue = evtoEbitda[previous_date]
    if(previous_revenue != 0):
        growth = (current_revenue - previous_revenue)/previous_revenue
        evtoEbitda_ttm[current_date] = growth

pricetoBook_ttm = dict()
date_list = sorted(pricetoBook.keys())

for i in range(4, len(date_list)):
    current_date = date_list[i]
    previous_date = date_list[i-4]
    current_revenue = pricetoBook[current_date]
    previous_revenue = pricetoBook[previous_date]
    if(previous_revenue != 0):
        growth = (current_revenue - previous_revenue)/previous_revenue
        pricetoBook_ttm[current_date] = growth

pricetoEarnings_ttm = dict()
date_list = sorted(pricetoEarnings.keys())

for i in range(4, len(date_list)):
    current_date = date_list[i]
    previous_date = date_list[i-4]
    current_revenue = pricetoEarnings[current_date]
    previous_revenue = pricetoEarnings[previous_date]
    if(previous_revenue != 0):
        growth = (current_revenue - previous_revenue)/previous_revenue
        pricetoEarnings_ttm[current_date] = growth

eps_growth = dict()
date_list2 = sorted(eps_data.keys())
for i in range(1, (len(date_list2))):
    current_eps = eps_data[date_list2[i]]
    previous_eps = eps_data[date_list2[i-1]]
    if(previous_eps != 0):
        growth = ((current_eps)/previous_eps)**4
        eps_growth[date_list2[i]] = growth

pe_growth = dict()
for date, peRatio in pricetoEarnings.items():
    try:
        if peRatio is not None and eps_growth[date] is not None and eps_growth[date]!=0:
            pe_growth[date] = peRatio/eps_growth[date]
    except KeyError:
        pass

pe_growth_ttm = dict()
date_list2 = sorted(pe_growth.keys())
for i in range(4, (len(date_list2))):
    current_eps = pe_growth[date_list2[i]]
    previous_eps = pe_growth[date_list2[i-4]]
    if(previous_eps != 0):
        growth = (current_eps)/previous_eps
        pe_growth_ttm[date_list2[i]] = -1*growth

quarterly_returns = dict()
for i in range(0, (len(date_list))):
    if i<(len(date_list)-1):
        current_price = total_prices[date_list[i]]
        future_price = total_prices[date_list[i+1]]
        if(current_price != 0):
            growth = (future_price - current_price)/current_price
            quarterly_returns[date_list[i]] = growth  

yearly_returns = dict()
for i in range(0, (len(date_list))):
    if i<(len(date_list)-4):
        current_price = total_prices[date_list[i]]
        future_price = total_prices[date_list[i+4]]
        if current_price!=0:
            growth = (future_price - current_price)/current_price
            yearly_returns[date_list[i]] = growth
    elif i<(len(date_list)-2):
        current_price = total_prices[date_list[i]]
        future_price = total_prices[date_list[(len(date_list)-1)]]
        if current_price!=0:
            growth = (future_price - current_price)/current_price
            yearly_returns[date_list[i]] = growth

##################################### MERGE ALL METRICS

def find_values_within_range(df, column_name, value_df):
    for index, row in df.iterrows():
        mask = (value_df['Date'] >= row['Start_Period']) & (value_df['Date'] <= row['End_Period'])
        values_within_range = value_df[mask][column_name].values

        if len(values_within_range) > 0:
            df.at[index, column_name] = values_within_range[0]  

df_eps = pd.DataFrame(list(eps_data.items()), columns=['Date', 'EPS'])
df_eps['Date'] = pd.to_datetime(df_eps['Date'])

def create_df_from_dict(data_dict, column_name):
    df = pd.DataFrame(list(data_dict.items()), columns=['Date', column_name])
    df['Date'] = pd.to_datetime(df['Date'])
    return df

df_priceEarnings = create_df_from_dict(pricetoEarnings, 'Price_to_Earnings')
df_priceEarnings_ttm = create_df_from_dict(pricetoEarnings_ttm, 'Price_to_Earnings_TTM')
df_priceBook = create_df_from_dict(pricetoBook, 'Price_to_Book')
df_priceBook_ttm = create_df_from_dict(pricetoBook_ttm, 'Price_to_Book_TTM')
df_evEbitda = create_df_from_dict(evtoEbitda, 'EV_to_EBITDA')
df_evEbitda_ttm = create_df_from_dict(evtoEbitda_ttm, 'EV_to_EBITDA_TTM')
df_revenueGrowth = create_df_from_dict(revenue_growth, 'Revenue_Growth')
df_revenueGrowth_ttm = create_df_from_dict(revenue_growth_ttm, 'Revenue_Growth_TTM')
df_priceEarningsGrowth = create_df_from_dict(pe_growth, 'PE_to_Growth')
df_priceEarningsGrowth_ttm = create_df_from_dict(pe_growth_ttm, 'PE_to_Growth_TTM')
df_roe = create_df_from_dict(roe, 'ROE')
df_quarterlyReturns = create_df_from_dict(quarterly_returns, 'Quarterly_Returns')
df_yearlyReturns = create_df_from_dict(yearly_returns, 'Yearly_Returns')


additional_columns = ['Price_to_Earnings', 'Price_to_Earnings_TTM', 'Price_to_Book', 'Price_to_Book_TTM', 'EV_to_EBITDA', 'EV_to_EBITDA_TTM', 'Revenue_Growth', 'Revenue_Growth_TTM', 'PE_to_Growth', 'PE_to_Growth_TTM', 'ROE','Quarterly_Returns', 'Yearly_Returns']
for col in additional_columns:
    df_eps[col] = np.nan

df_eps['Start_Period'] = df_eps['Date'] - pd.DateOffset(months=1)
df_eps['End_Period'] = df_eps['Date'] + pd.DateOffset(months=1)

dataframes_to_merge = [df_priceEarnings, df_priceEarnings_ttm, df_priceBook, df_priceBook_ttm,
                    df_evEbitda, df_evEbitda_ttm, df_revenueGrowth, df_revenueGrowth_ttm, df_priceEarningsGrowth, df_priceEarningsGrowth_ttm, df_roe, df_quarterlyReturns, df_yearlyReturns]

for df in dataframes_to_merge:
    column_name = df.columns[1]
    find_values_within_range(df_eps, column_name, df)

df_final = df_eps.drop(['Start_Period', 'End_Period'], axis=1).fillna(np.nan)


################################################### OLS REGRESSION FOR COMPOSITE METRIC

def fill_with_average(df, columns):
    for col in columns:
        for i in range(len(df)):
            if pd.isna(df[col].iloc[i]):
                # Find indices of previous and next non-NaN values
                prev_index = df[col].iloc[:i].last_valid_index()
                next_index = df[col].iloc[i+1:].first_valid_index()

                # Check if non-NaN values exist before and after the current NaN
                if prev_index is not None and next_index is not None:
                    prev_val = df[col].iloc[prev_index]
                    next_val = df[col].iloc[next_index]
                    avg_val = (prev_val + next_val) / 2
                    df.at[i, col] = avg_val

    return df

independent_vars = ['EPS','Price_to_Earnings', 'Price_to_Book', 'EV_to_EBITDA', 'Revenue_Growth_TTM', 'PE_to_Growth_TTM','ROE']

dependent_var = 'Yearly_Returns'

df_analysis = fill_with_average(df_final, independent_vars + [dependent_var])
df_analysis = df_analysis.dropna()


X = df_analysis[independent_vars]
y = df_analysis[dependent_var]

if len(X)==0 or len(y)==0:
    dependent_var = 'Quarterly_Returns'
    df_analysis = df_final.dropna(subset=independent_vars + [dependent_var])
    #replace that with filling na's with column averages
    X = df_analysis[independent_vars]
    y = df_analysis[dependent_var]


X = sm.add_constant(X)

model = sm.OLS(y, X)

results = model.fit()

print(results.summary())

final_weights = np.array(results.params)


    

























# %%

##### GARCH, BLACK SCHOLES, AND IMPLIED VOLATILITY

import yfinance as yf
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from arch import arch_model
from datetime import datetime, timedelta
import requests


tag = 'HMY'
tag = tag.upper()
print(f'Analyzing: {tag}')
num_simulations = 100
numWeeks = 10
df = yf.download(tag, '2020-09-01', '2023-12-13')

# GET 252-D MA IV30

url = f'https://marketchameleon.com/Overview/{tag}/IV/'
print(f'Please access the folowing link: {url}')

# EIV = input('Once there, locate the 252-Day HV mean which can be found in the following format: 252 day HV (type this value) mean. Then type this value in: ')

"""
try:
    EIV_numeric = float(EIV)
    expectedIV = EIV_numeric / 100
    print("The expected IV is:", expectedIV)
except ValueError:
    print("Invalid input. Please enter a numeric value.")

"""



np.random.seed(42)
pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)


priceData = df['Close']
volatilityData = df['Volume']
returns = np.diff(priceData) / priceData[:-1]

### GARCH

model = arch_model(returns, vol='Garch', p=1, q=1)
results = model.fit()
print(results)
numDataPoints = len(priceData)

print(results.summary())

volatilityData = np.sqrt(volatilityData)
scale = np.mean(volatilityData)**1.565

volatility = np.sqrt(results.conditional_volatility**2)
plt.figure(figsize=(10, 6))
plt.plot(volatilityData.index, volatilityData, label='Real Volatility')
plt.plot(returns.index, volatility * scale, label='Model Volatility')

forecast_steps = 100
forecasted_volatility = []

current_volatility = results.conditional_volatility.iloc[-1]
mu = np.mean(returns)
omega = results.params['omega']
alpha = results.params['alpha[1]']
beta = results.params['beta[1]']

for _ in range(forecast_steps):
    current_volatility = np.sqrt(omega + alpha * (returns[-1] - mu)**2 + beta * current_volatility**2)
    forecasted_volatility.append(current_volatility)

forecasted_volatility = np.array(forecasted_volatility) * scale
forecasted_dates = pd.date_range(start=returns.index[-1], periods=forecast_steps + 1, freq='B')[1:]

plt.plot(forecasted_dates, forecasted_volatility, label=f'Forecasted Volatility ({forecast_steps} steps)')
plt.title(f'Composite Volatility Model - {tag.upper()}')
plt.xlabel('Date')
plt.ylabel('Scaled Volatility')
plt.legend()
plt.show()


# BLACK SCHOLES (IV)



options_data = yf.Ticker(tag).options
options_prices = {}
for expiration_date in options_data:
    options_chain = yf.Ticker(tag).option_chain(expiration_date)
    call_prices = options_chain.calls
    put_prices = options_chain.puts
    options_prices[expiration_date] = {
        'calls': call_prices,
        'puts': put_prices
    }
option_data_call = []
option_data_put = []
for expiration_date, option_prices in options_prices.items():
    if 'calls' in option_prices and 'puts' in option_prices:
        call_data = option_prices['calls']
        put_data = option_prices['puts']

        call_data['expiration_date'] = expiration_date
        put_data['expiration_date'] = expiration_date

        option_data_call.append(call_data)
        option_data_put.append(put_data)

options_df_call = pd.concat(option_data_call, ignore_index=True)
options_df_put = pd.concat(option_data_put, ignore_index=True)

options_df_call = options_df_call.sort_values(by=['expiration_date', 'strike'])
options_df_put = options_df_put.sort_values(by=['expiration_date', 'strike'])

atmRange = priceData[-1]



def find_closest_friday_one_months_from_now(numWeeks):
    current_date = datetime.now()
    four_months_later = current_date + timedelta(days=(numWeeks*7))
    days_until_friday = (4 - four_months_later.weekday() + 7) % 7
    closest_friday = four_months_later + timedelta(days=days_until_friday)
    return closest_friday

expiration_date = find_closest_friday_one_months_from_now(numWeeks)
expiration_date = str(expiration_date)[0:10]
atmPrice = -1

for strikeP in options_df_call['strike']:
    if (strikeP > (atmRange-2.5)) & (strikeP < (atmRange+10)):
        atmPrice = strikeP
garchForecast = forecasted_volatility[numWeeks*7]/scale
iv = options_df_call.loc[(options_df_call['expiration_date']==expiration_date) & (options_df_call['strike']==atmPrice)]['impliedVolatility']
if iv.size == 0:
    finalVolatility = garchForecast
else:
    lamma = 0.2
    finalVolatility = lamma*garchForecast + (1-lamma)*iv/10


# GEOMETRIC BROWNIAN MOTION

seven_days_ago = datetime.today() - timedelta(days=7)
curPri = yf.download(tag, start=seven_days_ago, end=datetime.today())
currentPrice = curPri['Adj Close'][-1]

num_steps = numWeeks*7  
average_model_prices = np.zeros(num_steps+1)
average_model_prices[0] = currentPrice

def simulate_gbm(S0, r, sigma_combined, T, num_simulations, num_steps):
    dt = T / num_steps
    stock_prices = np.zeros((num_simulations, num_steps + 1))
    stock_prices[:, 0] = S0

    for i in range(1, num_steps + 1):
        Z = np.random.standard_normal(num_simulations)
        count = 0
        for j in range(num_simulations):
            stock_prices[j, i] = stock_prices[j, i - 1] * np.exp((r - 0.5 * sigma_combined**2) * dt + sigma_combined * np.sqrt(dt) * Z[j])
            count+=stock_prices[j, i]
        count = count/num_simulations
        average_model_prices[i]=(count)
    return stock_prices

def plot_simulation(stock_prices, T):
    num_simulations, num_steps = stock_prices.shape
    time_steps  = []

    for i in range(num_steps):
        time_steps.append(i)
    
    plt.figure(figsize=(10, 6))
    for i in range(num_simulations):
        plt.plot(time_steps, stock_prices[i, :], lw=1, alpha=0.6)
    plt.plot(time_steps, average_model_prices, label='Average Price Forecast')
    plt.title(f'Simulation of {tag} Prices')
    plt.xlabel('Number of Days')
    plt.ylabel(f'{tag} Price (USD)')
    plt.legend()
    plt.show()



mu = np.diff(priceData) / priceData[:-1]
drift = np.mean(mu)



S0_value = currentPrice 

sigma_combined = finalVolatility  
r = drift
T = 1.0     

S0 = np.full((num_simulations,), S0_value)


simulated_stock_prices = simulate_gbm(S0, r, sigma_combined, T, num_simulations, num_steps)
plot_simulation(simulated_stock_prices, T)

time_steps  = []

for i in range(num_steps+1):
    time_steps.append(i)
plt.plot(time_steps, average_model_prices, label = 'Average Predicted Price')
plt.xlabel('Number of Days')
plt.ylabel(f'{tag} Price (USD)')
plt.title('Average Model Price Prediction')
plt.show()




    # %%




# %%


#################################### Filter Stocks



import yfinance as yf
import numpy as np
import matplotlib.pyplot as plt
import requests
import pandas as pd
import re
import json


pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)


def filter_values(ticker):
        try:
            tickerData = yf.Ticker(ticker)
            data = tickerData.info
            dataEbitda = 1/data['enterpriseToEbitda']
            dataRoe = data['returnOnEquity']
            revG = data['revenueGrowth']
            if((not np.isnan(dataEbitda)) and (not np.isnan(dataRoe)) and (not np.isnan(revG))):
                if dataRoe>0 and dataEbitda>0: 
                    return dataRoe, dataEbitda, revG
                
            return np.nan, np.nan, np.nan
            

        except Exception as e:
            print(f'Insufficient data on {ticker}')
            return np.nan, np.nan, np.nan

df_stonks = pd.read_csv('StockList.csv')
finalTickers = dict()
sectors = ['Basic Materials','Consumer Discretionary','Consumer Staples','Energy','Finance','Health Care','Industrials','Miscellaneous','Real Estate','Technology','Telecommunications','Utilities']
for sector in sectors:
    print(f'Working on the {sector} sector')
    df_sector = df_stonks.loc[df_stonks['Sector']==sector]
    stock_tickers = df_sector['Symbol']
    roes = dict()
    evebits = dict()
    revGs = dict()
    for ticker in stock_tickers:
        print(f'Analyzing: {ticker}')
        roe, evebit, revG = filter_values(ticker)
        print(f'{ticker}: {roe} {evebit} {revG}')
        if not np.isnan(roe):
            roes[ticker] = roe
        if not np.isnan(evebit):
            evebits[ticker] = evebit
        if not np.isnan(revG):
            revGs[ticker] = revG



    


    mean_roe = np.mean(list(roes.values()))
    std_roe = np.std(list(roes.values()))
    mean_evebits = np.mean(list(evebits.values()))
    std_evebits = np.std(list(evebits.values()))
    mean_rev = np.mean(list(revGs.values()))
    std_rev = np.std(list(revGs.values()))

    roe_mult = mean_evebits/mean_roe
    rev_mult = mean_evebits/mean_rev
    


    file_path = 'StockList_Filtered.csv'
    val_score = dict()

    for stock, roe in roes.items():
        val_score[stock] = roe*roe_mult + evebits[stock] + revGs[stock]*rev_mult

    mean_score = np.mean(list(val_score.values()))
    std_score = np.std(list(val_score.values()))

    for stock, roe in roes.items():
        if val_score[stock]>(mean_score+std_score):
            df_filtered = df_stonks[df_stonks['Symbol'] == stock]
            sec = df_filtered['Sector'].iloc[0]

            finalTickers[stock] = sec

            print(f'{stock} passed')

        else:
            print(f'{stock} failed')

finalTickers




# %%
