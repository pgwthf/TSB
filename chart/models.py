'''
chart/models.py v0.1 121206

Created on 121008

@author: edwin
'''
from __future__ import division
from __future__ import absolute_import

import matplotlib as mpl
mpl.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
from matplotlib.ticker import MultipleLocator
from matplotlib.dates import MonthLocator, YearLocator, WeekdayLocator, \
        DateFormatter
from matplotlib.patches import Rectangle
from matplotlib.dates import date2num

from django.http import HttpResponse
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas

#from utils_python.utils import str2dict
#from TSB.utils import init_redis


class Chart(object):
    '''
    Chart plotting class that must be used inside a stock instance. This is
    only intended for generating png images.

    Charts can have multiple areas, there is always a primary area that 
    contains at least a price plot. In addition to that there may be multiple
    areas for displaying indicators or volume.
    Each area may contain multiple indicators, e.g. the volume + its moving avg
    The primary area may have a secondary dataset which can be synchronised on
    the first date. This may be used to show the index.

TODO: document self.areas
    '''
    lock = 0
    lock_queue = 0

    def __init__(self, stock, title=None, style='candle', height=1, log=True, 
                legend=True, size=(1024, 768), colour=None, **kwargs):
        '''
        Define the primary plot area
        '''
        self.lock_queue = Chart.lock_queue
        Chart.lock_queue += 1
        if self.lock_queue:
            while Chart.lock != self.lock_queue:
                pass  # prevents multiple plots affecting each other
        self.stock = stock
        self.dates = stock.price.close.get_dates(*stock.date_range)
        self.title = stock.name if title is None else title
        self.style = style
        self.kwargs = kwargs
#        if style == 'market_type':
#            self.trend = kwargs.get('trend')
#            self.volatility = kwargs.get('volatility')
        self.colour = 'black' if colour is None else colour
        self.size = size
        self.areas = [{'height': height, 'log': log, 'dataset': []}]


    def add_secondary(self, price, colour=None):
        '''
        Add a secondary dataset to the primary plot
        '''
        self.areas[0]['secondary'] = {'price': price, 'colour': colour}


    def new_area(self, height=0.5, log=False):
        '''
        Add a plot area to the chart.
        '''
        self.areas.append({'height': height, 'log': log, 'dataset': []})


    def add_indicator(self, indicator, parameters=None, data=None, 
            colour=None, scale=None):
        '''
        Add an indicator to the current area 
        '''
        self.areas[-1]['dataset'].append({'indicator': indicator, 
                'parameters': parameters, 'data': data, 'colour': colour,
                'scale': scale})


    def add_trade(self, dates, prices, colour=None):
        '''
        Add an trade to the current area 
        '''
        self.areas[-1]['dataset'].append({'trade': True, 'dates': dates,
                'prices': prices, 'colour': colour})


    def draw_current_channel(self, lookback, startdate, enddate):
        '''
        Add top and bottom channel line to the current area
        '''
        b = self.stock.price.channel.bottom(lookback)[enddate]
        t = self.stock.price.channel.top(lookback)[enddate]
        a = self.stock.price.channel.angle(lookback)[enddate]
        n = self.stock.price.close.delta(startdate, enddate)
        self.add_trade(dates=(startdate, 
                self.stock.price.close.latest_date_before(enddate)), 
                prices=(b*(1/(1+0.01*a))**(n/252), b), colour='pink')
        self.add_trade(dates=(startdate, 
                self.stock.price.close.latest_date_before(enddate)), 
                prices=(t*(1/(1+0.01*a))**(n/252), t), colour='lightgreen')


    def draw_channel_history(self, lookback):
        '''
        Add channel history to the current area
        '''
        self.add_indicator('top', {'lookback': lookback}, data='channel', 
                colour='green')
        self.add_indicator('bottom', {'lookback': lookback}, data='channel', 
                colour='red')


    def draw_channel_parameters(self, lookback, height=0.33):
        '''
        Make a new area and plot the channel angle and width.
        '''
        self.new_area(height=height)
        self.add_indicator('angle', {'lookback': lookback}, data='channel', 
                colour='orange')
        self.add_indicator('width', {'lookback': lookback}, data='channel', 
                colour='blue')


    def draw_channel_indicator(self, lookback, height=0.33):
        '''
        Make a new area and plot the channel indicator in it.
        '''
        self.new_area(height=height)
        self.add_indicator('rc', {'lookback': lookback}, data='channel', 
                            colour='purple')


    def plot(self):
        '''
        Return a png chart plot
        '''
        plot = Plot(self.size, secondary=('secondary' in self.areas[0]))
        axes = []
        primary_axis = None
        heights = [a['height'] for a in self.areas]
        for area in self.areas:
            axes.append(plot.add_axis(heights, primary_axis, area['log']))

            if axes[0] == axes[-1]:
                # this is the primary plot
                primary_axis = axes[0]
                plot.primary(self.style, axes[0], self.stock.price, 
                        dates=self.dates, colour=self.colour, **self.kwargs)
                primary = True

            if area.get('secondary', None):
                # this is a secondary plot
                plot.secondary(axes[0], area['secondary']['price'], 
                        colour=area['secondary']['colour'])

            legend_ax = []
            legend_txt = []
            for dataset in area['dataset']:
                if 'trade'in dataset:
                    plot.plot_trade(axes[-1], dataset['dates'], 
                            dataset['prices'], dataset['colour'])
                    continue
                if dataset['data'] is None:
                    price = self.stock.price
                else:
                    price = getattr(self.stock.price, dataset['data'])
                data = getattr(price, dataset['indicator'])(
                         **dataset['parameters'])[slice(*self.stock.date_range)]
                if dataset['scale'] is not None:
                    data = [d*dataset['scale'] for d in data ]
                ax, = plot.line(axes[-1], data, colour=dataset['colour'])
                legend_ax.append(ax)
                legend_txt.append('{}({})'.format(dataset['indicator'], ','.
                        join(str(v) for _,v in dataset['parameters'].items())))
            if len(legend_ax):
                print legend_ax
                print legend_txt
                leg = plt.legend(legend_ax, legend_txt, loc='upper left', 
                        prop={'size':10})
                leg.get_frame().set_alpha(0.5)
            plot.format_xaxis(axes[-1], primary)
            primary = False
        plt.title(self.title)
        canvas=FigureCanvas(plot.fig)
        response=HttpResponse(content_type='image/png')
        canvas.print_png(response)
        Chart.lock += 1
        return response



class Plot(object):

    def __init__(self, size=(1024, 768), secondary=False):
        '''
        Initialise plot
        '''
        width, height = size
        right_margin = 0.03 if secondary else 0.01
        self.margins = (0.04*768/height, 0.02*768/height, 0.05*1025/width, 
                right_margin, 0.02) # top, bottom, left, right, space
        dpi = 80
        plt.rc('axes', grid=True)
        plt.rc('grid', color='0.7', linestyle='-', linewidth=0.5)
        self.fig = plt.figure(facecolor='white', dpi=dpi, figsize=(width/dpi,
                height/dpi))


    def add_axis(self, heights, primary_axis, log=False):
        '''
        Add a new plot area to the plot. The x axis is always common.
        To plot 2 charts on top of each other, this method only needs to be
        called once, even if their y-axis scaling is different.
        This method returns an axis identifier that can be used for plotting:
        ax_id.plot(something)
        For stacked charts, call this method multiple times, the first one 
        will be at the bottom. 
        '''
        top, bottom, left, right, space = self.margins
        arguments = {'axisbg':'#fafafa'}
        if log: arguments['yscale'] = 'log'
        if not hasattr(self, 'i_axis'):
            self.i_axis = 0
        else:
            self.i_axis += 1
            arguments['sharex'] = primary_axis
        c = (1 - top - bottom - space * (len(heights) - 1)) / sum(
                                                            h for h in heights)
        height = c * heights[self.i_axis]
        bottom += sum(c * h for h in heights[:self.i_axis]
                                                        ) + self.i_axis * space
        width = 1 - left - right
        axis = self.fig.add_axes([left, bottom, width, height], **arguments)
        return axis


    def format_xaxis(self, axis, primary):
        '''
        Set the grid of the x axis with appropriate spacing for the date range
        '''
        steps = (1,2,3,4,6,12)
        step = steps[min(len(self.dates) // 265, 5)]
        print len(self.dates), step
        axis.set_axisbelow(True)
        axis.xaxis.grid(b=True, which='minor', color='0.90', linewidth=0.5)
        if len(self.dates) < 260:
            axis.xaxis.set_major_locator(MonthLocator(bymonth=range(1,13,step)))
            axis.xaxis.set_minor_locator(WeekdayLocator(byweekday=6))
            axis.xaxis.set_major_formatter(DateFormatter(fmt='%b %y'))
            if not primary: # this is not the primary axis
                plt.setp(axis.get_xticklabels(), visible=False)
        else:
            axis.xaxis.set_minor_locator(MonthLocator(bymonth=range(1,13,step)))
            axis.xaxis.set_major_locator(YearLocator())
            axis.xaxis.set_minor_formatter(DateFormatter(fmt='%b %y'))
            plt.setp(axis.get_xticklabels(minor=False), visible=False)
            if not primary: # this is not the primary axis
                plt.setp(axis.get_xticklabels(minor=False), visible=False)
                plt.setp(axis.get_xticklabels(minor=True), visible=False)


    def line(self, axis, data, colour=None):
        '''
        Plot a line
        '''
        if len(self.dates) == len(data):
            return axis.plot(self.dates, data, color=colour)
        else: # Assume the enddate is the same
            dates = self.dates[-len(data):]
            return axis.plot(dates, data, color=colour)


    def primary(self, style, axis, prices, dates, colour=None, **kwargs):
        '''
        Plot primary chart
        '''
        self.dates = dates
        if style == 'line':
            data = prices.close[dates[0]:dates[-1]]
            axis.plot(dates, data, color=colour)
            lo, hi = min(data), max(data)
        elif style == 'candle':
            lo, hi = self.candlestick(axis, prices)
        elif style == 'hilo':
            lo, hi = self.hilo(axis, prices, colour=colour)
        elif style == 'market_type':
            lo, hi = self.market_type(axis, prices, **kwargs)
#TODO: delete next 2 lines
        elif style == 'market_conditions_channel':
            lo, hi = self.market_conditions_channel(axis, prices)


        self.range = (prices.close[dates[0]], lo, hi) # for secondary plot
        self.format_yaxis(axis, hi, lo)


    def secondary(self, axis, prices, colour):
        '''
        Generates a secondary y axis that is linked to [axis] and scales with
        it.
        The origin of the two charts will the the same on the startdate.
        '''
        sec_axis = axis.twinx()
        sec_axis.set_yscale('log')
        data = [prices[d] for d in self.dates]
        pri_start, pri_lo, pri_hi = self.range # of primary plot
        sec_start, sec_lo, sec_hi = data[0], min(data), max(data)
        reset_primary = False
        if pri_lo/pri_start > sec_lo/sec_start:
            pri_lo = sec_lo * pri_start/sec_start
            reset_primary = True
        else:
            sec_lo = pri_lo * sec_start/pri_start

        if pri_hi/pri_start < sec_hi/sec_start:
            pri_hi = sec_hi * pri_start/sec_start
            reset_primary = True
        else:
            sec_hi = pri_hi * sec_start/pri_start
        if reset_primary:
            axis.set_ylim([pri_lo * 0.95, pri_hi * 1.05])
        sec_axis.plot(self.dates, data, color=colour)
        sec_axis.set_ylim([sec_lo * 0.95, sec_hi * 1.05])
        axis.yaxis.grid(b=False, which='minor')
        axis.yaxis.grid(b=False, which='major')
        self.format_yaxis(sec_axis, sec_hi, sec_lo)


    def yformat(self, x, pos=0):
        return '{:1.0f}'.format(x)


    def yformat_small(self, x, pos=0):
        return '{:2.1f}'.format(x)


    def format_yaxis(self, axis, hi, lo):
        steps = [0.1, 0.2, 0.5, 1, 2, 5, 10, 20, 50, 100, 200, 500, 1e3, 2e3,
                 5e3, 1e4, 2e4, 5e4, 1e5, 2e5, 5e5, 1e6, 2e6, 5e6, 1e7]
        y_steps = (hi - lo) / 4
        for i, step in enumerate(steps):
            if step > y_steps:
                break
        axis.yaxis.set_minor_locator(MultipleLocator(steps[i-2]))
        axis.yaxis.set_major_locator(MultipleLocator(steps[i]))
        if hi > 10:
            axis.yaxis.set_major_formatter(FuncFormatter(self.yformat))
        else:
            axis.yaxis.set_major_formatter(FuncFormatter(self.yformat_small))
        axis.yaxis.grid(which='minor', color='0.90', linewidth=0.5)
        axis.set_ylim([lo * 0.95, hi * 1.05])


    def hilo(self, axis, prices, width=0.5, colour=None):
        """
        Plot the time, open, close, high, low as a vertical line ranging
        from low to high. plot a line from every days close to the next open.
        """
        dates = []
        lines = []
        for date in self.dates:
            t = date2num(date)
            lines.extend([prices.open[date], None, prices.low[date], 
                    prices.high[date], None, prices.close[date]])
            dates.extend([t, None, t, t, None, t])
        axis.plot(dates, lines, linewidth=1, color=colour, antialiased=True)
        return min(y for y in lines if y is not None), max(lines)


    def candlestick(self, axis, prices, width=0.5, colorup='green', 
                colordown='red', alpha=1.0):
        """
        Plot the time, open, close, high, low as a vertical line ranging
        from low to high.  Use a rectangular bar to represent the
        open-close span.  If close >= open, use colorup to color the bar,
        otherwise use colordown
        ax          : an Axes instance to plot to
        width       : fraction of a day for the rectangle width
        colorup     : the color of the rectangle where close >= open
        colordown   : the color of the rectangle where close <  open
        alpha       : the rectangle alpha level
        """
        dates = []
        lines = []
        for date in self.dates:
            t = date2num(date)
            close = prices.close[date]
            open_ = prices.open[date]
            if close >= open_:
                color = colorup
                lower = open_
                height = close - open_
            else:
                color = colordown
                lower = close
                height = open_ - close
            lines.extend([prices.low[date], prices.high[date], None])
            dates.extend([t, t, None])
            rect = Rectangle(xy=(t - width/2, lower), width=width,
                    height=height, facecolor=color, edgecolor=color, zorder=2)
            rect.set_alpha(alpha)
            axis.add_patch(rect)
        axis.plot(dates, lines, linewidth=0.5, zorder=1, antialiased=True)
        return min(y for y in lines if y is not None), max(lines)


    def market_type(self, axis, prices, **kwargs):
        '''
        Plot the pool index chart using colour codes and thickness to indicate
        market conditions.
        '''
        mt = kwargs.get('markettype')
        trends = mt.get_trend()
        volatilities = mt.get_volatility()

#        trends = kwargs.get('trend')
#        volatilities = kwargs.get('volatility')

        linecolours = kwargs.get('linecolours', None)
        if not linecolours:
            linecolours = {mt.UP:'darkgreen', mt.FLAT:'orange', 
                    mt.DOWN:'darkred'}
        bgcolours = kwargs.get('bgcolours', None)
        if not bgcolours:
            bgcolours = {mt.VOLATILE: '#ffaaaa', mt.NORMAL: '#eecccc', 
                    mt.QUIET: '#eeeeee'}

        years = len(prices.close)/250
        if years > 10:
            linewidth = 0.5
        if years > 5:
            linewidth = 0.75
        else:
            linewidth = 1

        dates = []
        lines = []
        startdate = self.dates[0]
        if trends:
            linecolour = linecolours[trends[startdate]]
        else:
            linecolour = 'black'
        if volatilities:
            bgcolour = bgcolours[volatilities[startdate]]

        for today in self.dates:
            close = prices.close[today]
            dates.append(today)
            lines.append(close)

            if volatilities:
                volatility = volatilities[today]
                if bgcolour != bgcolours[volatility]:
                    # fill background colour if volatility has changed:
                    axis.axvspan(startdate, today, fc=bgcolour, lw=0, alpha=0.5)
                    startdate = today
                    bgcolour = bgcolours[volatility]

            if trends:
                trend = trends[today]
                if linecolour != linecolours[trend]:
                    # draw price lines if the trend has changed:
                    axis.plot(dates, lines, color=linecolour, 
                            linewidth=linewidth)
                    dates = [today]
                    lines = [close]
                    linecolour = linecolours[trend]

        # draw final lines and background colour:
        if volatilities:
            axis.axvspan(startdate, today, fc=bgcolour, lw=0, alpha=0.5)
        axis.plot(dates, lines, color=linecolour, linewidth=linewidth)
        return min(prices.close.as_list()), max(prices.close.as_list())



    def plot_trade(self, axis, dates, prices, colour):
        '''
        Plots a single trade on a price chart
        '''
        axis.plot(dates, prices, color=colour, linewidth=2)



#TODO: everything below this line can be deleted when market_type works

#    def market_conditions(self, axis, prices, settings=None, colours=None,
#                bgcolours=None):
#        '''
#        Plot the index chart using colour codes and thickness to indicate
#        market conditions.
#        '''
#        if not colours: 
#            linecolours = {'up':'darkgreen', 'flat':'orange', 'down':'darkred'}
#        if not bgcolours:
#            bgcolours = {'volatile': '#ffaaaa', 'normal': '#eecccc', 
#                         'quiet': '#eeeeee'}
#        if not settings:
#            rs = init_redis()
#            settings = str2dict(rs.get('market_conditions_settings'))
#        years = len(prices.close)/250
#        if years > 10:
#            linewidth = 0.5
#        if years > 5:
#            linewidth = 0.75
#        else:
#            linewidth = 1
#
#        linecolour = None
#        bgcolour = None
#        for today in self.dates:
#            close = prices.close[today]
#            trend, volatility = prices.mc(date_=today, **settings)
#            if linecolour is None:
#                # initialise first loop
#                dates = []
#                lines = []
#                linecolour = linecolours[trend]
#                startdate = today
#                bgcolour = bgcolours[volatility]
#            dates.append(today)
#            lines.append(close)
#            if linecolour != linecolours[trend]:
#                # draw price lines if the trend has changed:
#                axis.plot(dates, lines, color=linecolour, linewidth=linewidth)
#                dates = [today]
#                lines = [close]
#                linecolour = linecolours[trend]
#            if bgcolours[volatility] != bgcolour:
#                # fill background colour if volatility has changed:
#                axis.axvspan(startdate, today, fc=bgcolour, lw=0, alpha=0.5)
#                startdate = today
#                bgcolour = bgcolours[volatility]
#        # draw final lines and background colour:
#        axis.axvspan(startdate, today, fc=bgcolour, lw=0, alpha=0.5)
#        axis.plot(dates, lines, color=linecolour, linewidth=linewidth)
#        return min(prices.close.as_list()), max(prices.close.as_list())



#    def market_conditions_channel(self, axis, prices, settings=None, 
#                colours=None, bgcolours=None):
#        '''
#TMP - need permanent solution (mkt cond in params?)
#        '''
#        if not colours: 
#            linecolours = {'up':'darkgreen', 'flat':'orange', 'down':'darkred'}
#        if not bgcolours:
#            bgcolours = {'volatile': '#ffaaaa', 'normal': '#eecccc', 
#                         'quiet': '#eeeeee'}
#        if not settings:
#            rs = init_redis()
#            settings = str2dict(rs.get('market_conditions_settings'))
#        years = len(prices.close)/250
#        if years > 10:
#            linewidth = 0.5
#        if years > 5:
#            linewidth = 0.75
#        else:
#            linewidth = 1
#
#        from channel.models import Channel
#
#        linecolour = None
##        bgcolour = None
#        for today in self.dates:
#            close = prices.close[today]
#            aM = prices.channel.angle(Channel.MONTH)[today]
#            aSW = prices.channel.angle(Channel.SIXWEEKS)[today]
#            aTM = prices.channel.angle(Channel.TWOMONTHS)[today]
#            if aM > 0 and aSW > 0 and aTM > 0 :
#                trend = 'up'
#            elif aM < 0 and aSW < 0 and aTM < 0 :
#                trend = 'down'
#            else:
#                trend = 'flat'
#            if linecolour is None:
#                # initialise first loop
#                dates = []
#                lines = []
#                linecolour = linecolours[trend]
##                startdate = today
##                bgcolour = bgcolours[volatility]
#            dates.append(today)
#            lines.append(close)
#            if linecolour != linecolours[trend]:
#                # draw price lines if the trend has changed:
#                axis.plot(dates, lines, color=linecolour, linewidth=linewidth)
#                dates = [today]
#                lines = [close]
#                linecolour = linecolours[trend]
##            if bgcolours[volatility] != bgcolour:
##                # fill background colour if volatility has changed:
##                axis.axvspan(startdate, today, fc=bgcolour, lw=0, alpha=0.5)
##                startdate = today
##                bgcolour = bgcolours[volatility]
#        # draw final lines and background colour:
##        axis.axvspan(startdate, today, fc=bgcolour, lw=0, alpha=0.5)
#        axis.plot(dates, lines, color=linecolour, linewidth=linewidth)
#        return min(prices.close.as_list()), max(prices.close.as_list())



#def get_market_condition(prices, date, settings):
#    '''
#    Returns the market condition, which consists of 2 parameters:
#        trend: up, flat or down
#        volatility: volatile, normal or quiet
#    These parameters can have 2 or 3 values, in case of two, the middle one is
#    dropped.
#    If it is a 3x3, 2x3 or 3x2 matrix there are 2 thresholds for the 3 axis and
#        only one threshold for the 2 axis. In that case the second value is
#        ignored.
#    If it is a 2x2 matrix, the thresholds are used as follows:
#        * trend th1=th2 and volatility th1=th2: both are considered as a single
#            threshold.
#        * trend th1=th2 and volatility th1!=th2: v_th1 is used for the DOWN
#            trend and v_th2 is used for the UP trend.
#        * trend th1!=th2 and volatility th1=th2: t_th1 is used for the QUIET
#            volatility and t_th2 is used for the VOLATILE volatility.
#        * trend th1!=th2 and volatility th1!=th2: illegal
#    '''
#    ma = prices.close.sma(settings['n_ma'], date)
#    close = prices.close[date]
#    if close < ma * (1 + settings['trend_th'][0]):
#        trend = 'down'
#    elif settings['trend_zones'] == 3 and close < ma * (1 + 
#            settings['trend_th'][1]):
#        trend = 'flat'
#    else:
#        trend = 'up'
#    atr = prices.atr(settings['n_atr'], date, as_price=False)
#    if atr < settings['vol_th'][0]:
#        volatility = 'quiet'
#    elif settings['vol_zones'] == 3 and atr < settings['vol_th'][1]:
#        volatility = 'normal'
#    else:
#        volatility = 'volatile'
#    return trend, volatility
