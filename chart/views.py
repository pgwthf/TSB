'''
chart/view.py v0.1 120711

Created on 120601

@author: edwin
'''
from __future__ import division
from __future__ import absolute_import

import datetime

from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.shortcuts import render
import Image, ImageDraw
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas

from pyutillib.date_utils import last_year, datestr2date, date2datestr, \
        next_weekday
from equity.models import Thumbnail, EquityHistory
from tradesignal.models import Trade
from system.models import System

from chart.forms import StoplossForm

from pricemanager.models import Stock

#from metasystem.models import MetaSystem


def make_line(canvas, width, y, colour):
    '''
    Draw a horizontal axis in <colour>.
    '''
    canvas.line([(0,y),(width-1,y)], width=1, fill='grey')


def draw_thumbnail(request, system_id):
    '''
    Return thumbnail image of the equity chart of this result.

    The image is retrieved from the Thumbnail table.
    '''
    linecolour = 'darkred'
    if Trade.objects.filter(system_id=system_id).count():
        linecolour = 'darkgreen'
    (width, height, y0, y1tuple, y2tuple, data) = Thumbnail.read(system_id)
    image = Image.new("RGB", (width, height))
    canvas = ImageDraw.Draw(image)
    canvas.rectangle([(0,0), (width, height)], fill='white')
    # draw origin
    make_line(canvas, width, y0, 'grey')
    if y1tuple[1]:
        make_line(canvas, width, y1tuple[0], 'darkred')
    if y2tuple[1]:
        make_line(canvas, width, y1tuple[0], 'lightgrey')
    # draw chart
    for x, (y0, y1) in enumerate(data):
        canvas.line([(x,y0),(x,y0+y1)], width=1, fill=linecolour)
    # add system id
    y_text = 1 if y0 > height/2 else y0 + 1
    canvas.text((1,y_text), str(system_id), fill='black')
    # return image
    response = HttpResponse(mimetype="image/png")
    image.save(response, "PNG")
    return response


def draw_equity_chart(request, system_id):
    '''
    Return full size chart of the equity curve of this result.
    '''
    system = System.objects.get(id=system_id)
    metasystem = system.metasystem
    metasystem.make_system(system.params)

    equity = EquityHistory(system_id=system_id)
    if not equity.exists():
        return None
    total = equity.percentage()

    index = metasystem.pool.index
    index.date_range = (total.dates[0], total.dates[-1])

    markettype = metasystem.markettype
    chart = index.chart(title='equity', style='market_type', size=(1024, 480), 
            markettype=markettype)
    chart.add_secondary(total, colour='blue')
    return chart.plot()


def custom_stock_chart(request, symbol, startdate_str=None, enddate_str=None):
    '''
TODO: MAKE GENERIC
    '''
    stock = Stock.objects.get(name=symbol)
    if startdate_str:
        startdate = datestr2date(startdate_str)
    if enddate_str:
        enddate = datestr2date(enddate_str)
    stock.date_range = (startdate, enddate)
    chart = stock.chart(style='line', size=(1600,960)) #format for printing

    colours = ('green', 'orange', 'red', 'magenta', 'purple', 'blue')

#   chart.add_indicator('sumangle', {}, data='channel', colour='blue')

    from pricemanager.models import Pool
    pool = Pool.objects.get(name='S&P500')
    pool.index.global_date_range = (pool.startdate, datetime.date.today())

    chart.new_area(1)
    for lookback, colour in zip(Channel.LOOKBACKS, colours):
        if lookback == Channel.YEAR:
            chart.add_indicator('pool_market', {'pool': pool, 'lookback': lookback}, data='channel', colour=colour)
#        if lookback == Channel.TWOMONTHS:
#            break
#   chart.add_indicator('pool_market', {'pool': pool, 'lookback': Channel.MONTH}, data='channel', colour='blue')

#    chart.new_area(1)
#    for lookback, colour in zip(Channel.LOOKBACKS, colours):
#        chart.add_indicator('angle', {'lookback': lookback}, data='channel', 
#                colour=colour, scale=lookback/100)

#    chart.new_area(1)
#    chart.add_indicator('sumwidth', {}, data='channel', colour='blue')
#
#    chart.new_area(1)
#    for lookback, colour in zip(Channel.LOOKBACKS, colours):
#        chart.add_indicator('width', {'lookback': lookback}, data='channel', 
#                colour=colour, scale=10/lookback**0.5)
    return chart.plot()


def draw_stock_chart(request, symbol, startdate_str=None, enddate_str=None, 
        lookback=None):
    '''
    input: stock, date range, chart format
        generate chart object
    set all subcharts
    generate plot
        calc all data
        check date range - adjust if not all data available
    '''
    stock = Stock.objects.get(name=symbol)
    if startdate_str:
        startdate = datestr2date(startdate_str)
    if enddate_str:
        enddate = datestr2date(enddate_str)
    if lookback and int(lookback) in Channel.LOOKBACKS:
        lookback = int(lookback)
    else:
        lookback = request.session.get('channel_lookback_period')
        if not lookback:
            lookback = Channel.YEAR

    stock.date_range = (startdate, enddate)
    chart = stock.chart(style='candle', size=(1024,600))

    chart.draw_current_channel(lookback, startdate, enddate)
    chart.draw_channel_history(lookback)
    chart.draw_channel_parameters(lookback)
    chart.draw_channel_indicator(lookback)
    return chart.plot()


def draw_trade_chart(request, trade_id):
    '''
    Generate a plot of a stock chart with the trade <trade_id> on it as a line.
    The trade may be open (a position) or closed.
    '''
    trade = Trade.objects.get(id=trade_id)
#TODO: gcl = obsolete
    lookback = trade.method.rank.get_channel_lookback(trade=trade)
    if not lookback:
        lookback = Channel.YEAR

    latest_date = trade.stock.get_latest_date()
    stoplossdate = next_weekday(latest_date)
    exitdate = trade.date_exit if trade.rule_exit else latest_date
    trade_length = (exitdate - trade.date_entry).days

    # show at least 30 days of the chart before entry
    daysbefore = max(30, trade_length // 10)
    startdate = trade.date_entry - datetime.timedelta(days=daysbefore)
    # adjust the startdate i

    if trade.rule_exit: # This is a closed trade
        # show up to 6 months of the chart after exit
        daysafter = max(30, trade_length // 2)
        enddate = trade.date_exit + datetime.timedelta(days=daysafter)
        exitprice = float(trade.price_exit)
    else: # this is an open trade (portfolio position)
        enddate = trade.stock.get_latest_date()
        exitprice = trade.stock.price.close[exitdate]
        if trade.date_exit: # check if the date for custom stoploss is earlier
            startdate = min(startdate, trade.date_exit)

    trade.stock.date_range = (startdate, enddate)
    chart = trade.stock.chart(style='candle', size=(1024,600))
    chart.add_trade((trade.date_entry, exitdate), 
            (float(trade.price_entry), exitprice), colour='black')

    if not trade.rule_exit:
        if trade.price_exit and trade.date_exit:
            # This is a position with a custom stoploss
            stoploss = trade.stoploss()
            stoploss_startdate = trade.date_exit
            stoploss_startprice = trade.stock.price.low[stoploss_startdate]
        else:
            # This is a position with the default stoploss
            stoploss = trade.stock.price.channel.stoploss(lookback=lookback, 
                    date=stoplossdate, date_entry=trade.date_entry)
            stoploss_startdate = trade.stock.price.close.get_date(
                    trade.date_entry, -1)
            stoploss_startprice = trade.stock.price.channel.bottom(lookback)[
                    stoploss_startdate]
        chart.add_trade((stoploss_startdate, latest_date + datetime.timedelta(
                days=1)), (stoploss_startprice, stoploss), colour='orange')

    chart.draw_channel_history(lookback)
    chart.draw_channel_parameters(lookback)
    chart.draw_channel_indicator(lookback)
    return chart.plot()


def draw_market_chart(request, system_id, startdate_str=None, enddate_str=None):
    '''
    Return a png plot with the pool index coloured by market condition.
    '''
    system = System.objects.get(id=system_id)
    metasystem = system.metasystem
    metasystem.make_system(system.params)

    if startdate_str:
        startdate = datestr2date(startdate_str)
    else:
        startdate = metasystem.startdate
    if enddate_str:
        enddate = datestr2date(enddate_str)
    else:
        enddate = metasystem.enddate

    index = metasystem.pool.index
    index.date_range = (startdate, enddate)

    markettype = metasystem.markettype
    chart = index.chart(style='market_type', size=(1024, 480), 
            markettype=markettype)
    return chart.plot()



from channel.models import Channel

def show_trade(request, trade_id):
    '''
    Show 2 states of a trade: day before entry and entry + exit (or open trade)
    '''
    trade = Trade.objects.get(id=trade_id)
#TODO: gcl = obsolete
    lookback = trade.method.rank.get_channel_lookback(trade=trade)
    if not lookback:
        lookback = Channel.YEAR

    if trade.rule_exit is not None:
        enddate = trade.date_exit
    else:
        enddate = datetime.date.today()
    trade.stock.date_range = (last_year(trade.date_entry), enddate)

    if trade.rule_exit is None:
        if request.method == 'POST':
            stoplossform = StoplossForm(request.POST)
            if stoplossform.is_valid():
                trade.date_exit = stoplossform.cleaned_data['startdate']
                angle = stoplossform.cleaned_data['angle']
                if angle is not None:
                    angle = int(angle)
                trade.price_exit = angle
                trade.save()
        stoplossform = StoplossForm(data={'angle': trade.price_exit, 
                'startdate': trade.date_exit })
        stoplossdate = next_weekday(trade.stock.get_latest_date())
    else:
        stoplossform = stoplossdate = stoploss = None

    entrychart = reverse('show_stock_chart_from_to_lookback', kwargs={
            'symbol': trade.stock.name, 
            'startdate_str': date2datestr(trade.date_entry - 
                datetime.timedelta(days=365)), 
            'enddate_str': date2datestr(trade.date_entry - 
                datetime.timedelta(days=1)),
            'lookback': lookback})
    exitchart = reverse('draw_trade_chart', kwargs={'trade_id': trade_id})

    if not trade.rule_exit:
        if trade.price_exit and trade.date_exit:
            # This is an open trade (portfolio position) with a custom stoploss
            stoploss = trade.stoploss()
        else:
            # This is an open trade (portfolio position) with default stoploss
            stoploss = trade.stock.price.channel.stoploss(lookback=lookback, 
                    date=stoplossdate, date_entry=trade.date_entry)

    # previous, next trade links:
    trades = trade.system.trade_set.order_by('date_entry')
    trade_id = int(trade_id)
    prev_id = prev_trade = next_trade = None
    for tr in trades:
        if prev_id == trade_id:
            next_trade = reverse('show_trade', kwargs={'trade_id': tr.id})
        if tr.id == trade_id and prev_id is not None:
            prev_trade = reverse('show_trade', kwargs={'trade_id': prev_id})
        prev_id = tr.id

    return render(request, 'show_trade.html',{
            'trade': trade,
            'entrychart': entrychart,
            'exitchart': exitchart,
            'entry_data': trade.stock.data_summary(
                trade.stock.price.close.get_date(
                trade.date_entry, -1), lookback),
            'exit_data': trade.stock.data_summary(enddate, lookback),
            'prev_trade': prev_trade,
            'next_trade': next_trade,
            'stoplossdate': stoplossdate,
            'stoploss': stoploss,
            'stoplossform': stoplossform})
