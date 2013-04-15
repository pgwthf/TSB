'''
DjangoEurope:
* test  cron-runnable scripts for updates
* Get production server running (flup??)

clean up utils_python & make separate package

check cython or shedskin for (channel) indicators (how to deal with different os'es?)
	make automated profiler to see if this makes sense.
	Indicators are the most obvious choice, but maybe also the datedlist?

stockmanager needs -v cmd line option

Trading System Builder is an integrated package that allows:
	* defining trading systems
	* backtesting trading systems on historical data
	* real-time running (paper trading) of trading systems
	* managing (discretionary) portfolios
	* selecting and filtering stocks
	* charting
All of the above can be either stand-alone or online, where stand-alone is more
appropriate for backtesting and online for real-time running.
Instead of paper trades, the user can take real trades, but currently no
interface is planned for that.

Components:
	* stockmanager:
		package that maintains stocks, markets, prices, indices, currencies
	* poolmanager
	* trademanager
	* equitymanager


BUGS:
* calculating takes too long: check if channel is taken from DB
* edit_metasystem: markettype = 0 (wrong), but with /force : mt = any (right)
* backtest on short timeperiod fails (e.g. 1 year)
* email van site werkt niet meer
* there are still memory leaks: 30% after a bit of browsing, 15% after backtest
* in all parameters.params_*: in description: if self.repr('x') must take the
	list / all case into account for CHOICES

DONE 1) import pool
DONE 2) show ranks in pool
3) use:
	+ develop position sizing idea
	+ show daily increment in % and $
	+ rank by channel length-independent quality & width
4) migrate to DjangoEurope
5) trade

6) further develop, start with new data manager
* from eoddata.com:
	* daily (amex) prices - manual d/l
	* daily (amex) prices - auto ftp d/l
	* 20y historical (amex) prices - manual d/l
	* daily(?) symbol changes (file format?)
	* daily(?) splits (file format?)
	* symbol lists (to get names)

7) simultaneous with 6), new data formats - save space & time
DB size:
* replace decimal with integer (4 byte int of postgresql) uses 30% of the space
* use postgresql date type (4 bytes), not time(stamp) (8 bytes)
* use 8 byte integer for volume (index may have high vol)

8) turn channel into a std indicator: speed up using C?

DISCRETIONARY:
* see pool with indicators and click to see stock
* take trade inside stock view (enter + vol, or exit)
* see mkt cond
* (edit?)
* calc performance / equity
* suggest trade size



PRIORITIES:

DONE 1	Test Ratchetps ax | grep 
DONE 2	Exit on mkt type change
DONE 3	Run backtests as separate processes

4	Check channel calculation algorithm

5	Run real time (portfolio, signals, mkt type)

6	Install entire system on Macbook (use for backtesting)

7	Migrate to Django Europe

8	Buy data source(s) (S&P, nasdaq, ...?)


SYSTEM DEVELOPMENT:
1)	take good Long channel system
2)	apply number of mkt types with different params
		* 2) can be traded now
3)	find short system that works well in flat periods of 2)
4)	test with mkt type
5) 	combine


SYSTEM:
* alloc? 20% to start with?
* mkt type ? (1y ma?)
* UP mkt: Long 1y highest channel quality
* DN mkt: Short 6w highest channel quality


QUESTION:
* should lookback be dynamic? if so: what determines lookback? time since last
	big mkt turn (=extreme)?
* FOR market type PATTERN is more important than ABSOLUTE TIME, e.g. 1y lookback


GENERAL:
	* Test entries using sell next day at o/c exit (for short term systems)
	* maybe HOME should be: metasystem groups + system bookmarks
	* do we need a stand-alone show_markettype?
	* pages for markettype, pool and stock should take system_id as input for
		showing indicators etc.
	* implement market types: from TODO list
		- sumangle, (sumqual)
		- n_channels > 0
		- mkt type based on order of channel angles <> 0
	* maak weekend check routine for past week
	* implement entry: angle 21 > angle 252
	* chart with all angles (widths?)
	* try AAPL enter on start of green, exit at end of green
	* calc mkt cond by % of pos angles for each LB (pool function?)
	* consider adjusting t/b channel line AGAINST the direction of the trend


TODO :

metasystem/parameters:
	* update all other param_rank methods for get_table


show_metasystems:
	* put "new metasystem" somewhere else
	* implement view settings (save state in redis or http) (example: show_systems)
	* implement speed in Maxresults column


show_metasystem:
	* allow changing of markettype if ANY
	* in header: prev/next metasystem
	* implement view settings (save state in redis or http)
	* is_discretionary only works on 1 system (LONG) - how about SHORT?
	* implement (from show_systems):
		bookmark selected (select bookmark)
		filter (on separate tab?)
	* show_systems used to have export_systems - is this still necessary??


show_system (includes edit_system)
	* in header prev/next system
	* test bookmarks (and put link in header)
	* also show  (open trades) in portfolio tab for non-discr systems? 
	* is there anything to copy?
	metasys structure with sys values
		if ms.has_one_method: copy method to new ms
	markettype(system_id)
		editable if metasys has discr entry/exit
	equity chart
		calculate if system.is_discretionary
	performance list
		calculate if system.is_discretionary


show_pool, show_system_pool
	* finish


show_trade:
	* display exit data (price, n_days, S/L, rule, ...)

edit_metasystem:
	* check if errors works / does anything
	* show the correct tab names (UP QUIET, etc) - THIS IS HARD!!




TODO :
* move show trade from chart to signaldinges
* in show_trade exit tab: show trade performance (% of eq, etc)
* implement link to group in show metasystem (show systems)
* implement filter to remove identical systems? - or to prevent calculating identical systems
* show_trades express p/l as % of equity
	- in trades table: show % profit & % of equity profit
* use separate process for calcs
* use description (sentence) in edit_metasystem for alloc & eq model
	- do together with re-selecting method if not readonly 
	- improve rendering of mjultiwidget (ParamWidget)
	- put get_parameters into ParamFormField
* translate standard_rules to std_rules everywhere

CONSIDER :
* merge show_systems with show_metasystem

pricemanager:
* is all the dates manipulation still necessary?
* use price data from AU site
* weekly d/l on Sunday
* warning for incomplete price data - in stock
* must find better price data source!!!!!!!
* NOTE: prevent all channel dramas by real time calculation!!!!!!!!!!!!!!

css:
* rename
* make classes, id's 
* make UL/LI work (in show_pool)
* make h1 work

show_pools:
* Manage tab with:
	- d/l all pools
	- check all pools
* document pool & how dates are used

show_pool just pool:
* manage: 
	- check: index range must be at least pool range
	- dl missing of all stocks separately & channels
	- must also be possible to run straight from URL (for cron job)

show_pool: channel version (from metasystem):
	- show stop loss for type of entry (e.g. @limit = high)
	- list tomorrows top X for given indicator (within pool)
	- highlight good values for width, stop_loss
	- default date is today, implement setting alternative date
	- implement show thumbnail of stock?

edit_pool:
* consider: integrate with show_pool, maybe need "new pool"?
* lock pool editing once used by a metasystem
* redo edit_pool (use self.instance.<pool> (as in MetaSystemForm())
	.remove pool from table in edit_pool


Weekly Cron run:
A - for each pool:
1) d/l all index prices for past week
2) compare d/l prices & dates with database
3) update missing/different
4) email notification of all changes and existing prices that were not in new dl
5) calc channels
B - for each stock in pool:
1) d/l all prices for past week
2) compare d/l prices & dates with database
3) update missing/different
4) email notification of all changes and existing prices that were not in new dl
4) check for splits in past week & notify if necessary
5) calc channels

Manual run (for new pool or after Fubar):
A - Index:
1) d/l all index prices for pool date range (up to today)
2) compare d/l prices & dates with database
3) update missing/different
4) show notification of all changes and existing prices that were not in new dl
5) calc index channels
B - for each stock in Pool (same functions as in stock_view):
1) d/l all index prices for pool date range (up to today)
2) compare d/l prices & dates with database
3) update missing/different
4) show notification of all changes and existing prices that were not in new dl
5) check for splits - need notification
6) calc index channels
MUST BE POSSIBLE IN stock_view TO FORCE D/L, UPD

/pool/cron/weekly_check

Need
market_closed list (per market), where market = stock property, curr = mkt prop
market_closed is list of all weekdays the market was closed - exists only for 
	indices (markets)
ignore date list (per stock)
ignore split list (per stock) - OR: split list ??

stock -> market !
pool -> index -> market !
market: currency, index, etc?

e.g. NYSE: what is index? US market? NASDAQ?

integrate with mkt conditions?

* automatic backup of system databases (not prices! - too much data)



BUG:
* sometimes date in ViewStock is 31/12/12
* reverse split may have occured for msg after price d/l
* link to show_stock in pool must use lookback
* in params_entry.daily self.at MAY not be available
* in show_stock: channel angle/width/bottom is entry value only (also on exit page)


TODO channel test:
* implement entries/exits that use channel parameter from method ranking
* make params editable after selection
* implement exit at top channel line
* implement other exits (see Note)
* implement entry 252 up AND 21 up
* consider which lookback to use (from exit/stop/rank) in stops/edit_system/..
* need shorter names for methods & params in metasystem.parameters.params_*
* clean up repr mess
* in metasystem.run_all: use % as progress tracker (not sys/hr)


ALLOCATION:
* MS = structure, S = values & performance results: SO: in addition to rnd &
	fixed, there must be other variable selections that will cause the variable
	value to be recorded in system.params

AAA: document parameters + parameters.update()??
AAB: npos - np (exit)
AAC: nd->lb,
AAD: force_exit
AAF: replace action with session in views



Show profolio:
in all tables: do deleting etc through session variables (to prevent issues with
	sorting)

TODO discretionary systems:
* edit_system -> show positions
	- make link to this page somewhere (sys 626832)
	- show thumbnail?
	- need to select method L/S
	- column with current position risk and total equity/sl risk
	- may be discretionary or may belong to a system
	- tab with portfolio performance stats
	- calculate performance & update
* Need a special metasystem, system for discretionary trading (portfolios)
	- ranking -> show pool, stops -> show pool / default exit
	- equity_model + allocation + startcash -> pos size
	* show_portfolio (enter, exit trades, calc/view performance, show trades,..)
	* use ranking from metasystem def.
	* use exits for showing stop_losses
	* use pos_sizing - link show_pool to system (for s/l, pos, etc)

BIG SIMPLIFICATION:
	translate channel calculation into C and if fast enough replace Channels db


MetaSystems:
* allow modification of alloc, methodselector, equitymodel (e.g. after copy)
* implement groups of MS's that have the same Pool, startdate and enddate, so
	that they can be run together, while only loading the prices (and channels)
	once

TODO market conditions:
* Implement market conditions as per Trevor's email

BUGS:
* memory leak in show_pool !?

TODO development general
* in all DT2 tables with dates: date = tables.DateColumn(format='Y/m/d')
* on channel display page (show_stock) chart with only price and channels on
	enddate (all of them, or select: 225, 126, ...)
* separate SQ from system
* document workflows (make pool d/l, make metasys, etc)
* trawl through code for TODO's
* new show_pool with position size, risk, etc (needs to know capital, Portf Risk, etc)
* Logical gui workflow for channel systems / trading / portfolios
* fibonacci profit taking
* optionally use different equity model: cash + sum(stop*volume)

TODO short term:

* show_stock
	- implement indicators, etc

* stock charts:
	* make ui with dropdowns for indicators
	* visualise past and current trades
		- click on a stock to see its chart - with indicators (dynamic views)
		- set watchlist (or portfolio with entrydate/price, or trades list)
		- generate portfolio & trades (save portf as open trade) - this is 
			equivalent to r/t system
	* when r-t trading works: show signals

* Implement real-time running of systems:
	- daily signals
	- backtest systems - extend backtest for rt syst
	- turn system into realtime by changing enddate & adding name?
	- use copy system to metasystem to make real-time sys?
	-  Generate systems by selecting metasystem + fixed values + run backtest


TODO medium term:
* replace today() with stock.latest_price (for index?)
* make sure exit_sl is ALWAYS the first exit
* are multiple dates in StockPrice object unneccessarily slow? use 1 dates list
	at prices level.
* show_metasystems: 
	- when in group go back to group after copy/del, etc
	- click on name to go to results
* add to show_system view: show results per mkt condition
* turn trades per year (tpa) into decimal
* layout of documentation


think about:
* split performance by market condition
* how to do 5dd with exit - continuation univ.entry or fail short
* how to do entry/exit based on any combo of indicators
* how to do multiple positions per stock
* how to test entries/exits (or any rule)?
* how to test indicators? draw chart?
* how to enter and exit on the same ma period??
* way to easily try combinations of L and S methods


GUI:

* show_bookmarks:
	* implement view parameters (tab)
	* link to metasys should go to show_systems (same for click on name in show_ms)

* show systems:
	- make (delete) filters (e.g. -1 < SQN < 1)
	- make human readable allocation column (rule: par)
	- make human readable base system column (link to base system)
	- indicate if trades/equity exists, delete/generate tr/eq
	- shows scrollbar even if it would fit on the screen: needs a min height?
	- header width if no scrollbar
	- hor scrollbar?

* show_system:
#	- display parameters individually instead of dict
	- format alloc sys table (no checkbox), fix link to systems
	- save id's to redis in view (allocate now)
* quick links in show_system:
	- run same system over new time period
	- start/stop calc
	- generate/run single system from show_metasystem
		+ make system (set parameters) & run (return id)
	- allocate from 'allocate now' link in show_system does not work

* show_metasystem:
#	- manually enter a system & run it
	- correct (un)allocated

* edit_metasystem:
	- use tabs for easier navigation
	- show previous value after fixed->variable v.v.
	- allow resetting methodselectors, (also ranks?)
	- implement (saving) conditions

* show metasystems:
	- hide/delete metasystems
	- (test) run without redis for checking for runtime errors (admin only?)

* show_stock_chart:
	- form with dropdown boxes
	- make market conditions more generic


CONSIDER system/indicator/trade ideas:
* X days down where X is a function of the ROC (or some other indicator)
* trend following vs. take high probability trades
* fibonacci pullback entry, exit, mkt condition
* is there a correlation between closeness to trendline, profit over next x days
* compare stocks (short term) performance with its index
* define new version of SQN with separate std_dev for wins & losses
* non-time based ROC, e.g. number of bars of x ATR
* triangle detector at different scales
* drawdown recovery rate: %max_dd / n_days_to_next_high
* replace VT R with avg neg trade * its probability

CONSIDER usability improvements:
* implement (generic) filters with drop-downs (n>=6pa, |sqn|>1, |exp/d|>0.1, 
	|exp|>0.5)
* in method: make n_pos var/fixed
* lowest allowed rank must be > n_pos
* fill vertical gaps in equity thumbnail (on tn generation)
* Indicate with colours if pi, MAn/MAx are in buying range
* Implement exclude in get_rule_choices
* validation errors at right fields (multivaluefield)
* put limits on all FORMfields that are not in ParamField
* improve colours on equity thumbnail

CONSIDER performance/efficiency improvements:
*** cheaper way to do MA is to add last, subtract x ago and use cache
* use raw sql to speed up slow tasks
* use cache on prices and indicators (ma, roc, ...)
* Don't save equity, because it can be generated from Trades/Prices/Allocation
* Use model manager to (batch) delete equity/trades to save database space
* Is defaultdict(list) a useful replacement for some of my dicts?
* DT2 can calculate performance on the fly to save DB space, sort by non-db fld
* Profiling run_random: (previously 30% is spent in datedlist.index)
* use only single date list for StockPrices class (instead of DatedList
* Port datedlist to C
* indicator calculations: skip first 250 (or start on startdate)

Development roadmap, Version x.y
* external libraries: datedlist, indicators, random_parameters(?)
* use git, pip
* migrate to github
* Clean up code - separate modules?
* migrate to dotcloud, PaaS, somethingelse.com, how does that work with:
	+ consider IB data interface
	+ Go back to Celery - use multiple processors

* Use Django-CMS
* Subscribe users to systems - Users can then select which one they want to
	have active
* Add users site, show signals/trade history
* Add dashboard, view performance/indicators/charts for selected pool (table)
	or stocks
* Add commercial site
'''